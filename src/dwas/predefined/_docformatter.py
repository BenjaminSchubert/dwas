from __future__ import annotations

import logging
import subprocess
from typing import Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults

LOGGER = logging.getLogger(__name__)


@set_defaults(
    {
        "dependencies": ["docformatter"],
        "additional_arguments": ["--recursive", "--check", "--diff"],
        "files": ["."],
        "expected_status_codes": [0],
    }
)
class DocFormatter(Step):
    def __init__(self) -> None:
        self.__name__ = "docformatter"

    def __call__(
        self,
        step: StepRunner,
        files: Sequence[str],
        additional_arguments: Sequence[str],
        expected_status_codes: Sequence[int],
    ) -> None:
        try:
            step.run(["docformatter", *additional_arguments, *files])
        except subprocess.CalledProcessError as exc:
            if exc.returncode not in expected_status_codes:
                raise
            LOGGER.debug(
                "Ignoring error code %d from subprocess, as it is expected",
                exc.returncode,
            )


def docformatter(
    *,
    files: Sequence[str] | None = None,
    additional_arguments: list[str] | None = None,
    expected_status_codes: list[int] | None = None,
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
    :param expected_status_codes: Status codes that are acceptable from ``docformatter``.
                                  Defaults to :python:`[0]`. When formatting in
                                  place, you might want to set to :python:`[0, 3]`,
                                  as ``docformatter`` always returns 3 if a file
                                  was modified.
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
                    expected_status_codes=[0, 3],
                    run_by_default=False,
                    files=["src,", "tests", "dwasfile.py", "setup.py"],
                )
            )
    """
    return build_parameters(
        files=files,
        additional_arguments=additional_arguments,
        expected_status_codes=expected_status_codes,
    )(DocFormatter())
