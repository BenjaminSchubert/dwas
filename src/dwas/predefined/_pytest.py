import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, TypeVar

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepHandler
from .. import parametrize as apply_parameters
from .. import register_managed_step, set_defaults

T = TypeVar("T")
LOGGER = logging.getLogger(__name__)


@set_defaults({"dependencies": ["pytest"], "args": []})
class Pytest(Step):
    __name__ = "pytest"

    def gather_artifacts(self, step: StepHandler) -> Dict[str, List[Any]]:
        coverage_file = self._get_coverage_file(step)
        if coverage_file is None or not coverage_file.exists():
            return {}

        return {"coverage_files": [str(coverage_file)]}

    def __call__(self, step: StepHandler, args: Sequence[str]) -> None:
        step.run(
            ["pytest", *args],
            env={"COVERAGE_FILE": str(self._get_coverage_file(step))},
        )

    def _get_coverage_file(self, step: StepHandler) -> Path:
        return step.cache_path / "reports" / "coverage"


def pytest(
    *,
    name: Optional[str] = None,
    args: Optional[Sequence[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    dependencies: Optional[Sequence[str]] = None,
    parametrize: Optional[Callable[[T], T]] = None,
) -> None:
    pytest_ = Pytest()

    if args is not None:
        pytest_ = apply_parameters("args", [args], ids=[""])(pytest_)

    if parametrize is not None:
        pytest_ = parametrize(pytest_)  # type: ignore

    register_managed_step(
        pytest_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
