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
        step: StepHandler,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        if step.config.colors and not [
            p
            for p in additional_arguments
            if p.startswith("--output-format") or p.startswith("-f")
        ]:
            additional_arguments.append("--output-format=colorized")

        cmd = ["pylint", *additional_arguments, *files]
        step.run(cmd)


def pylint(
    *,
    name: str = "pylint",
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[Sequence[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[Sequence[str]] = None,
    run_by_default: Optional[bool] = None,
) -> None:
    """
    Run `pylint`_ against your source code.

    :param name: The name to give to the step.
                 Defaults to :python:`"pylint"`.
    :param files: The list of files or directories to run ``pylint`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``pylint``
                                 invocation.
                                 Defaults to :python:`[]`.
    :param python: The version of python to use.
                   Defaults to the version *dwas* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["pylint"]`.
    :param run_by_default: Whether to run this step by default or not.
                           Defaults to :python:`True`.

    :Examples:

        .. code-block::

            dwas.predefined.pylint(
                files=["./src", "./tests"],
                # Install both test and package dependencies to make pylint
                # find them
                dependencies=["requests", "pytest", "pylint"],
            )
    """
    pylint_ = Pylint()

    if files is not None:
        pylint_ = parametrize("files", [files])(pylint_)
    if additional_arguments is not None:
        pylint_ = parametrize("additional_arguments", [additional_arguments])(
            pylint_
        )

    register_managed_step(
        pylint_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
