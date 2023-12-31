from __future__ import annotations

import logging
import signal
import time
from collections import deque
from concurrent import futures
from contextlib import ExitStack
from contextvars import ContextVar, copy_context
from datetime import timedelta
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Callable, Generator, cast

from colorama import Fore, Style

from . import _io
from ._exceptions import (
    DuplicateStepException,
    FailedPipelineException,
    UnavailableInterpreterException,
    UnknownStepsException,
)
from ._frontend import Frontend, StepSummary
from ._scheduler import JobResult, Resolver, Scheduler
from ._steps.handlers import BaseStepHandler, StepGroupHandler, StepHandler
from ._steps.parametrize import extract_parameters
from ._subproc import ProcessManager
from ._timing import format_timedelta, get_timedelta_since

if TYPE_CHECKING:
    from types import FrameType

    from ._config import Config
    from ._steps.steps import Step


LOGGER = logging.getLogger(__name__)

_PIPELINE = ContextVar["Pipeline"]("pipeline")


def get_pipeline() -> Pipeline:
    return _PIPELINE.get()


def set_pipeline(pipeline: Pipeline) -> None:
    _PIPELINE.set(pipeline)


class ExceptionWithTimeSpentException(Exception):
    def __init__(
        self, original_exception: Exception, time_spent: timedelta
    ) -> None:
        super().__init__(original_exception, time_spent)
        self.original_exception = original_exception
        self.time_spent = time_spent


class Pipeline:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.proc_manager = ProcessManager()

        self._registered_steps: list[tuple[str, Step, str | None]] = []
        self._registered_step_groups: list[
            tuple[str, list[str], str | None, bool | None]
        ] = []
        self._steps_cache: dict[str, BaseStepHandler] | None = None

    @property
    def steps(self) -> dict[str, BaseStepHandler]:
        if self._steps_cache is None:
            self._steps_cache = self._resolve_steps()
        return self._steps_cache

    def register_step(
        self, name: str, description: str | None, step: Step
    ) -> None:
        self._registered_steps.append((name, step, description))

    def register_step_group(
        self,
        name: str,
        requires: list[str],
        description: str | None = None,
        run_by_default: bool | None = None,
    ) -> None:
        self._registered_step_groups.append(
            (name, requires, description, run_by_default)
        )

    def _resolve_steps(self) -> dict[str, BaseStepHandler]:
        steps = {}

        for name, func, description in self._registered_steps:
            for step in self._resolve_parameters(name, func, description):
                if step.name in steps:
                    raise DuplicateStepException(step.name)

                steps[step.name] = step

        for (
            name,
            requires,
            description,
            run_by_default,
        ) in self._registered_step_groups:
            if name in steps:
                raise DuplicateStepException(name)

            steps[name] = StepGroupHandler(
                name, self, requires, run_by_default, description
            )

        return steps

    def _resolve_parameters(
        self, name: str, func: Step, description: str | None
    ) -> Generator[BaseStepHandler, None, None]:
        parameters = extract_parameters(func)
        all_run_by_default = True
        all_created = []

        for params_id, args in parameters:
            step_name = ""
            current_description = description
            if len(parameters) > 1 and params_id != "":
                step_name = f"[{params_id}]"

            step_name = f"{name}{step_name}"
            current_run_by_default = args.pop("run_by_default", None)

            if "description" in args:
                current_description = args.pop("description").format(**args)
            elif description is not None:
                current_description = description.format(**args)
            else:
                current_description = None

            all_created.append(step_name)
            all_run_by_default = all_run_by_default and current_run_by_default

            yield StepHandler(
                name=step_name,
                description=current_description,
                func=func,
                pipeline=self,
                python_spec=args.pop("python", None),
                requires=args.pop("requires", None),
                run_by_default=current_run_by_default,
                parameters=args,
                passenv=args.pop("passenv", None),
                setenv=args.pop("setenv", None),
            )

        if len(parameters) > 1:
            yield StepGroupHandler(
                name, self, all_created, all_run_by_default, description
            )

    def _build_graph(  # noqa: C901
        self,
        steps: list[str] | None = None,
        except_steps: list[str] | None = None,
        *,
        only_selected_steps: bool = False,
    ) -> dict[str, list[str]]:
        # we should refactor at some point
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements

        # First build the whole graph, without ignoring edges. This is necessary
        # to ensure we keep all dependency relations
        def expand(steps: list[str]) -> set[str]:
            expanded = set()
            to_process = deque(steps)
            while to_process:
                step = to_process.pop()
                expanded.add(step)
                step_info = self.steps[step]
                if isinstance(step_info, StepGroupHandler):
                    for req in step_info.requires:
                        if req not in expanded:
                            to_process.append(req)

            return expanded

        except_steps_set = (
            set() if except_steps is None else expand(except_steps)
        )

        if steps is None:
            steps = [
                name
                for name, step in self.steps.items()
                if step.run_by_default and name not in except_steps_set
            ]

        graph = {}
        steps_to_process = deque(steps)
        unknown_steps = []

        while steps_to_process:
            step = steps_to_process.pop()

            try:
                step_info = self.steps[step]
            except KeyError:
                unknown_steps.append(step)
                continue

            graph[step] = step_info.requires

            for requirement in step_info.requires:
                if requirement not in graph:
                    steps_to_process.append(requirement)

        if unknown_steps:
            raise UnknownStepsException(unknown_steps)

        if except_steps_set:
            except_replacements: dict[str, list[str]] = {}

            # FIXME: ensure we handle cycles
            def compute_replacement(requirements: list[str]) -> list[str]:
                replacements = []
                for requirement in requirements:
                    if requirement in steps:
                        replacements.append(requirement)
                    else:
                        if requirement not in except_replacements:
                            except_replacements[
                                requirement
                            ] = compute_replacement(graph[requirement])
                        replacements.extend(except_replacements[requirement])

                return replacements

            for step in except_steps_set:
                # The step might not be in the graph, if it is not depended
                # upon by anything else
                if step not in except_replacements and (
                    deps := graph.get(step)
                ):
                    except_replacements[step] = compute_replacement(deps)

            graph = {
                key: [
                    x for v in value for x in except_replacements.get(v, [v])
                ]
                for key, value in graph.items()
                if key not in except_steps_set
            }

        if only_selected_steps:
            only = expand(steps)
            only_replacements = {}

            def compute_only_replacement(
                step: str, requirements: list[str]
            ) -> list[str]:
                if step in only:
                    return [step]

                replacements = []
                for requirement in requirements:
                    if requirement not in only_replacements:
                        only_replacements[
                            requirement
                        ] = compute_only_replacement(
                            requirement, graph[requirement]
                        )
                    replacements.extend(only_replacements[requirement])

                return replacements

            for step in graph:
                if step not in only_replacements:
                    only_replacements[step] = compute_only_replacement(
                        step, graph[step]
                    )

            graph = {
                key: [x for v in value for x in only_replacements.get(v, [v])]
                for key, value in graph.items()
                if key in only
            }

        return graph

    def execute(
        self,
        steps: list[str] | None,
        except_steps: list[str] | None,
        *,
        only_selected_steps: bool,
        clean: bool,
    ) -> None:
        # pylint: disable=too-many-locals
        start_time = time.monotonic()

        graph = self._build_graph(
            steps, except_steps, only_selected_steps=only_selected_steps
        )
        resolver = Resolver(graph)
        scheduler = resolver.get_scheduler()
        steps_in_order = resolver.order()

        if clean:
            LOGGER.debug("Cleaning up workspace")
            for step in steps_in_order:
                self.steps[step].clean()

        LOGGER.info("Running steps: %s", ", ".join(steps_in_order))

        should_stop = False

        def request_stop(_signum: int, _frame: FrameType | None) -> None:
            nonlocal should_stop

            if not should_stop:
                LOGGER.warning(
                    "%sStopping requested. This will finish current jobs."
                    " To abort, hit ^C a second time.",
                    Style.BRIGHT,
                )
                should_stop = True
            else:
                LOGGER.critical("Aborting")
                self.proc_manager.kill()

        previous_signal = signal.signal(signal.SIGINT, request_stop)

        try:
            with ExitStack() as stack:
                if self.config.is_interactive:
                    stack.enter_context(
                        Frontend(StepSummary(scheduler, start_time)).activate()
                    )

                self._execute(scheduler, lambda: should_stop)
        finally:
            signal.signal(signal.SIGINT, previous_signal)

        self._log_summary(scheduler, steps_in_order, graph, start_time)

    def get_step(self, step_name: str) -> BaseStepHandler:
        return self.steps[step_name]

    def list_all_steps(
        self,
        steps: list[str] | None = None,
        except_steps: list[str] | None = None,
        *,
        only_selected_steps: bool = False,
        show_dependencies: bool = False,
    ) -> None:
        # pylint: disable=too-many-locals
        all_steps = Resolver(
            self._build_graph(list(self.steps.keys()))
        ).order()
        selected_steps = Resolver(
            self._build_graph(
                steps, except_steps, only_selected_steps=only_selected_steps
            )
        ).order()

        step_infos = []
        for step in sorted(all_steps):
            step_info = self.steps[step]

            dep_info = ""
            if show_dependencies and step_info.requires:
                dep_info = " --> " + ", ".join(
                    reversed([s for s in all_steps if s in step_info.requires])
                )

            description = ""
            if self.config.verbosity > 0 and step_info.description:
                description = step_info.description

            step_infos.append((step, dep_info, description))

        LOGGER.info("Available steps (* means selected, - means skipped):")
        if not step_infos:
            return

        max_step_length = max(len(s[0]) for s in step_infos)
        max_dependencies_length = max(len(s[1]) for s in step_infos)

        for step, dependencies, description in step_infos:
            indicator = "*"
            style = Style.BRIGHT
            if step not in selected_steps:
                style = ""
                indicator = "-"

            if self.config.verbosity > 0 and description:
                desc = f"\t[{Fore.BLUE}{Style.NORMAL}{description}{Style.RESET_ALL}{style}]"
            else:
                desc = ""

            LOGGER.info(
                "\t%s%s %-*s%-*s%s",
                style,
                indicator,
                max_step_length,
                step,
                max_dependencies_length,
                dependencies,
                desc,
            )

    def _execute(
        self,
        scheduler: Scheduler,
        should_stop: Callable[[], bool],
    ) -> None:
        running_futures: dict[
            futures.Future[None], tuple[str, _io.PipePlexer | None]
        ] = {}

        with futures.ThreadPoolExecutor(self.config.n_jobs) as executor:
            while scheduler:
                # Check if we should stop, and cancel new jobs
                if should_stop():
                    scheduler.stop()

                # Enqueue new jobs if possible
                while (
                    len(running_futures) < self.config.n_jobs
                    and scheduler.ready
                ):
                    step = scheduler.ready[0]
                    scheduler.mark_started(step)

                    pipe_plexer = (
                        _io.PipePlexer() if self.config.n_jobs != 1 else None
                    )

                    future = cast(
                        "futures.Future[None]",
                        executor.submit(
                            copy_context().run,
                            self._run_step,
                            step,
                            pipe_plexer,
                        ),
                    )
                    running_futures[future] = step, pipe_plexer

                # Wait for previous jobs to finish
                if not running_futures:
                    continue

                next_finished = next(
                    futures.as_completed(running_futures.keys())
                )
                name, pipe_plexer = running_futures.pop(next_finished)

                if pipe_plexer is not None:
                    with _io.log_file(None):
                        pipe_plexer.flush()

                self._handle_step_result(name, next_finished, scheduler)

    def _handle_step_result(
        self,
        name: str,
        result: futures.Future[None],
        scheduler: Scheduler,
    ) -> None:
        try:
            result.result()
        except Exception as exc:  # noqa:BLE001
            if (
                isinstance(exc, UnavailableInterpreterException)
                and self.config.skip_missing_interpreters
            ):
                scheduler.mark_skipped(name, exc)
                LOGGER.warning(
                    "Step %s%s%s failed: %s",
                    Style.BRIGHT,
                    name,
                    Style.NORMAL,
                    exc,
                )
            else:
                scheduler.mark_failed(name, exc)
                # FIXME: allow another exception that can be thrown programatically
                exc_info = (
                    exc
                    if not isinstance(
                        exc,
                        (CalledProcessError, UnavailableInterpreterException),
                    )
                    else None
                )
                LOGGER.error(  # noqa: TRY400, we want more control than .exception
                    "Step %s failed: %s",
                    name,
                    self._format_exception(exc),
                    exc_info=exc_info,
                )

                if self.config.fail_fast:
                    scheduler.stop()
        else:
            scheduler.mark_success(name)
            LOGGER.info(
                "%sStep %s%s%s finished successfully",
                Fore.GREEN,
                Style.BRIGHT,
                name,
                Style.NORMAL,
            )

    def _log_summary(
        self,
        scheduler: Scheduler,
        steps_order: list[str],
        graph: dict[str, list[str]],
        start_time: float,
    ) -> None:
        LOGGER.info("%s*** Steps summary ***", Style.BRIGHT)

        for name in steps_order:
            result, time_spent, exc = scheduler.results[name]

            if result == JobResult.SUCCESS:
                assert time_spent is not None

                LOGGER.info(
                    "\t%s[%s] %s%s%s: success",
                    Fore.GREEN,
                    format_timedelta(time_spent),
                    Style.BRIGHT,
                    name,
                    Style.NORMAL,
                )
            elif result == JobResult.SKIPPED:
                LOGGER.info(
                    "\t%s[-:--:--] %s%s%s: Skipped: %s",
                    Fore.YELLOW,
                    Style.BRIGHT,
                    name,
                    Style.NORMAL,
                    exc,
                )
            elif result == JobResult.CANCELLED:
                LOGGER.info(
                    "\t%s[-:--:--] %s%s%s: Cancelled",
                    Fore.YELLOW,
                    Style.BRIGHT,
                    name,
                    Style.NORMAL,
                )
            elif result == JobResult.FAILED:
                assert time_spent is not None
                assert exc is not None

                LOGGER.info(
                    "\t%s%s[%s] %s: error: %s",
                    Style.BRIGHT,
                    Fore.RED,
                    format_timedelta(time_spent),
                    name,
                    self._format_exception(exc),
                )
            elif result == JobResult.BLOCKED:
                blocking_dependencies = [
                    dep
                    for dep in graph[name]
                    if dep in scheduler.failed or dep in scheduler.blocked
                ]
                LOGGER.warning(
                    "\t%s[-:--:--] %s%s%s: blocked by %s",
                    Fore.YELLOW,
                    Style.BRIGHT,
                    name,
                    Style.NORMAL,
                    ", ".join(blocking_dependencies),
                )

        self._display_slowest_dependency_chain(graph, scheduler.results)

        LOGGER.info(
            "All steps ran in %s",
            format_timedelta(get_timedelta_since(start_time)),
        )
        if scheduler.failed or scheduler.blocked or scheduler.cancelled:
            raise FailedPipelineException(
                len(scheduler.failed),
                len(scheduler.blocked),
                len(scheduler.cancelled),
            )

    def _run_step(
        self,
        name: str,
        pipe_plexer: _io.PipePlexer | None,
    ) -> None:
        with ExitStack() as stack:
            if pipe_plexer is not None:
                stack.enter_context(
                    _io.redirect_streams(
                        pipe_plexer.stdout, pipe_plexer.stderr
                    )
                )

            LOGGER.info(
                "%s--- Step: %s ---%s", Style.BRIGHT, name, Style.RESET_ALL
            )
            log_file = self.config.log_path / f"{name}.log"

            LOGGER.debug("Log file can be found at %s", log_file)
            stack.enter_context(_io.log_file(log_file))

            self.steps[name].execute()

    def _format_exception(self, exc: Exception) -> str:
        if isinstance(exc, CalledProcessError):
            return f"Command '{' '.join(exc.cmd)}' returned exit status {exc.returncode}"
        return str(exc)

    def _display_slowest_dependency_chain(
        self,
        graph: dict[str, list[str]],
        results: dict[str, tuple[JobResult, timedelta, Exception | None]],
    ) -> None:
        if len(graph) <= 1:
            # If there's a single entry in the whole graph, no need to show
            return

        total_time_per_step = self._compute_slowest_chains(graph, results)

        LOGGER.debug("Dependency chains summaries:")
        LOGGER.debug("\ttime taken\tslowest dependency chain")

        total_slowest_step = ""
        total_slowest_time = timedelta()

        # Use the graph here, to display them in topological order
        for step in graph:
            if step not in total_time_per_step:
                continue

            slowest_chain, time_taken = total_time_per_step[step]
            if time_taken > total_slowest_time:
                total_slowest_step = step
                total_slowest_time = time_taken

            LOGGER.debug("\t%s\t%s", time_taken, " -> ".join(slowest_chain))

        LOGGER.info(
            "\tSlowest dependency chain takes %s: %s",
            total_slowest_time,
            " -> ".join(total_time_per_step[total_slowest_step][0]),
        )

    def _compute_slowest_chains(
        self,
        graph: dict[str, list[str]],
        results: dict[str, tuple[JobResult, timedelta, Exception | None]],
    ) -> dict[str, tuple[list[str], timedelta]]:
        total_time_per_step: dict[str, tuple[list[str], timedelta]] = {}

        def compute_chain(step: str) -> tuple[list[str], timedelta]:
            precomputed_result = total_time_per_step.get(step, None)
            if precomputed_result is not None:
                return precomputed_result

            time_for_current_step = results[step][1]

            if not graph[step]:
                # No dependenices, we are a root (or leaf)
                total_time_per_step[step] = [step], time_for_current_step
            else:
                slowest_dependency_chain, slowest_dependency_time = max(
                    (compute_chain(dependency) for dependency in graph[step]),
                    key=lambda dep: dep[1],
                )

                time_for_current_step += slowest_dependency_time
                total_time_per_step[step] = (
                    [step, *slowest_dependency_chain],
                    time_for_current_step,
                )

            return total_time_per_step[step]

        for step in results:
            compute_chain(step)

        return total_time_per_step
