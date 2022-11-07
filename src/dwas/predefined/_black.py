from typing import List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults


@set_defaults(
    {
        "dependencies": ["black"],
        "files": ["."],
        "additional_arguments": ["--check", "--diff", "-W1"],
    }
)
class Black(Step):
    def __init__(self) -> None:
        self.__name__ = "black"

    def __call__(
        self,
        step: StepRunner,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        additional_arguments = additional_arguments.copy()

        if (
            "--color" not in additional_arguments
            and "--no-color" not in additional_arguments
        ):
            color_arg = f"--{'' if step.config.colors else 'no-'}color"
            additional_arguments.append(color_arg)

        step.run(["black", *additional_arguments, *files])


def black(
    *,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
) -> Step:
    """
    Run `the Black formatter`_ against your python source code.

    By default, it will depend on :python:`["black"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    :param files: The list of files or directories to run ``black`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``black``
                                 invocation.
                                 Defaults to :python:`["--check", "--diff", "-W1"]`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        In order to verify your code but not change it, for a step
        named **black**:

        .. code-block::

            register_managed_step(dwas.predefined.black())

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            register_managed_step(
                dwas.predefined.black(additional_arguments=[]),
                # NOTE: this name is arbitrary, you could omit it, or specify
                #       something else. We suffix in our documentation all
                #       operations that will have destructive effect on the source
                #       code by ``:fix``
                name="black:fix",
                run_by_default=False,
            )

        Note that if you have other steps that will overwrite some of your files,
        you might want to order them so they don't conflict. For example, assuming
        that you also use :py:func:`dwas.predefined.isort`:

        .. code-block::

            register_managed_step(
                dwas.predefined.isort(additional_arguments=["--atomic"]),
                name="isort:fix",
                run_by_default=False,
            )
            register_managed_step(
                dwas.predefined.black(additional_arguments=[]),
                name="black:fix",
                run_by_default=False,
            )

        This will ensure that both steps don't step on each other and make black run
        second.
    """
    return build_parameters(
        files=files, additional_arguments=additional_arguments
    )(Black())
