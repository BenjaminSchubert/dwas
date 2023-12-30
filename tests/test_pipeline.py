# This tests some internals
# ruff: noqa:SLF001
from datetime import timedelta

import pytest

from dwas._exceptions import (
    CyclicStepDependenciesException,
    DuplicateStepException,
    UnknownStepsException,
)
from dwas._steps.parametrize import build_parameters

from ._utils import ANSI_COLOR_CODES_RE


def func():
    return lambda: None  # pragma: nocover


def step_with_requirements(requires):
    return build_parameters(requires=requires)(func())


def test_compute_slowest_chain_no_dependencies(pipeline):
    time_taken = timedelta(days=1)
    # pylint: disable=protected-access
    result = pipeline._compute_slowest_chains(
        {"step1": []}, {"step1": (None, time_taken)}
    )

    assert result == {"step1": (["step1"], time_taken)}


def test_compute_slowest_chain_dependencies(pipeline):
    time_taken_step1 = timedelta(days=1)
    time_taken_step2 = timedelta(hours=1)
    # pylint: disable=protected-access
    result = pipeline._compute_slowest_chains(
        {"step1": ["step2"], "step2": []},
        {
            "step1": (None, time_taken_step1),
            "step2": (None, time_taken_step2),
        },
    )

    assert result == {
        "step1": (["step1", "step2"], time_taken_step1 + time_taken_step2),
        "step2": (["step2"], time_taken_step2),
    }


@pytest.mark.parametrize(
    ("steps", "except_steps", "only_selected", "result"),
    (
        pytest.param(
            None,
            None,
            False,
            {
                "step-1": ["step-1-1", "step-1-2", "step-1-3"],
                "step-1-1": ["step-1-1-1"],
                "step-1-1-1": [],
                "step-1-2": ["step-1-2-1"],
                "step-1-2-1": [],
                "step-1-3": ["step-1-3-1"],
                "step-1-3-1": [],
            },
            id="default",
        ),
        pytest.param(
            ["step-nondefault"],
            None,
            False,
            {
                "step-nondefault": ["step-1-1", "step-1-2"],
                "step-1-1": ["step-1-1-1"],
                "step-1-1-1": [],
                "step-1-2": ["step-1-2-1"],
                "step-1-2-1": [],
            },
            id="nondefault",
        ),
        pytest.param(
            None,
            ["step-1-2"],
            False,
            {
                "step-1": ["step-1-1", "step-1-2-1", "step-1-3"],
                "step-1-1": ["step-1-1-1"],
                "step-1-1-1": [],
                "step-1-2-1": [],
                "step-1-3": ["step-1-3-1"],
                "step-1-3-1": [],
            },
            id="exclude-substep",
        ),
        pytest.param(
            None,
            ["step-1-3"],
            False,
            {
                "step-1": ["step-1-1", "step-1-2"],
                "step-1-1": ["step-1-1-1"],
                "step-1-1-1": [],
                "step-1-2": ["step-1-2-1"],
                "step-1-2-1": [],
            },
            id="exclude-group",
        ),
        pytest.param(
            ["step-1", "step-1-3-1"],
            ["step-1-3"],
            False,
            {
                "step-1": ["step-1-1", "step-1-2", "step-1-3-1"],
                "step-1-1": ["step-1-1-1"],
                "step-1-1-1": [],
                "step-1-2": ["step-1-2-1"],
                "step-1-2-1": [],
            },
            id="exclude-group-include-subgroup",
        ),
        pytest.param(
            ["step-1-1"],
            None,
            True,
            {"step-1-1": []},
            id="only-selected-step",
        ),
        pytest.param(
            ["step-1-3"],
            None,
            True,
            {
                "step-1-3": ["step-1-3-1"],
                "step-1-3-1": [],
            },
            id="only-group-selects-sub-steps",
        ),
        pytest.param(
            ["step-1"],
            ["step-1-2"],
            True,
            {
                "step-1": ["step-1-1", "step-1-3"],
                "step-1-1": [],
                # This is a group, and thus will include substeps recursively
                "step-1-3": ["step-1-3-1"],
                "step-1-3-1": [],
            },
            id="only-step-exclude-substep",
        ),
        pytest.param(
            None,
            ["step-1"],
            False,
            {"step-1-1-1": [], "step-1-2-1": []},
            id="exclude-top-level",
        ),
        pytest.param(
            ["step-1"],
            None,
            True,
            {
                "step-1": ["step-1-1", "step-1-2", "step-1-3"],
                "step-1-1": [],
                "step-1-2": [],
                "step-1-3": ["step-1-3-1"],
                "step-1-3-1": [],
            },
            id="only-top-level",
        ),
    ),
)
def test_graph_computation_is_correct(
    pipeline, steps, except_steps, only_selected, result
):
    # Top level steps
    pipeline.register_step_group(
        "step-1", ["step-1-1", "step-1-2", "step-1-3"]
    )
    pipeline.register_step_group(
        "step-nondefault",
        ["step-1-1", "step-1-2"],
        run_by_default=False,
    )

    # Sub steps
    pipeline.register_step(
        "step-1-1", None, step_with_requirements(["step-1-1-1"])
    )
    pipeline.register_step(
        "step-1-2", None, step_with_requirements(["step-1-2-1"])
    )
    pipeline.register_step_group("step-1-3", ["step-1-3-1"])

    # Sub sub steps
    pipeline.register_step("step-1-1-1", None, func())
    pipeline.register_step("step-1-2-1", None, func())
    pipeline.register_step("step-1-3-1", None, func())

    # pylint: disable=protected-access
    assert (
        pipeline._build_graph(
            steps, except_steps, only_selected_steps=only_selected
        )
        == result
    )


def test_only_keeps_dependency_information(pipeline):
    pipeline.register_step("1", None, step_with_requirements(["2"]))
    pipeline.register_step("2", None, step_with_requirements(["3"]))
    pipeline.register_step("3", None, step_with_requirements(["4"]))
    pipeline.register_step("4", None, func())

    # pylint: disable=protected-access
    assert pipeline._build_graph(
        ["1", "4"], None, only_selected_steps=True
    ) == {"1": ["4"], "4": []}


def test_exclude_keeps_dependency_information(pipeline):
    pipeline.register_step("1", None, step_with_requirements(["2"]))
    pipeline.register_step("2", None, step_with_requirements(["3"]))
    pipeline.register_step("3", None, step_with_requirements(["4"]))
    pipeline.register_step("4", None, func())

    # pylint: disable=protected-access
    assert pipeline._build_graph(
        None, ["2", "3"], only_selected_steps=False
    ) == {"1": ["4"], "4": []}


@pytest.mark.parametrize("step_type", ("normal", "group"))
def test_cannot_register_two_step_with_same_name(pipeline, step_type):
    pipeline.register_step("step", None, func())
    if step_type == "group":
        pipeline.register_step_group("step", [])
    else:
        pipeline.register_step("step", None, func())

    with pytest.raises(DuplicateStepException):
        pipeline.list_all_steps()


def test_handles_cyclic_dependencies(pipeline):
    pipeline.register_step("step-1", None, step_with_requirements(["step-2"]))
    pipeline.register_step("step-2", None, step_with_requirements(["step-1"]))

    with pytest.raises(CyclicStepDependenciesException):
        pipeline.list_all_steps()


def test_handles_unexpected_steps(pipeline):
    pipeline.register_step("step-1", None, step_with_requirements(["step-2"]))

    with pytest.raises(UnknownStepsException):
        pipeline.list_all_steps()


def test_ensure_steps_can_be_listed(pipeline, caplog):
    pipeline.register_step("bydefault", None, func())
    pipeline.register_step(
        "notbydefault", None, build_parameters(run_by_default=False)(func())
    )

    pipeline.list_all_steps()

    messages = [
        ANSI_COLOR_CODES_RE.sub("", m).strip() for m in caplog.messages
    ]
    assert "* bydefault" in messages
    assert "- notbydefault" in messages


def test_ensure_listing_shows_selected_steps(pipeline, caplog):
    pipeline.register_step("bydefault", None, func())
    pipeline.register_step(
        "notbydefault", None, build_parameters(run_by_default=False)(func())
    )

    pipeline.list_all_steps(["notbydefault"])

    messages = [
        ANSI_COLOR_CODES_RE.sub("", m).strip() for m in caplog.messages
    ]
    assert "- bydefault" in messages
    assert "* notbydefault" in messages


def test_listing_can_show_dependencies(pipeline, caplog):
    pipeline.register_step("step-1", None, func())
    pipeline.register_step("step-2", None, step_with_requirements(["step-1"]))
    pipeline.register_step("step-3", None, step_with_requirements(["step-2"]))
    pipeline.list_all_steps(show_dependencies=True)

    messages = [
        ANSI_COLOR_CODES_RE.sub("", m).strip() for m in caplog.messages
    ]
    assert "* step-1" in messages
    assert "* step-2 --> step-1" in messages
    assert "* step-3 --> step-2" in messages


def test_listing_can_show_description(pipeline, caplog):
    pipeline.register_step("step-1", "this is a step", func())
    pipeline.register_step("step-2", None, func())

    # First check it doesnt' show on low verbosity
    pipeline.config.verbosity = 0

    pipeline.list_all_steps()
    messages = [
        ANSI_COLOR_CODES_RE.sub("", m).strip() for m in caplog.messages
    ]
    assert "* step-1" in messages
    assert "* step-2" in messages

    caplog.handler.reset()

    # Then check it shows with higher verbosity
    pipeline.config.verbosity = 1

    pipeline.list_all_steps()
    messages = [
        ANSI_COLOR_CODES_RE.sub("", m).strip() for m in caplog.messages
    ]
    assert "* step-1" not in messages
