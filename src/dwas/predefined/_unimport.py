from typing import List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults


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
        additional_arguments = additional_arguments.copy()

        if not any(arg.startswith("--color") for arg in additional_arguments):
            color_arg = (
                f"--color={'always' if step.config.colors else 'never'}"
            )
            additional_arguments.append(color_arg)

        step.run(["unimport", *additional_arguments, *files])


def unimport(
    *,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
) -> Step:
    """
    Run `the Unimport formatter`_ against your python source code.

    By default, it will depend on :python:`["unimport"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    :param files: The list of files or directories to run ``unimport`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``unimport``
                                 invocation.
                                 Defaults to :python:`["--check", "--diff", "--gitignore"]`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        In order to verify your code but not change it, for a step
        named **unimport**:

        .. code-block::

            dwas.register_managed_step(dwas.predefined.unimport())

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.unimport(
                    # NOTE: `--gitignore` here is not required, but probably a good idea
                    additional_arguments=["--remove", "--gitignore"],
                ),
                # NOTE: this name is arbitrary, you could omit it, or specify
                #       something else. We suffix in our documentation all
                #       operations that will have destructive effect on the source
                #       code by ``:fix``
                name="unimport:fix",
                run_by_default=False,
            )

        Note that if you have other steps that will overwrite some of your files,
        you might want to order them so they don't conflict. For example, assuming
        that you also use :py:func:`dwas.predefined.isort`:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.unimport(
                    # NOTE: `--gitignore` here is not required, but probably a good idea
                    additional_arguments=["--remove", "--gitignore"],
                ),
                name="unimport:fix",
                run_by_default=False,
            )
            dwas.register_managed_step(
                dwas.predefined.isort(additional_arguments=["--atomic"]),
                name="isort:fix",
                requires=["unimport:fix"],
                run_by_default=False,
            )

        This will ensure that both steps don't step on each other and make
        unimport run first.
    """
    return build_parameters(
        files=files, additional_arguments=additional_arguments
    )(Unimport())
