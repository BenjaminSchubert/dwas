import logging
import os
import pty
import subprocess
import sys
from contextlib import suppress
from contextvars import ContextVar, copy_context
from threading import Thread
from typing import Dict, List

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


def run(
    command: List[str], env: Dict[str, str], *, silent_on_success: bool = False
) -> subprocess.CompletedProcess[None]:
    LOGGER.debug("Running command: '%s'", " ".join(command))

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
        ) as proc:
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
        ret.check_returncode()
        return ret

    if not silent_on_success:
        return _run()

    pipe_plexer = PipePlexer()

    def _run_in_context() -> subprocess.CompletedProcess[None]:
        set_subprocess_default_pipes(pipe_plexer.stdout, pipe_plexer.stderr)
        return _run()

    context = copy_context()

    try:
        return context.run(_run_in_context)
    except subprocess.CalledProcessError:
        pipe_plexer.dump(sys.stdout, sys.stderr)
        raise
