from typing import List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults


@set_defaults(
    {
        "dependencies": ["docformatter"],
        "additional_arguments": ["--recursive", "--check", "--diff"],
        "files": ["."],
    }
)
class DocFormatter(Step):
    def __init__(self) -> None:
        self.__name__ = "docformatter"

    def __call__(
        self,
        step: StepRunner,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        step.run(["docformatter", *additional_arguments, *files])


def docformatter(
    *,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
) -> Step:
    """
    Run `docformatter`_ against your python source code.

    By default, it will depend on :python:`["docformatter"]`, when registered
    with :py:func:`dwas.register_managed_step`.

    :param files: The list of files or directories to run ``docformatter`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``docformatter``
                                 invocation.
                                 Defaults to :python:`["--recursive"]`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        In order to verify your code but not change it, for a step
        named **docformatter**:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.docformatter(files["src", "tests", "dwasfile.py", "setup.py"])
            )

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.docformatter(
                    # NOTE: this name is arbitrary, you could omit it, or specify
                    #       something else. We suffix in our documentation all
                    #       operations that will have destructive effect on the source
                    #       code by ``:fix``
                    name="docformatter:fix",
                    additional_arguments=["--in-place"],
                    run_by_default=False,
                    files=["src,", "tests", "dwasfile.py", "setup.py"],
                )
            )
    """
    return build_parameters(
        files=files,
        additional_arguments=additional_arguments,
    )(DocFormatter())
