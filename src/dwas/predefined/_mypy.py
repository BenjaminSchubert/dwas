import logging
import os
from typing import List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults

LOGGER = logging.getLogger(__name__)


@set_defaults(
    {"dependencies": ["mypy"], "additional_arguments": [], "files": ["."]}
)
class Mypy(Step):
    def __init__(self) -> None:
        self.__name__ = "mypy"

    def __call__(
        self,
        step: StepRunner,
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
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
) -> Step:
    """
    Run `mypy`_ against your python source code.

    By default, it will depend on :python:`["mypy"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    :param files: The list of files, directories or packages to run ``mypy``
                  against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``mypy``
                                 invocation.
                                 Defaults to :python:`[]`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        .. code-block::

            dwas.register_managed_step(
                # Only run for sources, not tests/ or setup.py
                dwas.predefined.mypy(files=["./src"]),
                dependencies=["mypy", "types-requests"],
            )
    """
    return build_parameters(
        files=files,
        additional_arguments=additional_arguments,
    )(Mypy())
