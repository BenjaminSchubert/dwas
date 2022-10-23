from pathlib import Path
from typing import List, Optional, Union

from .. import (
    Step,
    StepRunner,
    build_parameters,
    register_managed_step,
    set_defaults,
)


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
    name: Optional[str] = None,
    builder: Optional[str] = None,
    sourcedir: Optional[Union[Path, str]] = None,
    output: Optional[Union[Path, str]] = None,
    warning_as_error: Optional[bool] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> Step:
    """
    Run `sphinx`_.

    :param name: The name to give to the step.
                 Defaults to :python:`"sphinx"`.
    :param builder: The sphinx builder to use.
                    Defaults to :python:`"html"`.
    :param sourcedir: The directory in which the ``conf.py`` resides.
                      Defaults to :python:`"."`.
    :param output: The directory in which to output the generated files.
                   If :python:`None`, will keep the data in the cache.
                   Defaults to :python:`None`.
    :param warning_as_error: Turn warnings into errors
                             Defaults to :python:`False`.
    :param python: The version of python to use.
                   Defaults to the version *dwas* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["pytest"]`.
    :param run_by_default: Whether to run this step by default or not.
                           If :python:`None`, will default to :python:`True`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        For running sphinx with a specific version of python, with your
        ``conf.py`` under ``docs/``, outputting the html files under
        ``_build/docs``:

        .. code-block::

            dwas.predefined.sphinx(
                sourcedir="docs", output="_build/docs", python="3.8"
            )

        Or, to run doctests, linkchecks and build the output to ``_build/docs``,
        requiring the current package to be installed (see
        :py:func:`dwas.predefined.package`):

        .. code-block::

            dwas.parametrize(
                ("builder", "output"),
                [
                    ("html", "_build/docs"),
                    # We don't care about the output of those two here.
                    ("linkcheck", None),
                    ("doctests", None),
                ],
                ids=["html", "linkcheck", "doctests"],
            )(dwas.predefined.sphinx(requires=["package"]))
    """
    sphinx_ = Sphinx()

    sphinx_ = build_parameters(
        builder=builder,
        sourcedir=sourcedir,
        output=output,
        warning_as_error=warning_as_error,
    )(sphinx_)

    return register_managed_step(
        sphinx_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
