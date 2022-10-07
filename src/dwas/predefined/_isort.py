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
        "dependencies": ["isort[colors]"],
        "additional_arguments": ["--check-only", "--diff"],
        "files": ["."],
    }
)
class Isort(Step):
    def __init__(self) -> None:
        self.__name__ = "isort"

    def __call__(
        self,
        step: StepHandler,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        if step.config.colors:
            additional_arguments.append("--color")

        step.run(["isort", *additional_arguments, *files])


def isort(
    *,
    name: Optional[str] = None,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    dependencies: Optional[List[str]] = None,
) -> None:
    """
    Run `the isort formatter`_ against your python source code.

    :param name: The name to give to the step.
                 Defaults to :python:`"isort"`.
    :param files: The list of files or directories to run ``isort`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``isort``
                                 invocation.
                                 Defaults to :python:`["--check-only", "--diff"]`.
    :param python: The version of python to use.
                   Defaults to the version *dwas* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["isort[colors]"]`.
    :param run_by_default: Whether to run this step by default or not.
                           Defaults to :python:`True`.

    .. tip::

        isort can be quite slow to find all files it needs to handle, you might
        want to limit the number of directories searched.

    :Examples:

        In order to verify your code but not change it, for a step
        named **isort**:

        .. code-block::

            dwas.predefined.isort(files["src", "tests", "dwasfile.py", "setup.py"])

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            dwas.predefined.isort(
                # Note: this name is arbitrary, you could omit it, or specify
                #       something else. We suffix in our documentation all
                #       operations that will have destructive effect on the source
                #       code by ``:fix``
                name="isort:fix",
                additional_arguments=["--atomic"],
                run_by_default=False,
                files=["src,", "tests", "dwasfile.py", "setup.py"],
            )
    """
    isort_ = Isort()

    if files is not None:
        isort_ = parametrize("files", [files])(isort_)
    if additional_arguments is not None:
        isort_ = parametrize("additional_arguments", [additional_arguments])(
            isort_
        )

    register_managed_step(
        isort_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
