import shutil
from contextlib import suppress
from pathlib import Path
from typing import Optional, Union

from .. import Step, StepRunner, build_parameters, set_defaults


@set_defaults(
    {
        "builder": "html",
        "sourcedir": ".",
        "output": None,
        "warning_as_error": False,
        "dependencies": ["sphinx"],
    }
)
class Sphinx(Step):
    def __init__(self) -> None:
        self.__name__ = "sphinx"

    def clean(self, output: Optional[Union[Path, str]]) -> None:
        if output is not None:
            with suppress(FileNotFoundError):
                shutil.rmtree(output)

    def __call__(
        self,
        step: StepRunner,
        builder: str,
        sourcedir: Union[Path, str],
        output: Optional[Union[Path, str]],
        warning_as_error: bool,
    ) -> None:
        if step.config.verbosity == -2:
            verbosity = ["-Q"]
        elif step.config.verbosity == -1:
            verbosity = ["-q"]
        elif step.config.verbosity > 0:
            verbosity = ["-v"] * step.config.verbosity
        else:
            verbosity = []

        if output is None:
            output = step.cache_path / builder

        command = [
            "sphinx-build",
            f"--{'' if step.config.colors else 'no-'}color",
            *verbosity,
            f"-b={builder}",
            f"-d={step.cache_path / 'doctrees'}",
            str(sourcedir),
            str(output),
        ]

        if warning_as_error:
            command.append("-W")

        step.run(command)


def sphinx(
    *,
    builder: Optional[str] = None,
    sourcedir: Optional[Union[Path, str]] = None,
    output: Optional[Union[Path, str]] = None,
    warning_as_error: Optional[bool] = None,
) -> Step:
    """
    Run `sphinx`_.

    By default, it will depend on :python:`["sphinx"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    :param builder: The sphinx builder to use.
                    Defaults to :python:`"html"`.
    :param sourcedir: The directory in which the ``conf.py`` resides.
                      Defaults to :python:`"."`.
    :param output: The directory in which to output the generated files.
                   If :python:`None`, will keep the data in the cache.
                   Defaults to :python:`None`.
    :param warning_as_error: Turn warnings into errors
                             Defaults to :python:`False`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        For running sphinx with a specific version of python, with your
        ``conf.py`` under ``docs/``, outputting the html files under
        ``_build/docs``:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.sphinx(sourcedir="docs", output="_build/docs"),
                python="3.8"
            )

        Or, to run doctests, linkchecks and build the output to ``_build/docs``,
        requiring the current package to be installed (see
        :py:func:`dwas.predefined.package`):

        .. code-block::

            register_managed_step(
                dwas.parametrize(
                    ("builder", "output"),
                    [
                        ("html", "_build/docs"),
                        # We don't care about the output of those two here.
                        ("linkcheck", None),
                        ("doctests", None),
                    ],
                    ids=["html", "linkcheck", "doctests"],
                )(dwas.predefined.sphinx()),
                requires=["package"],
            )
    """
    return build_parameters(
        builder=builder,
        sourcedir=sourcedir,
        output=output,
        warning_as_error=warning_as_error,
    )(Sphinx())
