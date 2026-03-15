from __future__ import annotations

import logging
import shutil
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from ._exceptions import CommandNotFoundException, CommandNotInEnvironment

if TYPE_CHECKING:
    import os
    import subprocess

    from ._config import Config
    from ._subproc import ProcessManager


LOGGER = logging.getLogger(__name__)


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
        self._bin_path = self._path / "bin"
        self._config = config
        self._environ = environ
        self._proc_manager = proc_manager
        self._python_spec = python_spec
        self._uv = str(Path(sys.executable).parent.joinpath("uv"))

    @property
    def python(self) -> str:
        return str(self._bin_path / "python")

    def clean(self) -> None:
        with suppress(FileNotFoundError):
            shutil.rmtree(self._path)

    def prepare(self) -> None:
        if self._path.exists():
            LOGGER.debug("venv already exists. Reusing")
            return

        cmd = [
            self._uv,
            "venv",
            "--no-project",
            "--no-python-downloads",
            str(self._path),
        ]
        if self._python_spec is not None:
            cmd.append(f"--python={self._python_spec}")
        else:
            cmd.append(f"--python={sys.executable}")

        self._proc_manager.run(
            cmd,
            env=self._merge_env(self._config),
            silent_on_success=self._config.verbosity < 2,
        )

    def install(
        self,
        *packages: str,
        sync: bool = False,
        no_deps: bool = False,
        force_reinstall: bool = False,
    ) -> None:
        if sync:
            command = [
                self._uv,
                "sync",
                "--frozen",
                "--no-install-project",
                "--no-default-groups",
                "--active",
            ]
        else:
            command = [self._uv, "pip", "install"]

        if no_deps:
            command.append("--no-deps")
        if force_reinstall:
            command.append("--force-reinstall")

        command += packages
        self.run(
            command,
            silent_on_success=self._config.verbosity < 2,
            external_command=True,
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
                "PATH": f"{self._bin_path}:{env['PATH']}",
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

        command_in_venv = cmd.startswith(str(self._bin_path))

        if command_in_venv and external_command:
            LOGGER.warning(
                "The specified command %s is found in the virtual environment,"
                " but external_command=True",
                command,
            )
        if not external_command and not command_in_venv:
            raise CommandNotInEnvironment(command)
