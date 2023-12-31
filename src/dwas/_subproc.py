from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from contextlib import suppress
from contextvars import copy_context
from threading import Lock, Thread
from typing import Any, TextIO

from . import _io

LOGGER = logging.getLogger(__name__)


def _stream(source: int, dest: TextIO) -> None:
    with suppress(IOError):
        while data := os.read(source, 4096):
            dest.write(data.decode())


class ProcessManager:
    def __init__(self) -> None:
        self.processes: set[subprocess.Popen[Any]] = set()
        self._lock = Lock()

        self._was_killed = False

    def kill(self) -> None:
        self._was_killed = True

        with self._lock:
            LOGGER.debug("Stopping %s processes", len(self.processes))
            for proc in list(self.processes):
                try:
                    pgrp = os.getpgid(proc.pid)
                except ProcessLookupError:
                    # Process is dead, we are good
                    self.processes.remove(proc)
                    continue

                os.killpg(pgrp, signal.SIGTERM)

            # wait a maximum of 5 seconds for processes to quit
            total_wait_time = 5.0

            for proc in self.processes:
                start = time.monotonic()

                try:
                    proc.wait(total_wait_time)
                except subprocess.TimeoutExpired:
                    break
                total_wait_time -= time.monotonic() - start
            else:
                return  # All subprocesses exited

            LOGGER.warning(
                "Some processes took too long to finish, killing them."
            )
            for proc in self.processes:
                try:
                    pgrp = os.getpgid(proc.pid)
                except ProcessLookupError:
                    # Process is dead, we are good
                    continue

                os.killpg(pgrp, signal.SIGKILL)

    def run(
        self,
        command: list[str],
        env: dict[str, str],
        cwd: str | bytes | os.PathLike[str] | os.PathLike[bytes] | None = None,
        *,
        silent_on_success: bool = False,
    ) -> subprocess.CompletedProcess[None]:
        LOGGER.debug("Running command: '%s'", " ".join(command))
        if self._was_killed:
            # Prevent starting new jobs if the program has been interrupted
            raise KeyboardInterrupt()

        def _run() -> subprocess.CompletedProcess[None]:
            with subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                start_new_session=True,
            ) as proc:
                self._add(proc)

                assert proc.stdout is not None
                assert proc.stderr is not None

                stdout_reader = Thread(
                    target=copy_context().run,
                    args=[_stream, proc.stdout.fileno(), sys.stdout],
                )
                stderr_reader = Thread(
                    target=copy_context().run,
                    args=[_stream, proc.stderr.fileno(), sys.stderr],
                )

                stdout_reader.start()
                stderr_reader.start()

                stdout_reader.join()
                stderr_reader.join()

            ret: subprocess.CompletedProcess[
                None
            ] = subprocess.CompletedProcess(command, proc.returncode)
            self._remove(proc)
            ret.check_returncode()
            return ret

        if not silent_on_success:
            return _run()

        pipe_plexer = _io.PipePlexer()

        def _run_in_context() -> subprocess.CompletedProcess[None]:
            with _io.redirect_streams(pipe_plexer.stdout, pipe_plexer.stderr):
                return _run()

        context = copy_context()

        try:
            return context.run(_run_in_context)
        except subprocess.CalledProcessError:
            pipe_plexer.flush()
            raise

    def _add(self, proc: subprocess.Popen[Any]) -> None:
        with self._lock:
            self.processes.add(proc)

    def _remove(self, proc: subprocess.Popen[Any]) -> None:
        with self._lock:
            self.processes.remove(proc)
