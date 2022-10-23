import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner
from .. import parametrize as apply_parameters
from .. import register_managed_step, set_defaults

LOGGER = logging.getLogger(__name__)


@set_defaults({"dependencies": ["pytest"], "args": []})
class Pytest(Step):
    def __init__(self) -> None:
        self.__name__ = "pytest"

    def gather_artifacts(self, step: StepRunner) -> Dict[str, List[Any]]:
        coverage_file = self._get_coverage_file(step)
        if coverage_file is None or not coverage_file.exists():
            return {}

        return {"coverage_files": [str(coverage_file)]}

    def __call__(self, step: StepRunner, args: Sequence[str]) -> None:
        step.run(
            ["pytest", *args],
            env={"COVERAGE_FILE": str(self._get_coverage_file(step))},
        )

    def _get_coverage_file(self, step: StepRunner) -> Path:
        return step.cache_path / "reports" / "coverage"


def pytest(
    *,
    name: Optional[str] = None,
    args: Optional[Sequence[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[Sequence[str]] = None,
    run_by_default: Optional[bool] = None,
) -> Step:
    """
    Run `pytest`_.

    :param name: The name to give to the step.
                 Defaults to :python:`"pytest"`.
    :param args: arguments to pass to the ``pytest`` invocation.
                 Defaults to :python:`[]`.
    :param python: The version of python to use.
                   Defaults to the version *dwas* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["pytest"]`.
    :param run_by_default: Whether to run this step by default or not.
                           If :python:`None`, will default to :python:`True`.
    :return: The step so that you can add additional parameters to it if needed.

    .. tip::

        If you use ``pytest-cov``, it will also automatically expose a
        ``coverage_files`` :term:`artifact` that can be used by dependent steps,
        for an example, see :py:func:`coverage`

    :Examples:

        For running pytest with the a specific version of python, with your
        code in the `PYTHONPATH`:

        .. code-block::

            dwas.predefined.pytest(python="3.9")

        Or, for a more concrete example, across multiple versions of python and
        testing your installed application:

        .. code-block::

            # Setup a "package" step, to install the source code automatically
            # for the tests
            dwas.predefined.package()

            dwas.parametrize("python", ["3.8", "3.9", "3.10"])(
                dwas.predefined.pytest(
                    dependencies=["pytest", "pytest-cov"],
                    requires=["package"],
                )
            )

        Leveraging :py:func:`dwas.parametrize`, this generates 4 different
        steps: ``pytest``, which is a :term:`step group` which depends on the
        other ``pytest[3.8]``, ``pytest[3.9]`` and ``pytest[3.10]`` which each
        run pytest with the given version of python.

        Similarly, if you wanted to test multiple multiple versions of a python
        package, with different versions of python:

        .. code-block::

            dwas.parametrize("python", ["3.8", "3.9", "3.10"])(
                dwas.parametrize(
                    "dependencies",
                    [["pytest", "django==3.0"], ["pytest", "django==4.0"]],
                    ids=["django3", "django4"],
                )(dwas.predefined.pytest(requires=["package"])
            )
    """
    pytest_ = Pytest()

    if args is not None:
        pytest_ = apply_parameters("args", [args])(pytest_)

    return register_managed_step(
        pytest_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
