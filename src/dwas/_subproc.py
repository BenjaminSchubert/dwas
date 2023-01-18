import logging
import os
import pty
import signal
import subprocess
import sys
import time
from contextlib import suppress
from contextvars import ContextVar, copy_context
from threading import Lock, Thread
from typing import Any, Dict, List, Set

from ._log_capture import PipePlexer, WriterProtocol

LOGGER = logging.getLogger(__name__)

_STDOUT_PIPE = ContextVar[WriterProtocol]("_STDOUT_PIPE", default=sys.stdout)
_STDERR_PIPE = ContextVar[WriterProtocol]("_STDERR_PIPE", default=sys.stderr)


def set_subprocess_default_pipes(
    stdout: WriterProtocol, stderr: WriterProtocol
) -> None:
    _STDOUT_PIPE.set(stdout)
    _STDERR_PIPE.set(stderr)


def _stream(source: int, dest: WriterProtocol) -> None:
    with suppress(IOError):
        while data := os.read(source, 2048):
            dest.write(data.decode())


class ProcessManager:
    def __init__(self) -> None:
        self.processes: Set[subprocess.Popen[Any]] = set()
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
        command: List[str],
        env: Dict[str, str],
        *,
        silent_on_success: bool = False,
    ) -> subprocess.CompletedProcess[None]:
        LOGGER.debug("Running command: '%s'", " ".join(command))
        if self._was_killed:
            # Prevent starting new jobs if the program has been interrupted
            raise KeyboardInterrupt()

        def _run() -> subprocess.CompletedProcess[None]:
            p_stdin, c_stdin = pty.openpty()
            p_stdout, c_stdout = pty.openpty()
            p_stderr, c_stderr = pty.openpty()

            with subprocess.Popen(
                command,
                env=env,
                text=True,
                stdin=c_stdin,
                stdout=c_stdout,
                stderr=c_stderr,
                close_fds=True,
                start_new_session=True,
            ) as proc:
                self._add(proc)

                for fd in [c_stdin, c_stdout, c_stderr]:
                    os.close(fd)

                stdout_reader = Thread(
                    target=_stream, args=[p_stdout, _STDOUT_PIPE.get()]
                )
                stderr_reader = Thread(
                    target=_stream, args=[p_stderr, _STDERR_PIPE.get()]
                )

                stdout_reader.start()
                stderr_reader.start()

                stdout_reader.join()
                stderr_reader.join()

            for fd in [p_stdin, p_stdout, p_stderr]:
                os.close(fd)

            ret = subprocess.CompletedProcess[None](command, proc.returncode)
            self._remove(proc)
            ret.check_returncode()
            return ret

        if not silent_on_success:
            return _run()

        pipe_plexer = PipePlexer()

        def _run_in_context() -> subprocess.CompletedProcess[None]:
            set_subprocess_default_pipes(
                pipe_plexer.stdout, pipe_plexer.stderr
            )
            return _run()

        context = copy_context()

        try:
            return context.run(_run_in_context)
        except subprocess.CalledProcessError:
            pipe_plexer.dump(sys.stdout, sys.stderr)
            raise

    def _add(self, proc: subprocess.Popen[Any]) -> None:
        with self._lock:
            self.processes.add(proc)

    def _remove(self, proc: subprocess.Popen[Any]) -> None:
        with self._lock:
            self.processes.remove(proc)
