from __future__ import annotations

from typing import Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults


@set_defaults(
    {
        "dependencies": ["pylint"],
        "additional_arguments": [],
        "files": ["."],
    }
)
class Pylint(Step):
    def __init__(self) -> None:
        self.__name__ = "pylint"

    def __call__(
        self,
        step: StepRunner,
        files: Sequence[str],
        additional_arguments: list[str],
    ) -> None:
        additional_arguments = additional_arguments.copy()

        if step.config.colors and not [
            p
            for p in additional_arguments
            if p.startswith(("--output-format", "-f"))
        ]:
            additional_arguments.append("--output-format=colorized")

        cmd = ["pylint", *additional_arguments, *files]
        step.run(cmd)


def pylint(
    *,
    files: Sequence[str] | None = None,
    additional_arguments: Sequence[str] | None = None,
) -> Step:
    """
    Run `pylint`_ against your source code.

    By default, it will depend on :python:`["pylint"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    :param files: The list of files or directories to run ``pylint`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``pylint``
                                 invocation.
                                 Defaults to :python:`[]`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.pylint(files=["./src", "./tests"]),
                # Install both test and package dependencies to make pylint
                # find them
                dependencies=["requests", "pytest", "pylint"],
            )
    """
    return build_parameters(
        files=files,
        additional_arguments=additional_arguments,
    )(Pylint())
