import json
from pathlib import Path

import dwas
from dwas import StepRunner
from dwas.predefined import package

dwas.register_managed_step(package())


@dwas.step(requires=["package"])
def check_install(step: StepRunner) -> None:
    step.run(["python", "-m", "test_project"])


@dwas.step(requires=["package"], run_by_default=False)
def output_artifacts(step: StepRunner) -> None:
    Path("artifacts.json").write_text(
        json.dumps(
            {
                "sdists": step.get_artifacts("sdists"),
                "wheels": step.get_artifacts("wheels"),
            }
        ),
        "utf-8",
    )
