from typing import List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import (
    Step,
    StepRunner,
    build_parameters,
    register_managed_step,
    set_defaults,
)


@set_defaults(
    {
        "dependencies": ["unimport"],
        "files": ["."],
        "additional_arguments": ["--check", "--diff", "--gitignore"],
    }
)
class Unimport(Step):
    def __init__(self) -> None:
        self.__name__ = "unimport"

    def __call__(
        self,
        step: StepRunner,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        if not any(arg.startswith("--color") for arg in additional_arguments):
            color_arg = (
                f"--color={'always' if step.config.colors else 'never'}"
            )
            additional_arguments.append(color_arg)

        step.run(["unimport", *additional_arguments, *files])


def unimport(
    *,
    name: Optional[str] = None,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> Step:
    """
    Run `the Unimport formatter`_ against your python source code.

    If the `dwas` cache is part of the running directory, it will automatically
    get ignored.

    :param name: The name to give to the step.
                 Defaults to :python:`"unimport"`.
    :param files: The list of files or directories to run ``unimport`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``unimport``
                                 invocation.
                                 Defaults to :python:`["--check", "--diff", "--gitignore"]`.
    :param python: The version of python to use.
                   Defaults to the version *dwas* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["unimport"]`.
    :param run_by_default: Whether to run this step by default or not.
                           Defaults to :python:`True`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        In order to verify your code but not change it, for a step
        named **unimport**:

        .. code-block::

            dwas.predefined.unimport()

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            dwas.predefined.unimport(
                # Note: this name is arbitrary, you could omit it, or specify
                #       something else. We suffix in our documentation all
                #       operations that will have destructive effect on the source
                #       code by ``:fix``
                name="unimport:fix",
                # NOTE: `--gitignore` here is not required, but probably a good idea
                additional_arguments=["--remove", "--gitignore"],
                run_by_default=False,
            )

        Note that if you have other steps that will overwrite some of your files,
        you might want to order them so they don't conflict. For example, assuming
        that you also use :py:func:`dwas.predefined.isort`:

        .. code-block::

            dwas.predefined.unimport(
                name="unimport:fix",
                # NOTE: `--gitignore` here is not required, but probably a good idea
                additional_arguments=["--remove", "--gitignore"],
                run_by_default=False,
            )
            dwas.predefined.isort(
                name="isort:fix",
                additional_arguments=["--atomic"],
                requires=["unimport:fix"],
                run_by_default=False,
            )

        This will ensure that both steps don't step on each other and make
        unimport run first.
    """

    unimport_ = Unimport()

    unimport_ = build_parameters(
        files=files, additional_arguments=additional_arguments
    )(unimport_)

    return register_managed_step(
        unimport_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
