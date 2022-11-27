import graphlib
import logging
import sys
import time
from collections import deque
from concurrent import futures
from contextvars import Context, ContextVar, copy_context
from datetime import timedelta
from subprocess import CalledProcessError
from typing import Dict, Generator, List, Optional, Tuple

from colorama import Fore, Style

from dwas._steps.handlers import BaseStepHandler, StepGroupHandler, StepHandler
from dwas._steps.parametrize import extract_parameters
from dwas._steps.steps import Step

from ._config import Config
from ._exceptions import (
    CyclicStepDependenciesException,
    DuplicateStepException,
    FailedPipelineException,
    UnavailableInterpreterException,
    UnknownStepsException,
)
from ._log_capture import PipePlexer
from ._logging import set_context_handler
from ._subproc import set_subprocess_default_pipes
from ._timing import get_timedelta_since

LOGGER = logging.getLogger(__name__)

_PIPELINE = ContextVar["Pipeline"]("pipeline")


def get_pipeline() -> "Pipeline":
    return _PIPELINE.get()


def set_pipeline(pipeline: "Pipeline") -> None:
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

        self._registered_steps: List[Tuple[str, Step]] = []
        self._registered_step_groups: List[
            Tuple[str, List[str], Optional[bool]]
        ] = []
        self._steps_cache: Optional[Dict[str, BaseStepHandler]] = None

    @property
    def _steps(self) -> Dict[str, BaseStepHandler]:
        if self._steps_cache is None:
            self._steps_cache = self._resolve_steps()
        return self._steps_cache

    def register_step(self, name: str, step: "Step") -> None:
        self._registered_steps.append((name, step))

    def register_step_group(
        self,
        name: str,
        requires: List[str],
        run_by_default: Optional[bool] = None,
    ) -> None:
        self._registered_step_groups.append((name, requires, run_by_default))

    def _resolve_steps(self) -> Dict[str, BaseStepHandler]:
        steps = {}

        for name, func in self._registered_steps:
            for step in self._resolve_parameters(name, func):
                if step.name in steps:
                    raise DuplicateStepException(step.name)

                steps[step.name] = step

        for name, requires, run_by_default in self._registered_step_groups:
            if name in steps:
                raise DuplicateStepException(name)

            steps[name] = StepGroupHandler(
                name, self, requires, run_by_default
            )

        return steps

    def _resolve_parameters(
        self, name: str, func: Step
    ) -> Generator[BaseStepHandler, None, None]:
        parameters = extract_parameters(func)
        all_run_by_default = True
        all_created = []

        for params_id, args in parameters:
            step_name = ""
            if len(parameters) > 1 and params_id != "":
                step_name = f"[{params_id}]"

            step_name = f"{name}{step_name}"
            current_run_by_default = args.pop("run_by_default", None)

            all_created.append(step_name)
            all_run_by_default = all_run_by_default and current_run_by_default

            yield StepHandler(
                name=step_name,
                func=func,
                pipeline=self,
                python=args.pop("python", None),
                requires=args.pop("requires", None),
                run_by_default=current_run_by_default,
                parameters=args,
                passenv=args.pop("passenv", None),
                setenv=args.pop("setenv", None),
            )

        if len(parameters) > 1:
            yield StepGroupHandler(name, self, all_created, all_run_by_default)

    def _resolve_execution_order(
        self,
        steps: Optional[List[str]] = None,
        only_steps: Optional[List[str]] = None,
        except_steps: Optional[List[str]] = None,
    ) -> List[str]:
        assert not (only_steps and except_steps)
        if only_steps:
            steps = only_steps
        if except_steps is None:
            except_steps = []

        if steps is None:
            steps = [
                name
                for name, step in self._steps.items()
                if step.run_by_default and name not in except_steps
            ]

        graph = {}
        steps_to_process = deque(steps)
        unknown_steps = []

        while steps_to_process:
            step = steps_to_process.pop()

            try:
                step_info = self._steps[step]
            except KeyError:
                unknown_steps.append(step)
                continue

            required_steps = step_info.requires
            if only_steps:
                required_steps = [r for r in required_steps if r in only_steps]
            elif except_steps:
                required_steps = [
                    r for r in required_steps if r not in except_steps
                ]

            graph[step] = required_steps

            for requirement in required_steps:
                if (
                    requirement not in graph
                    and requirement not in except_steps
                ):
                    steps_to_process.append(requirement)

        if unknown_steps:
            raise UnknownStepsException(unknown_steps)

        sorter = graphlib.TopologicalSorter(graph)
        try:
            return list(sorter.static_order())
        except graphlib.CycleError as exc:
            raise CyclicStepDependenciesException(exc.args[1]) from exc

    def execute(
        self,
        steps: Optional[List[str]],
        only_steps: Optional[List[str]],
        except_steps: Optional[List[str]],
        clean: bool,
    ) -> None:
        # we should refactor at some point
        # pylint: disable=too-many-branches,too-many-locals,too-many-statements
        start_time = time.monotonic()

        steps = self._resolve_execution_order(steps, only_steps, except_steps)
        if only_steps is None:
            only_steps = steps
        if except_steps is None:
            except_steps = []

        if clean:
            LOGGER.debug("Cleaning up workspace")
            for step in steps:
                self._steps[step].clean()

        LOGGER.info("Running steps: %s", ", ".join(steps))

        graph = {
            step: [
                r
                for r in self._steps[step].requires
                if r in only_steps and r not in except_steps
            ]
            for step in steps
        }

        sorter = graphlib.TopologicalSorter(graph)
        sorter.prepare()

        results: Dict[str, Tuple[Optional[Exception], timedelta]] = {}
        should_stop = False

        with futures.ThreadPoolExecutor(self.config.n_jobs) as executor:
            running_futures: Dict[
                futures.Future[timedelta], Tuple[str, Optional[PipePlexer]]
            ] = {}

            while sorter.is_active():
                ready = sorter.get_ready()
                if not ready:
                    if not running_futures:
                        # No more tasks ready to run, and all tasks has finished
                        # we can't move forward
                        break

                    next_finished = next(
                        futures.as_completed(running_futures.keys())
                    )
                    name, pipe_plexer = running_futures.pop(next_finished)

                    if pipe_plexer is not None:
                        pipe_plexer.dump(sys.stdout, sys.stderr)

                    try:
                        time_spent = next_finished.result()
                    except ExceptionWithTimeSpentException as exc:
                        results[name] = exc.original_exception, exc.time_spent

                        if (
                            isinstance(
                                exc.original_exception,
                                UnavailableInterpreterException,
                            )
                            and self.config.skip_missing_interpreters
                        ):
                            sorter.done(name)
                        else:
                            if self.config.fail_fast:
                                should_stop = True
                                for future in running_futures:
                                    future.cancel()

                            # We won't be able to enqueue new results after a failure
                            # anyways
                            continue
                    except futures.CancelledError as exc:
                        results[name] = exc, timedelta()
                        continue
                    else:
                        results[name] = None, time_spent
                        sorter.done(name)

                if should_stop:
                    continue

                for name in ready:
                    pipe_plexer = (
                        PipePlexer() if self.config.n_jobs != 1 else None
                    )

                    # XXX: Save the context to be able to rerun in it with each
                    # executor. This needs to be done every time as it's not
                    # possible to re-enter a context.
                    pipeline_context = copy_context()

                    future = executor.submit(
                        self._run_step_in_context,
                        pipeline_context,
                        name,
                        pipe_plexer,
                    )
                    running_futures[future] = name, pipe_plexer

            self._log_summary(graph, results, start_time)

    def get_step(self, step_name: str) -> BaseStepHandler:
        return self._steps[step_name]

    def list_all_steps(
        self,
        steps: Optional[List[str]] = None,
        only_steps: Optional[List[str]] = None,
        except_steps: Optional[List[str]] = None,
        show_dependencies: bool = False,
    ) -> None:
        all_steps = self._resolve_execution_order(list(self._steps.keys()))
        selected_steps = self._resolve_execution_order(
            steps, only_steps, except_steps
        )

        LOGGER.info("Available steps (* means selected, - means skipped):")
        for step in sorted(all_steps):
            dep_info = ""
            if show_dependencies and self._steps[step].requires:
                dep_info = " --> " + ", ".join(
                    reversed(
                        [
                            s
                            for s in all_steps
                            if s in self._steps[step].requires
                        ]
                    )
                )
            if step in selected_steps:
                LOGGER.info("\t* %s%s", step, dep_info)
            else:
                LOGGER.info("\t%s- %s%s", Fore.LIGHTBLACK_EX, step, dep_info)

    def _log_summary(
        self,
        graph: Dict[str, List[str]],
        results: Dict[str, Tuple[Optional[Exception], timedelta]],
        start_time: float,
    ) -> None:
        LOGGER.info("%s*** Steps summary ***", Style.BRIGHT)
        sorter = graphlib.TopologicalSorter(graph)

        failed_jobs = []
        blocked_jobs = []
        cancelled_jobs = []

        for name in sorter.static_order():
            if name in results:
                result, time_spent = results[name]
                if result is None:
                    LOGGER.info(
                        "\t%s[%s] %s: success", Fore.GREEN, time_spent, name
                    )
                elif (
                    isinstance(result, UnavailableInterpreterException)
                    and self.config.skip_missing_interpreters
                ):
                    LOGGER.info(
                        "\t%s%s: Skipped: %s",
                        Fore.YELLOW,
                        name,
                        result,
                    )
                elif isinstance(result, futures.CancelledError):
                    LOGGER.info(
                        "\t%s%s: Cancelled",
                        Fore.YELLOW,
                        name,
                    )
                    cancelled_jobs.append(name)
                else:
                    LOGGER.info(
                        "\t%s%s[%s] %s: error: %s",
                        Style.BRIGHT,
                        Fore.RED,
                        time_spent,
                        name,
                        self._format_exception(result),
                    )
                    failed_jobs.append(name)
            elif cancelled_jobs:
                LOGGER.info(
                    "\t%s%s: Cancelled",
                    Fore.YELLOW,
                    name,
                )
                cancelled_jobs.append(name)
            else:
                blocking_dependencies = [
                    dep
                    for dep in graph[name]
                    if dep in failed_jobs or dep in blocked_jobs
                ]
                assert blocking_dependencies is not None
                blocked_jobs.append(name)
                LOGGER.warning(
                    "\t%s%s: blocked by %s",
                    Fore.YELLOW,
                    name,
                    ", ".join(blocking_dependencies),
                )

        self._display_slowest_dependency_chain(graph, results)

        LOGGER.info("All steps ran in %s", get_timedelta_since(start_time))
        if failed_jobs:
            raise FailedPipelineException(
                len(failed_jobs), len(blocked_jobs), len(cancelled_jobs)
            )

    def _run_step_in_context(
        self,
        pipeline_context: Context,
        name: str,
        pipe_plexer: Optional[PipePlexer],
    ) -> timedelta:
        # We need to make sure that we run in a sub-context of the pipeline.
        # Running via `futures.ThreadPoolExecutor` however does not forward the
        # context. As such, we need first to re-enter the pipeline context,
        # copy it, to avoid modifications, and run inside this new context.
        def execute() -> timedelta:
            # Ensure we run in a clean sub-context
            context = copy_context()
            return context.run(self._run_step, name, pipe_plexer)

        # Forcefully run in the pipeline context
        return pipeline_context.run(execute)

    def _run_step(
        self,
        name: str,
        pipe_plexer: Optional[PipePlexer],
    ) -> timedelta:
        if pipe_plexer is not None:
            set_context_handler(pipe_plexer.stderr)
            set_subprocess_default_pipes(
                pipe_plexer.stdout, pipe_plexer.stderr
            )

        LOGGER.info(
            "%s--- Step: %s ---%s", Style.BRIGHT, name, Style.RESET_ALL
        )
        start_time = time.monotonic()

        try:
            self._steps[name].execute()
        except UnavailableInterpreterException as exc:
            LOGGER.warning("Step %s failed: %s", name, exc)
            raise ExceptionWithTimeSpentException(
                exc, get_timedelta_since(start_time)
            ) from exc
        except Exception as exc:
            # FIXME: allow another exception that can be thrown programatically
            exc_info = exc if not isinstance(exc, CalledProcessError) else None
            LOGGER.error(
                "Step %s failed: %s",
                name,
                self._format_exception(exc),
                exc_info=exc_info,
            )
            raise ExceptionWithTimeSpentException(
                exc, get_timedelta_since(start_time)
            ) from exc

        LOGGER.info("%sStep %s finished successfully", Fore.GREEN, name)
        return get_timedelta_since(start_time)

    def _format_exception(self, exc: Exception) -> str:
        if isinstance(exc, CalledProcessError):
            return f"Command '{' '.join(exc.cmd)}' returned exit status {exc.returncode}"
        return str(exc)

    def _display_slowest_dependency_chain(
        self,
        graph: Dict[str, List[str]],
        results: Dict[str, Tuple[Optional[Exception], timedelta]],
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
        for step in graph.keys():
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
        graph: Dict[str, List[str]],
        results: Dict[str, Tuple[Optional[Exception], timedelta]],
    ) -> Dict[str, Tuple[List[str], timedelta]]:
        total_time_per_step: Dict[str, Tuple[List[str], timedelta]] = {}

        def compute_chain(step: str) -> Tuple[List[str], timedelta]:
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

        for step in results.keys():
            compute_chain(step)

        return total_time_per_step
