from typing import List, Optional

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import (
    Step,
    StepHandler,
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
    __name__ = "coverage"

    def __call__(
        self,
        step: StepHandler,
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
    run_by_default: bool = True,
) -> None:
    coverage_ = Coverage()

    if reports is not None:
        coverage_ = parametrize("reports", [reports], ids=[""])(coverage_)

    register_managed_step(
        coverage_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
