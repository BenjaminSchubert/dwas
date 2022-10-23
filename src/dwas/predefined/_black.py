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
        if (
            "--color" not in additional_arguments
            and "--no-color" not in additional_arguments
        ):
            color_arg = f"--{'' if step.config.colors else 'no-'}color"
            additional_arguments.append(color_arg)

        step.run(["black", *additional_arguments, *files])


def black(
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
    Run `the Black formatter`_ against your python source code.

    :param name: The name to give to the step.
                 Defaults to :python:`"black"`.
    :param files: The list of files or directories to run ``black`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``black``
                                 invocation.
                                 Defaults to :python:`["--check", "--diff", "-W1"]`.
    :param python: The version of python to use.
                   Defaults to the version *dwas* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["black"]`.
    :param run_by_default: Whether to run this step by default or not.
                           Defaults to :python:`True`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        In order to verify your code but not change it, for a step
        named **black**:

        .. code-block::

            dwas.predefined.black()

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            dwas.predefined.black(
                # Note: this name is arbitrary, you could omit it, or specify
                #       something else. We suffix in our documentation all
                #       operations that will have destructive effect on the source
                #       code by ``:fix``
                name="black:fix",
                additional_arguments=[],
                run_by_default=False,
            )

        Note that if you have other steps that will overwrite some of your files,
        you might want to order them so they don't conflict. For example, assuming
        that you also use :py:func:`dwas.predefined.isort`:

        .. code-block::

            dwas.predefined.isort(
                name="isort:fix",
                additional_arguments=["--atomic"],
                run_by_default=False,
            )
            dwas.predefined.black(
                name="black:fix",
                requires=["isort:fix"],
                additional_arguments=[],
                run_by_default=False,
            )

        This will ensure that both steps don't step on each other and make black run
        second.
    """

    black_ = Black()

    black_ = build_parameters(
        files=files, additional_arguments=additional_arguments
    )(black_)

    return register_managed_step(
        black_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
