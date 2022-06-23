import logging
import multiprocessing
import os
import random
import sys
from pathlib import Path
from typing import Optional

from ._exceptions import BaseDwasException

LOGGER = logging.getLogger(__name__)


# This is a config class, it's easier to have everything there...
# pylint: disable=too-many-instance-attributes
class Config:
    def __init__(
        self,
        user_config: str,
        cache_path: str,
        verbosity: int,
        colors: bool,
        n_jobs: int,
        skip_missing_interpreters: bool,
        skip_setup: bool,
        skip_run: bool,
        fail_fast: bool,
    ) -> None:
        self.user_config = user_config
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
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "NO_PROXY",
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

        return sys.stdin.isatty()
