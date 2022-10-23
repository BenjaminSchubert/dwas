from typing import List, Optional

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import (
    Step,
    StepRunner,
    parametrize,
    register_managed_step,
    set_defaults,
)


@set_defaults(
    {
        "dependencies": ["coverage"],
        "reports": [["report", "--show-missing"]],
    }
)
class Coverage(Step):
    def __init__(self) -> None:
        self.__name__ = "coverage"

    def __call__(
        self,
        step: StepRunner,
        reports: List[List[str]],
    ) -> None:
        env = {"COVERAGE_FILE": str(step.cache_path / "coverage")}

        coverage_files = step.get_artifacts("coverage_files")
        if not coverage_files:
            raise Exception("No coverage files provided. Can't proceed")

        step.run(["coverage", "combine", "--keep", *coverage_files], env=env)

        for report in reports:
            step.run(["coverage", *report], env=env)


def coverage(
    *,
    name: Optional[str] = None,
    reports: Optional[List[List[str]]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> Step:
    """
    Run `coverage.py`_ to generate coverage reports.

    :param name: The name to give to the step.
                 Defaults to :python:`"coverage"`.
    :param reports: A list of parameters to pass to coverage to generate
                    reports.
                    Defaults to :python:`[["report", "--show-missing"]]`
    :param python: The version of python to use.
                   Defaults to the version *dwas* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["coverage"]`.
    :param run_by_default: Whether to run this step by default or not.
                           Defaults to :python:`True`.

    This step leverages :term:`artifacts<artifact>` named ``coverage_files`` provided by
    other steps to provide reports.

    :Example:

        Here is a fully fledged example that packages source code, runs pytest
        and generates coverage out of it:

        .. code-block::

            # One step to generate the package
            dwas.predefined.package()

            # One step to run pytest across multiple python versions
            dwas.predefined.pytest(
                dependencies=["pytest", "pytest-cov"],
                requires=["package"],
                parametrize=dwas.parametrize("python", ["3.8", "3.9", "3.10"])
            )

            # And finally generate xml report and one on stdout.
            # This will combine all coverage info from the previous pytest runs.
            dwas.predefined.coverage(
                reports=[
                    ["xml", "-o", "reports/coverage.xml"],
                    ["report", "--show-missing"],
                ],
                requires=["pytest"],
            )

    :return: The step so that you can add additional parameters to it if needed.
    """
    coverage_ = Coverage()

    if reports is not None:
        coverage_ = parametrize("reports", [reports])(coverage_)

    return register_managed_step(
        coverage_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
