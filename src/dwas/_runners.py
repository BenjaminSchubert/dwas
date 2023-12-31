from __future__ import annotations

import logging
import os
import shutil
import sys
from contextlib import suppress
from typing import TYPE_CHECKING, cast

from virtualenv import session_via_cli

from . import _io
from ._exceptions import (
    CommandNotFoundException,
    CommandNotInEnvironment,
    UnavailableInterpreterException,
)

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

    from virtualenv.run.session import Session

    from ._config import Config
    from ._subproc import ProcessManager


LOGGER = logging.getLogger(__name__)


class _VirtualenvInstaller:
    def __init__(self, path: Path, python_spec: str | None) -> None:
        self.environ = os.environ.copy()
        self.environ["VIRTUALENV_CLEAR"] = "False"
        if python_spec is not None:
            self.environ["VIRTUALENV_PYTHON"] = python_spec

        self._python_spec = python_spec
        self._path = path

        self._session_cache = None

    @property
    def python(self) -> str:
        return str(self._session.creator.exe)

    @property
    def paths(self) -> list[str]:
        creator = self._session.creator
        if creator.bin_dir == creator.script_dir:
            return [str(creator.bin_dir)]
        return [str(creator.bin_dir), str(creator.script_dir)]

    def resolve(self) -> None:
        if self._session_cache is not None:
            return

        plexer = _io.PipePlexer()

        try:
            with _io.redirect_streams(plexer.stdout, plexer.stdout):
                session = session_via_cli(
                    [str(self._path)], setup_logging=False, env=self.environ
                )
        except RuntimeError as exc:
            raise UnavailableInterpreterException(
                cast(str, self._python_spec)
            ) from exc

        self._session_cache = session

    @property
    def _session(self) -> Session:
        if self._session_cache is None:
            self.resolve()
        return self._session_cache


class VenvRunner:
    def __init__(
        self,
        name: str,
        python_spec: str | None,
        config: Config,
        environ: dict[str, str],
        proc_manager: ProcessManager,
    ) -> None:
        self._path = (config.venvs_path / name.replace(":", "-")).resolve()
        self._config = config
        self._environ = environ
        self._proc_manager = proc_manager

        self._installer = _VirtualenvInstaller(self._path, python_spec)

    @property
    def python(self) -> str:
        return self._installer.python

    def clean(self) -> None:
        with suppress(FileNotFoundError):
            shutil.rmtree(self._path)

    def prepare(self) -> None:
        if self._path.exists():
            LOGGER.debug("venv already exists. Reusing")
            return

        self._installer.resolve()

        self._proc_manager.run(
            [sys.executable, "-m", "virtualenv", str(self._path)],
            env=self._installer.environ,
            silent_on_success=self._config.verbosity < 2,
        )

    def install(self, *packages: str) -> None:
        self.run(
            [self.python, "-m", "pip", "install", *packages],
            silent_on_success=self._config.verbosity < 2,
        )

    def run(
        self,
        command: list[str],
        cwd: str | bytes | os.PathLike[str] | os.PathLike[bytes] | None = None,
        env: dict[str, str] | None = None,
        *,
        external_command: bool = False,
        silent_on_success: bool = False,
    ) -> subprocess.CompletedProcess[None]:
        env = self._merge_env(self._config, env)
        self._validate_command(
            command[0], env, external_command=external_command
        )

        return self._proc_manager.run(
            command,
            cwd=cwd,
            env=env,
            silent_on_success=silent_on_success,
        )

    def _merge_env(
        self, config: Config, additional_env: dict[str, str] | None = None
    ) -> dict[str, str]:
        env = config.environ.copy()
        env.update(self._environ)
        env.update(
            {
                "VIRTUAL_ENV": str(self._path),
                "PATH": f"{':'.join(self._installer.paths)}:{env['PATH']}",
            }
        )
        if additional_env is not None:
            env.update(additional_env)
        return env

    def _validate_command(
        self, command: str, env: dict[str, str], *, external_command: bool
    ) -> None:
        cmd = shutil.which(command, path=env["PATH"])

        if cmd is None:
            raise CommandNotFoundException(command, path=env["PATH"])

        command_in_venv = any(
            cmd.startswith(path) for path in self._installer.paths
        )

        if command_in_venv and external_command:
            LOGGER.warning(
                "The specified command %s is found in the virtual environment,"
                " but external_command=True",
                command[0],
            )
        if not external_command and not command_in_venv:
            raise CommandNotInEnvironment(command)
