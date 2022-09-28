import logging
import os
from typing import List, Optional, Sequence

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
    {"dependencies": ["mypy"], "additional_arguments": [], "files": ["."]}
)
class Mypy(Step):
    __name__ = "mypy"

    def __call__(
        self,
        step: StepHandler,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        env = {}
        if step.config.colors:
            env["MYPY_FORCE_COLOR"] = "1"
            # pylint: disable=line-too-long
            # Mypy requires a valid term for color settings
            # See https://github.com/python/mypy/blob/eb1c52514873b27db93ccb8abecb4b4713feb667/mypy/util.py#L551
            if "TERM" in os.environ:
                env["TERM"] = os.environ["TERM"]
            else:
                LOGGER.warning(
                    "No TERM set, mypy won't be able to show colors"
                )

        step.run(["mypy", *additional_arguments, *files], env=env)


def mypy(
    *,
    name: Optional[str] = None,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[Sequence[str]] = None,
    run_by_default: Optional[bool] = None,
) -> None:
    mypy_ = Mypy()

    if files is not None:
        mypy_ = parametrize("files", [files], ids=[""])(mypy_)
    if additional_arguments is not None:
        mypy_ = parametrize(
            "additional_arguments", [additional_arguments], ids=[""]
        )(mypy_)

    register_managed_step(
        mypy_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
