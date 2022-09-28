import logging
import os
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

LOGGER = logging.getLogger(__name__)


@set_defaults(
    {
        "dependencies": ["twine"],
        "additional_arguments": ["check", "--strict"],
        "passenv": [],
    }
)
class Twine(Step):
    __name__ = "twine"

    def __call__(
        self,
        step: StepHandler,
        additional_arguments: List[str],
        passenv: List[str],
    ) -> None:
        sdists = step.get_artifacts("sdists")
        wheels = step.get_artifacts("wheels")
        if not sdists and not wheels:
            raise Exception("No sdists or wheels provided")

        env = {}
        for env_name in passenv:
            if env_name not in os.environ:
                LOGGER.warning(
                    "Asked to pass %s as environment variable, but variable is not present",
                    env_name,
                )
            else:
                env[env_name] = os.environ[env_name]

        step.run(["twine", *additional_arguments, *sdists, *wheels], env=env)


def twine(
    *,
    name: Optional[str] = None,
    additional_arguments: Optional[List[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    passenv: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> None:
    twine_ = Twine()

    if additional_arguments is not None:
        twine_ = parametrize(
            "additional_arguments", [additional_arguments], ids=[""]
        )(twine_)
    if passenv is not None:
        twine_ = parametrize("passenv", [passenv], ids=[""])(twine_)

    register_managed_step(
        twine_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
