from typing import Dict, List, Optional, Set
from unittest.mock import ANY

import pytest

from dwas._exceptions import CyclicStepDependenciesException
from dwas._scheduler import Resolver, Scheduler


def assert_scheduler_state(
    scheduler: Scheduler,
    waiting: Optional[Set[str]] = None,
    ready: Optional[List[str]] = None,
    running: Optional[Dict[str, float]] = None,
    done: Optional[Set[str]] = None,
    failed: Optional[Set[str]] = None,
    blocked: Optional[Set[str]] = None,
    cancelled: Optional[Set[str]] = None,
    skipped: Optional[Set[str]] = None,
) -> None:
    assert {
        "waiting": scheduler.waiting,
        "ready": scheduler.ready,
        "running": scheduler.running,
        "done": scheduler.done,
        "failed": scheduler.failed,
        "blocked": scheduler.blocked,
        "cancelled": scheduler.cancelled,
        "skipped": scheduler.skipped,
    } == {
        "waiting": waiting or set(),
        "ready": ready or [],
        "running": running or {},
        "done": done or set(),
        "failed": failed or set(),
        "blocked": blocked or set(),
        "cancelled": cancelled or set(),
        "skipped": skipped or set(),
    }


@pytest.mark.parametrize(
    ("graph", "expected_cycle"),
    (
        ({"a": ["b"], "b": ["a"]}, ["a", "b", "a"]),
        (
            {"a": ["b"], "b": ["c", "d"], "c": [], "d": ["e"], "e": ["a"]},
            ["a", "b", "d", "e", "a"],
        ),
    ),
)
def test_resolver_handles_cycles(graph, expected_cycle):
    with pytest.raises(CyclicStepDependenciesException) as exc_wrapper:
        Resolver(graph)

    assert exc_wrapper.value.cycle == expected_cycle


def test_simple_scenario():
    scheduler = Resolver(
        {"a": ["b", "c"], "b": ["d"], "c": ["d", "e"], "d": [], "e": []}
    ).get_scheduler()

    assert_scheduler_state(
        scheduler, ready=["d", "e"], waiting={"a", "b", "c"}
    )

    scheduler.mark_started("d")
    scheduler.mark_started("e")
    assert_scheduler_state(
        scheduler, running={"d": ANY, "e": ANY}, waiting={"a", "b", "c"}
    )

    scheduler.mark_done("d")
    assert_scheduler_state(
        scheduler,
        ready=["b"],
        running={"e": ANY},
        waiting={"a", "c"},
        done={"d"},
    )

    scheduler.mark_skipped("e")
    assert_scheduler_state(
        scheduler, ready=["b", "c"], waiting={"a"}, done={"d"}, skipped={"e"}
    )

    scheduler.mark_started("b")
    scheduler.mark_done("b")
    assert_scheduler_state(
        scheduler, ready=["c"], waiting={"a"}, done={"b", "d"}, skipped={"e"}
    )

    scheduler.mark_started("c")
    scheduler.mark_failed("c")
    assert_scheduler_state(
        scheduler, failed={"c"}, blocked={"a"}, done={"b", "d"}, skipped={"e"}
    )


def test_scheduler_cancelled_become_blocked():
    scheduler = Resolver({"a": ["b"], "b": []}).get_scheduler()

    scheduler.mark_started("b")
    scheduler.stop()

    assert_scheduler_state(scheduler, running={"b": ANY}, cancelled={"a"})

    scheduler.mark_failed("b")

    assert_scheduler_state(scheduler, failed={"b"}, blocked={"a"})


def test_scheduler_cancelled_does_not_become_ready():
    scheduler = Resolver({"a": ["b"], "b": [], "c": []}).get_scheduler()

    scheduler.mark_started("b")
    scheduler.stop()

    assert_scheduler_state(scheduler, running={"b": ANY}, cancelled={"a", "c"})

    scheduler.mark_done("b")

    assert_scheduler_state(scheduler, done={"b"}, cancelled={"a", "c"})


def test_scheduler_marks_as_blocked_recursively():
    scheduler = Resolver(
        {"a": ["b", "e"], "b": ["c", "d"], "c": [], "d": [], "e": []}
    ).get_scheduler()
    scheduler.mark_started("c")
    scheduler.mark_failed("c")

    assert_scheduler_state(
        scheduler, ready=["d", "e"], failed={"c"}, blocked={"a", "b"}
    )

    scheduler.mark_started("d")
    scheduler.mark_started("e")
    scheduler.mark_done("d")
    scheduler.mark_skipped("e")

    assert_scheduler_state(
        scheduler, failed={"c"}, blocked={"a", "b"}, done={"d"}, skipped={"e"}
    )
