from __future__ import annotations

from typing import Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults


@set_defaults(
    {
        "dependencies": ["ruff"],
        "files": ["."],
        "additional_arguments": ["check"],
    }
)
class Ruff(Step):
    def __init__(self) -> None:
        self.__name__ = "ruff"

    def __call__(
        self,
        step: StepRunner,
        files: Sequence[str],
        additional_arguments: list[str],
    ) -> None:
        step.run(
            ["ruff", *additional_arguments, *files],
            env={"RUFF_CACHE_DIR": str(step.cache_path / "ruff-cache")},
        )


def ruff(
    *,
    files: Sequence[str] | None = None,
    additional_arguments: list[str] | None = None,
) -> Step:
    """
    Run `Ruff`_ against your python source code.

    By default, it will depend on :python:`["ruff"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    :param files: The list of files or directories to run ``ruff`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``ruff``
                                 invocation. Defaults to :python:`["check"]`.
                                 Defaults to :python:`["--check", "--diff", "-W1"]`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        In order to verify your code but not change it, for a step
        named **ruff**:

        .. code-block::

            register_managed_step(dwas.predefined.ruff())

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            register_managed_step(
                dwas.predefined.ruff(additional_arguments=["check", "--fix"]),
                # NOTE: this name is arbitrary, you could omit it, or specify
                #       something else. We suffix in our documentation all
                #       operations that will have destructive effect on the source
                #       code by ``:fix``
                name="ruff:fix",
                run_by_default=False,
            )

        Similarly, if you want to use ruff to format your code you could do:

        .. code-block::

            # To check the formatting
            register_managed_step(
                dwas.predefined.ruff(additional_arguments=["format", "--diff"]),
                name="ruff:format-check",
            )
            # To autoformat
            register_managed_step(
                dwas.predefined.ruff(additional_arguments=["format"]),
                name="ruff:format",
            )
    """
    return build_parameters(
        files=files, additional_arguments=additional_arguments
    )(Ruff())
