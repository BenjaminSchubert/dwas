from typing import List, Optional

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, parametrize, set_defaults


@set_defaults(
    {
        "dependencies": ["coverage"],
        "reports": [["report", "--show-missing"]],
    }
)
class Coverage(Step):
    # TODO: this can create files outside the cache but does not offer a
    #       convenient way for hooking into `--clean`.
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
            # pylint: disable=broad-exception-raised
            raise Exception("No coverage files provided. Can't proceed")

        step.run(["coverage", "combine", "--keep", *coverage_files], env=env)

        for report in reports:
            step.run(["coverage", *report], env=env)


def coverage(*, reports: Optional[List[List[str]]] = None) -> Step:
    """
    Run `coverage.py`_ to generate coverage reports.

    By default, it will depend on :python:`["coverage"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    :param reports: A list of parameters to pass to coverage to generate
                    reports.
                    Defaults to :python:`[["report", "--show-missing"]]`

    This step leverages :term:`artifacts<artifact>` named ``coverage_files`` provided by
    other steps to provide reports.

    :Example:

        Here is a fully fledged example that packages source code, runs pytest
        and generates coverage out of it:

        .. code-block::

            # One step to generate the package
            dwas.register_managed_step(dwas.predefined.package())

            # One step to run pytest across multiple python versions
            dwas.register_managed_step(
                dwas.parametrize("python", ["3.8", "3.9", "3.10"])(
                    dwas.predefined.pytest()
                ),
                dependencies=["pytest', "pytest-cov"],
                requires=["package"]
            )

            # And finally generate xml report and one on stdout.
            # This will combine all coverage info from the previous pytest runs.
            dwas.register_managed_step(
                dwas.predefined.coverage(
                    reports=[
                        ["xml", "-o", "reports/coverage.xml"],
                        ["report", "--show-missing"],
                    ],
                ),
                requires=["pytest"],
            )

    :return: The step so that you can add additional parameters to it if needed.
    """
    coverage_ = Coverage()

    if reports is not None:
        coverage_ = parametrize("reports", [reports])(coverage_)

    return coverage_
