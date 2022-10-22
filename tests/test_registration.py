import sys
from typing import Any, Dict, List, Optional

import pytest

from dwas import parametrize, register_step
from dwas._exceptions import BaseDwasException
from dwas._pipeline import Pipeline, set_pipeline
from dwas._steps.handlers import BaseStepHandler, StepGroupHandler, StepHandler
from dwas._steps.registration import register_managed_step

from ._utils import isolated_context


def _get_all_steps_from_pipeline(pipeline: Pipeline) -> Dict[str, Any]:
    # We are testing some internals here
    # pylint: disable=protected-access
    def _format_step(step: BaseStepHandler) -> Dict[str, Any]:
        if isinstance(step, StepGroupHandler):
            return {
                "type": "group",
                "requires": step._requires,
                "run_by_default": step._run_by_default,
            }

        assert isinstance(step, StepHandler)

        parameters = step.parameters.copy()
        # XXX: The parameters always contain the current step, we don't need to
        # validate that, it makes the rest of the logic too complex
        parameters.pop("step")

        return {
            "python": step.python,
            "run_by_default": step._run_by_default,
            "requires": step._requires,
            "parameters": parameters,
        }

    pipeline._resolve_steps()
    return {key: _format_step(step) for key, step in pipeline._steps.items()}


def _expect_step(
    *,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if python is None:
        python = f"python{sys.version_info[0]}.{sys.version_info[1]}"
    if run_by_default is None:
        run_by_default = True
    if requires is None:
        requires = []
    if parameters is None:
        parameters = {}

    return {
        "python": python,
        "run_by_default": run_by_default,
        "requires": requires,
        "parameters": parameters,
    }


@pytest.mark.parametrize(
    ("name", "python", "run_by_default"),
    (
        pytest.param(None, None, None, id="defaults"),
        pytest.param("my_step", None, None, id="force_name"),
        pytest.param(None, "2.8", None, id="version_python"),
        pytest.param(None, "python2.8", None, id="explicit_python"),
        pytest.param(None, None, True, id="run_by_default"),
        pytest.param(None, None, False, id="no_run_by_default"),
    ),
)
@isolated_context
def test_can_register_step(pipeline, name, python, run_by_default):
    set_pipeline(pipeline)

    def noop():
        pass  # pragma: nocover

    register_step(
        noop, name=name, python=python, run_by_default=run_by_default
    )

    steps = _get_all_steps_from_pipeline(pipeline)

    if python == "2.8":
        python = "python2.8"
    if name is None:
        name = "noop"

    assert steps == {
        name: _expect_step(python=python, run_by_default=run_by_default)
    }


@isolated_context
def test_registering_parametrized_step_creates_multiple_entries(pipeline):
    set_pipeline(pipeline)

    # Register the step
    @parametrize("param", [1, 2])
    def noop():
        pass  # pragma: nocover

    register_step(noop)

    steps = _get_all_steps_from_pipeline(pipeline)
    assert steps == {
        "noop": {
            "requires": ["noop[1]", "noop[2]"],
            "run_by_default": True,
            "type": "group",
        },
        "noop[1]": _expect_step(parameters={"param": 1}),
        "noop[2]": _expect_step(parameters={"param": 2}),
    }


@isolated_context
def test_handles_step_with_no_name(pipeline):
    set_pipeline(pipeline)

    class Broken:
        def __call__(self) -> None:
            pass  # pragma: nocover

    with pytest.raises(BaseDwasException) as exc_wrapper:
        register_step(Broken())

    assert "does not implement `__name__`" in str(exc_wrapper.value)


@pytest.mark.parametrize(
    "from_parameters", [True, False], ids=["from_parameters", "direct"]
)
@isolated_context
def test_can_register_managed_step(pipeline, from_parameters):
    set_pipeline(pipeline)

    def noop():
        pass  # pragma: nocover

    if from_parameters:
        noop = parametrize("dependencies", [["one"]])(noop)
        kwargs: Dict[str, Any] = {}
    else:
        kwargs = {"dependencies": ["one"]}

    register_managed_step(noop, **kwargs)

    steps = _get_all_steps_from_pipeline(pipeline)
    assert steps == {
        "noop": _expect_step(parameters={"dependencies": ["one"]})
    }


@isolated_context
def test_cannot_override_setup_with_managed_step(pipeline):
    set_pipeline(pipeline)

    class Noop:
        def setup(self) -> None:
            pass

        def __call__(self) -> None:
            pass

    with pytest.raises(BaseDwasException) as exc_wrapper:
        register_managed_step(Noop())

    assert "already implements `setup`" in str(exc_wrapper.value)
