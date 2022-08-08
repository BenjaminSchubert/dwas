import graphlib
import logging
import sys
from collections import deque
from concurrent import futures
from contextvars import ContextVar
from datetime import datetime, timedelta
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from colorama import Fore, Style

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

if TYPE_CHECKING:
    from ._steps.handlers import BaseStepHandler

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
        self._steps: Dict[str, "BaseStepHandler"] = {}

    def register_step(self, step: "BaseStepHandler") -> None:
        if step.name in self._steps:
            raise DuplicateStepException(step.name)

        self._steps[step.name] = step

    def _resolve_steps(
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
                # StepHandler is a public interface, we don't want users accessing
                # this method.
                # pylint: disable=protected-access
                if step._run_by_default and name not in except_steps
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
            # StepHandler is a public interface, we don't want users accessing
            # this method.
            # pylint: disable=protected-access
            required_steps = step_info._requires
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
    ) -> None:
        # we should refactor at some point
        # pylint: disable=too-many-branches,too-many-locals
        start_time = datetime.now()

        steps = self._resolve_steps(steps, only_steps, except_steps)
        if only_steps is None:
            only_steps = steps
        if except_steps is None:
            except_steps = []

        LOGGER.info("Running steps: %s", ", ".join(steps))

        graph = {
            step: [
                r
                # StepHandler is a public interface, we don't want users accessing
                # this method.
                # pylint: disable=protected-access
                for r in self._steps[step]._requires
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
                    future = executor.submit(self._run_step, name, pipe_plexer)
                    running_futures[future] = name, pipe_plexer

            self._log_summary(graph, results, start_time)

    def get_requirement(self, requirement: str) -> "BaseStepHandler":
        return self._steps[requirement]

    def list_all_steps(
        self,
        steps: Optional[List[str]] = None,
        only_steps: Optional[List[str]] = None,
        except_steps: Optional[List[str]] = None,
        show_dependencies: bool = False,
    ) -> None:
        all_steps = self._resolve_steps(list(self._steps.keys()))
        selected_steps = self._resolve_steps(steps, only_steps, except_steps)

        LOGGER.info("Available steps (* means selected, - means skipped):")
        for step in sorted(all_steps):
            dep_info = ""
            # StepHandler is a public interface, we don't want users accessing
            # this method.
            # pylint: disable=protected-access
            if show_dependencies and self._steps[step]._requires:
                dep_info = " --> " + ", ".join(
                    reversed(
                        [
                            s
                            for s in all_steps
                            # StepHandler is a public interface, we don't want users accessing
                            # this method.
                            # pylint: disable=protected-access
                            if s in self._steps[step]._requires
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
        start_time: datetime,
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
                        result,
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
                    dep for dep in graph[name] if dep in failed_jobs
                ]
                assert blocking_dependencies is not None
                blocked_jobs.append(name)
                LOGGER.warning(
                    "\t%s%s: blocked by %s",
                    Fore.YELLOW,
                    name,
                    ", ".join(blocking_dependencies),
                )

        LOGGER.info("All steps ran in %s", datetime.now() - start_time)
        if failed_jobs:
            raise FailedPipelineException(
                len(failed_jobs), len(blocked_jobs), len(cancelled_jobs)
            )

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
        start_time = datetime.now()

        def total_time() -> timedelta:
            return datetime.now() - start_time

        # StepHandler is a public interface, we don't want users accessing
        # this method.
        # pylint: disable=protected-access
        try:
            self._steps[name]._execute()
        except UnavailableInterpreterException as exc:
            LOGGER.warning("Step %s failed: %s", name, exc)
            raise ExceptionWithTimeSpentException(exc, total_time()) from exc
        except Exception as exc:
            # FIXME: allow another exception that can be thrown programatically
            exc_info = exc if not isinstance(exc, CalledProcessError) else None
            LOGGER.error("Step %s failed: %s", name, exc, exc_info=exc_info)
            raise ExceptionWithTimeSpentException(exc, total_time()) from exc

        LOGGER.info("%sStep %s finished successfully", Fore.GREEN, name)
        return total_time()
