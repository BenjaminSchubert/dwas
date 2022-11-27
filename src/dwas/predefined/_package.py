import logging
import shutil
from contextlib import suppress
from typing import Any, Dict, List

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import (
    Step,
    StepRunner,
    StepWithDependentSetup,
    parametrize,
    set_defaults,
)

LOGGER = logging.getLogger(__name__)


@set_defaults({"dependencies": ["build"], "isolate": True})
class Package(StepWithDependentSetup):
    def __init__(self) -> None:
        self.__name__ = "package"

    def gather_artifacts(self, step: StepRunner) -> Dict[str, List[Any]]:
        artifacts = {}
        sdists = [str(p) for p in step.cache_path.glob("*.tar.gz")]
        if sdists:
            artifacts["sdists"] = sdists

        wheels = [str(p) for p in step.cache_path.glob("*.whl")]
        if wheels:
            artifacts["wheels"] = wheels

        return artifacts

    def setup_dependent(
        self, original_step: StepRunner, current_step: StepRunner
    ) -> None:
        wheels = list(original_step.cache_path.glob("*.whl"))
        assert len(wheels) == 1

        LOGGER.debug("Installing wheel with its dependencies")
        current_step.run(
            [current_step.python, "-m", "pip", "install", str(wheels[0])],
            silent_on_success=current_step.config.verbosity < 2,
        )

        LOGGER.debug(
            "Forcing reinstallation of the wheel in case it had code changes"
        )
        current_step.run(
            [
                current_step.python,
                "-m",
                "pip",
                "install",
                "--force-reinstall",
                "--no-deps",
                str(wheels[0]),
            ],
            silent_on_success=current_step.config.verbosity < 2,
        )

    def __call__(self, step: StepRunner, isolate: bool) -> None:
        with suppress(FileNotFoundError):
            shutil.rmtree(step.cache_path)

        command = [step.python, "-m", "build", f"--outdir={step.cache_path}"]
        if not isolate:
            command.append("--no-isolation")

        step.run(command, silent_on_success=step.config.verbosity < 1)


def package(*, isolate: bool = True) -> Step:
    """
    Build a python package that follows :pep:`517`, and install it in dependent venvs.

    .. warning::

        This step is not suitable for building wheels with C extensions. If you
        have such requirements, please see `the manylinux project`_, or other
        similar initiatives.

    By default, it will depend on :python:`["build"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    :param isolate: Whether to create a new virtual environment for building the
                    package, or run it in the one created for the step.
                    Setting this to :python:`False` does bring a measurable
                    speedup, but might lead to under-declared build dependencies.
                    Defaults to :python:`True`.
    :return: The step so that you can add additional parameters to it if needed.

    This leverages ``python -m build`` in order to build a source distribution
    and a universal wheel (assuming there are no c-extensions).

    When this step is used as a requirement for another step, it will also
    install the wheel inside it.

    This allows you to only build the sdist and wheel once, and then install
    your package in various different other steps, speeding up your whole
    pipeline. It also helps ensuring that your packaging is correct, as you
    end up running against the same version as if you were installing your
    project from e.g. pypi.

    .. tip::

        Using :python:`isolate=False` will speedup measurably this step, but reduces
        your confidence in not under-declaring build dependencies.

    :Examples:

        In order to generate a step ``package``:

        .. code-block::

            dwas.register_managed_step(dwas.predefined.package())

        Or, if you want your step to run faster:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.package(isolate=False),
                # We could read those from pyproject.toml directly, but we'd need
                # to install a toml reading library, so let's live with duplication
                # for now.
                dependencies=["build", "setuptools>=61.0.0", "wheel"],
            )
    """
    return parametrize("isolate", [isolate])(Package())
