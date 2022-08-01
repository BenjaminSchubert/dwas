import shutil
from contextlib import suppress
from typing import Any, Dict, List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import (
    StepHandler,
    StepWithDependentSetup,
    parametrize,
    register_managed_step,
    set_defaults,
)


@set_defaults({"dependencies": ["build"], "isolate": True})
class Package(StepWithDependentSetup):
    __name__ = "package"

    def gather_artifacts(self, step: StepHandler) -> Dict[str, List[Any]]:
        artifacts = {}
        sdists = [str(p) for p in step.cache_path.glob("*.tar.gz")]
        if sdists:
            artifacts["sdists"] = sdists

        wheels = [str(p) for p in step.cache_path.glob("*.whl")]
        if wheels:
            artifacts["wheels"] = wheels

        return artifacts

    def setup_dependent(
        self, original_step: StepHandler, current_step: StepHandler
    ) -> None:
        wheels = list(original_step.cache_path.glob("*.whl"))
        assert len(wheels) == 1

        current_step.run(
            [current_step.python, "-m", "pip", "install", str(wheels[0])],
            silent_on_success=current_step.config.verbosity < 2,
        )

    def __call__(self, step: StepHandler, isolate: bool) -> None:
        with suppress(FileNotFoundError):
            shutil.rmtree(step.cache_path)

        command = [step.python, "-m", "build", f"--outdir={step.cache_path}"]
        if not isolate:
            command.append("--no-isolation")

        step.run(command, silent_on_success=step.config.verbosity < 1)


def package(
    *,
    name: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: bool = True,
    isolate: bool = True,
    dependencies: Optional[Sequence[str]] = None,
) -> None:
    package_ = Package()
    package_ = parametrize("isolate", [isolate], ids=[""])(package_)

    register_managed_step(
        package_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
