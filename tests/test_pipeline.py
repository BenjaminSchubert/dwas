from datetime import timedelta

import pytest

from dwas._steps.parametrize import build_parameters


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
                "step-1": ["step-1-1", "step-1-3"],
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

    def func():
        return lambda: None  # pragma: nocover

    # Sub steps
    pipeline.register_step(
        "step-1-1", None, build_parameters(requires=["step-1-1-1"])(func())
    )
    pipeline.register_step(
        "step-1-2", None, build_parameters(requires=["step-1-2-1"])(func())
    )
    pipeline.register_step_group("step-1-3", ["step-1-3-1"])

    # Sub sub steps
    pipeline.register_step("step-1-1-1", None, func())
    pipeline.register_step("step-1-2-1", None, func())
    pipeline.register_step("step-1-3-1", None, func())

    # pylint: disable=protected-access
    assert pipeline._build_graph(steps, except_steps, only_selected) == result
