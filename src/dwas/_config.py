import logging
import multiprocessing
import os
import random
import sys
from pathlib import Path
from typing import Dict, Optional

from ._exceptions import BaseDwasException

LOGGER = logging.getLogger(__name__)


# This is a config class, it's easier to have everything there...
# pylint: disable=too-many-instance-attributes
class Config:
    """
    Holds the global configuration for ``dwas``.

    This contains a lot of the configuration that can be set from the
    command line and can be access in each step to configure their
    behavior.
    """

    cache_path: Path
    """
    The path to the root of the cache directory used by dwas.

    Note that in most cases, you can use the step-specific cache at
    :py:attr:`StepRunner.cache_path` and expose data via
    :py:func:`StepWithArtifacts.gather_artifacts`.
    """

    colors: bool
    """
    Whether to use colored output or not for the output.

    Determining whether color output is available is not trivial and many
    programs do it differently.

    Here is how `dwas` does it:

    - The cli supports --color|--no-color to force the value
    - Then, it will look for ``PY_COLORS`` and enable colors if this is ``"1"``,
      and disable if it is ``"0"``. Any other option will abort the program.
    - Then, it will look if ``NO_COLORS`` is set. If so, it will disable colors.
    - Then, it will look if ``FORCE_COLOR`` is set. If so, it will enable colors.
    - Then, it will detect if this is running in various CIs (currently
      `github actions`_ is supported.) and enable colors if they support it.
    - Finally, it will look if this is attached to a tty and enable colors if so.
    """

    environ: Dict[str, str]
    """
    The environment to use when running commands.

    This environment is on purpose minimal, and will only let pass values like

        - proxies: ``http_proxy``, ``https_proxy``, ``no_proxy``
        - ca certificates variables: ``URL_CA_BUNDLE``, ``REQUEST_CA_BUNDLE``, ``SSL_CERT_FILE``
        - language: ``LANG``, ``LANGUAGE``
        - pip: ``PIP_INDEX_URL``, ``PIP_EXTRA_INDEX_URL``
        - python: ``PYTHONHASHSEED``
        - system: ``PATH``, ``LD_LIBRARY_PATH``, ``TMPDIR``

    If will also forcefully set ``PY_COLORS`` and ``NO_COLOR`` based on the
    configuration. See :py:attr:`Config.colors`.

    If ``PYTHONHASHSEED`` is not passed when calling `dwas`, this will set it
    to a random value and log it to allow repeating the current run.
    """

    fail_fast: bool
    """
    Whether to stop enqueuing more jobs after the first failure or not.
    """

    n_jobs: int
    """
    The number of jobs to run in parallel.

    0 will use the number of cpus on the machine as given by
    :py:func:`multiprocessing.cpu_count`.
    """

    skip_missing_interpreters: bool
    """
    Whether to skip when an interpreter is not found, or fail.
    """

    skip_run: bool
    """
    Whether to skip the run part of each step.

    This is the reverse of :py:attr:`skip_setup`, and only runs the
    setup part.
    """

    skip_setup: bool
    """
    Whether to skip the setup phase of each step.
    """

    venvs_path: Path
    """
    The path to where the virtual environments are stored.
    """

    verbosity: int
    """
    The verbosity level to use.

    0 means an equal number of verbose and quiet flags have been passed
    positive means more verbose, and thus, negative less.
    """

    def __init__(
        self,
        cache_path: str,
        verbosity: int,
        colors: Optional[bool],
        n_jobs: int,
        skip_missing_interpreters: bool,
        skip_setup: bool,
        skip_run: bool,
        fail_fast: bool,
    ) -> None:
        self.cache_path = Path(cache_path).resolve()
        self.venvs_path = self.cache_path / "venvs"

        self.verbosity = verbosity
        self.skip_missing_interpreters = skip_missing_interpreters

        self.skip_setup = skip_setup
        self.skip_run = skip_run

        self.fail_fast = fail_fast

        if n_jobs == 0:
            n_jobs = multiprocessing.cpu_count()
        self.n_jobs = n_jobs

        self.environ = {
            # XXX: keep this list in sync with the above documentation
            key: os.environ[key]
            for key in [
                "URL_CA_BUNDLE",
                "PATH",
                "LANG",
                "LANGUAGE",
                "LD_LIBRARY_PATH",
                "PIP_INDEX_URL",
                "PIP_EXTRA_INDEX_URL",
                "PYTHONHASHSEED",
                "REQUESTS_CA_BUNDLE",
                "SSL_CERT_FILE",
                "http_proxy",
                "https_proxy",
                "no_proxy",
                "TMPDIR",
            ]
            if key in os.environ
        }

        if "PYTHONHASHSEED" in self.environ:
            LOGGER.info(
                "Using provided PYTHONHASHSEED=%s",
                self.environ["PYTHONHASHSEED"],
            )
        else:
            self.environ["PYTHONHASHSEED"] = str(random.randint(1, 4294967295))
            LOGGER.info(
                "Setting PYTHONHASHSEED=%s", self.environ["PYTHONHASHSEED"]
            )

        self.colors = self._get_color_setting(colors)
        if self.colors:
            self.environ["PY_COLORS"] = "1"
            self.environ["FORCE_COLOR"] = "1"
        else:
            self.environ["PY_COLORS"] = "0"
            self.environ["NO_COLOR"] = "0"

    def _get_color_setting(self, colors: Optional[bool]) -> bool:
        # pylint: disable=too-many-return-statements
        if colors is not None:
            return colors

        env_colors = os.environ.get("PY_COLORS", None)
        if env_colors == "1":
            return True
        if env_colors == "0":
            return False
        if env_colors is not None:
            raise BaseDwasException(
                f"PY_COLORS set to {env_colors}. This is invalid,"
                " only '1' or '0' is supported.",
            )

        env_colors = os.environ.get("NO_COLOR", None)
        if env_colors is not None:
            return False

        env_colors = os.environ.get("FORCE_COLOR", None)
        if env_colors is not None:
            return True

        # Check for CIs that were asked for, and enable colors by default
        # when it's possible. Do this towards the end to ensure other config
        # can override
        if "GITHUB_ACTION" in os.environ:
            return True

        return sys.stdin.isatty()
