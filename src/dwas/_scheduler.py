from __future__ import annotations

import copy
import enum
import logging
import time
from collections import deque
from datetime import timedelta
from typing import Any, Iterable, Mapping

from ._exceptions import CyclicStepDependenciesException

LOGGER = logging.getLogger(__name__)


@enum.unique
class JobResult(enum.Enum):
    SUCCESS = "DONE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class Scheduler:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        dependencies_graph: dict[str, set[str]],
        dependents_graph: dict[str, set[str]],
        weights: dict[str, Any],
    ) -> None:
        self._dependencies_graph = copy.deepcopy(dependencies_graph)
        self._dependents_graph = copy.deepcopy(dependents_graph)
        self._weights = weights
        self._stopped = False

        self.waiting: set[str] = set()
        self.ready: list[str] = []
        self.running: dict[str, float] = {}
        self.success: set[str] = set()
        self.failed: set[str] = set()
        self.blocked: set[str] = set()
        self.cancelled: set[str] = set()
        self.skipped: set[str] = set()

        self.results: dict[
            str, tuple[JobResult, timedelta, Exception | None]
        ] = {}

        # Enqueue all steps that are ready
        for step, dependencies in self._dependencies_graph.items():
            if not dependencies:
                self.ready.append(step)
            else:
                self.waiting.add(step)

    def mark_started(self, step: str) -> None:
        assert not self._stopped

        self.ready.remove(step)
        self.running[step] = time.monotonic()

    def mark_failed(self, step: str, exc: Exception) -> None:
        time_taken = self.running.pop(step)
        self.failed.add(step)
        self.results[step] = (
            JobResult.FAILED,
            timedelta(seconds=time.monotonic() - time_taken),
            exc,
        )
        self._mark_dependents_blocked(step)

    def mark_success(self, step: str) -> None:
        time_taken = self.running.pop(step)
        self.success.add(step)
        self.results[step] = (
            JobResult.SUCCESS,
            timedelta(seconds=time.monotonic() - time_taken),
            None,
        )
        self._mark_dependents_ready(step)

    def mark_skipped(self, step: str, exc: Exception) -> None:
        time_taken = self.running.pop(step)
        self.skipped.add(step)
        self.results[step] = (
            JobResult.FAILED,
            timedelta(time.monotonic() - time_taken),
            exc,
        )
        self._mark_dependents_ready(step)

    def _mark_dependents_ready(self, step: str) -> None:
        for dependent in self._dependents_graph[step]:
            dependencies = self._dependencies_graph[dependent]
            dependencies.remove(step)

            if not dependencies:
                try:
                    self.waiting.remove(dependent)
                except KeyError:
                    assert dependent in self.cancelled
                else:
                    # FIXME: ensure this is ordered
                    self.ready.append(dependent)

    def _mark_dependents_blocked(self, step: str) -> None:
        for dependent in self._dependents_graph[step]:
            try:
                self.waiting.remove(dependent)
            except KeyError:
                self.cancelled.remove(dependent)

            self.blocked.add(dependent)
            self.results[dependent] = JobResult.BLOCKED, timedelta(), None

            dependencies = self._dependencies_graph[dependent]
            dependencies.remove(step)

            # Remove this dependent from all it's dependencies, we will never
            # be able to start it anyways
            for dependency in dependencies:
                self._dependents_graph[dependency].remove(dependent)

            # And finally recurse
            self._mark_dependents_blocked(dependent)

    def stop(self) -> None:
        self._stopped = True
        while self.ready:
            step = self.ready.pop()
            self.cancelled.add(step)
            self.results[step] = JobResult.CANCELLED, timedelta(), None

        while self.waiting:
            step = self.waiting.pop()
            self.cancelled.add(step)
            self.results[step] = JobResult.CANCELLED, timedelta(), None

    def __bool__(self) -> bool:
        return bool(self.ready or self.running)


class Resolver:
    def __init__(self, graph: Mapping[str, Iterable[str]]) -> None:
        # step -> dependencies
        self._dependencies_graph = {
            step: set(dependencies) for step, dependencies in graph.items()
        }
        # step -> dependents
        self._dependents_graph = self._make_dependent_graph()

        # The relative weight of each node in the graph
        # This is to ensure a stable ordering when returning new nodes
        # This uses len(transitive_dependents), len(direct_dependents), name
        # as a way to sort.
        self._weights = self._build_weights()

    def _make_dependent_graph(self) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = {
            key: set() for key in self._dependencies_graph
        }

        for step, dependencies in self._dependencies_graph.items():
            for dependency in dependencies:
                graph[dependency].add(step)

        return graph

    def _build_weights(self) -> dict[str, tuple[int, int, str]]:
        weights: dict[str, tuple[int, int, str]] = {}

        path: deque[str] = deque()
        path_set = set()

        def _compute_weight(step: str) -> tuple[int, int, str]:
            if step in weights:
                return weights[step]

            path.appendleft(step)
            if step in path_set:
                raise CyclicStepDependenciesException(list(path))
            path_set.add(step)

            direct_dependents = self._dependents_graph[step]

            weight = (
                sum(_compute_weight(dep)[0] for dep in direct_dependents),
                len(direct_dependents),
                step,
            )
            weights[step] = weight

            path.popleft()
            path_set.remove(step)
            return weight

        for step in self._dependents_graph:
            _compute_weight(step)

        return weights

    def get_scheduler(self) -> Scheduler:
        return Scheduler(
            self._dependencies_graph, self._dependents_graph, self._weights
        )

    def order(self) -> list[str]:
        entries = []

        scheduler = self.get_scheduler()

        while scheduler:
            next_step = next(iter(scheduler.ready))
            entries.append(next_step)
            scheduler.mark_started(next_step)
            scheduler.mark_success(next_step)

        return entries
