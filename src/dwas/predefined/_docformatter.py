from typing import List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import (
    Step,
    StepHandler,
    build_parameters,
    register_managed_step,
    set_defaults,
)


@set_defaults(
    {
        "dependencies": ["docformatter"],
        # FIXME: --check does not show the diff on stdout which means it will
        #        just fail without information.
        #        https://github.com/PyCQA/docformatter/issues/125
        #
        "additional_arguments": ["--recursive", "--check"],
        "files": ["."],
    }
)
class DocFormatter(Step):
    def __init__(self) -> None:
        self.__name__ = "docformatter"

    def __call__(
        self,
        step: StepHandler,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        step.run(["docformatter", *additional_arguments, *files])


def docformatter(
    *,
    name: Optional[str] = None,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    dependencies: Optional[List[str]] = None,
) -> Step:
    """
    Run `docformatter`_ against your python source code.

    :param name: The name to give to the step.
                 Defaults to :python:`"docformatter"`.
    :param files: The list of files or directories to run ``docformatter`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``docformatter``
                                 invocation.
                                 Defaults to :python:`["--recursive"]`.
    :param python: The version of python to use.
                   Defaults to the version *dwas* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["docformatter"]`.
    :param run_by_default: Whether to run this step by default or not.
                           Defaults to :python:`True`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        In order to verify your code but not change it, for a step
        named **docformatter**:

        .. code-block::

            dwas.predefined.docformatter(files["src", "tests", "dwasfile.py", "setup.py"])

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            dwas.predefined.docformatter(
                # Note: this name is arbitrary, you could omit it, or specify
                #       something else. We suffix in our documentation all
                #       operations that will have destructive effect on the source
                #       code by ``:fix``
                name="docformatter:fix",
                additional_arguments=["--in-place"],
                run_by_default=False,
                files=["src,", "tests", "dwasfile.py", "setup.py"],
            )
    """
    docformatter_ = DocFormatter()

    docformatter_ = build_parameters(
        files=files,
        additional_arguments=additional_arguments,
    )(docformatter_)

    return register_managed_step(
        docformatter_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
