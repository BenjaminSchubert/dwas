import io
import re
import sys
from contextlib import (
    ExitStack,
    contextmanager,
    redirect_stderr,
    redirect_stdout,
)
from contextvars import ContextVar
from pathlib import Path
from typing import Generator, Iterator, List, Optional, TextIO, Tuple

STDOUT = ContextVar[TextIO]("STDOUT")
STDERR = ContextVar[TextIO]("STDERR")
LOG_FILE = ContextVar[TextIO]("LOG_FILE")

ANSI_ESCAPE_CODE_RE = re.compile(r"\x1b\[\d+(;\d+)*m")


class NoOpWriter(io.TextIOWrapper):
    def __init__(self) -> None:
        pass

    def read(self, size: Optional[int] = None) -> str:
        raise io.UnsupportedOperation("Can't read from a noopwriter")

    def write(self, data: str) -> int:
        return len(data)

    def flush(self) -> None:
        pass


class MemoryPipe(io.TextIOWrapper):
    def __init__(
        self,
        writer: "PipePlexer",
    ) -> None:
        self._writer = writer

    def read(self, size: Optional[int] = None) -> str:
        raise io.UnsupportedOperation("can't read from a memorypipe")

    def write(self, data: str) -> int:
        return self._writer.write(self, data)

    def flush(self) -> None:
        pass


class PipePlexer:
    def __init__(self) -> None:
        self.stderr = MemoryPipe(self)
        self.stdout = MemoryPipe(self)

        self._buffer: List[Tuple[MemoryPipe, str]] = []

    def write(self, stream: MemoryPipe, data: str) -> int:
        self._buffer.append((stream, data))
        return len(data)

    def flush(self) -> None:
        for stream, line in self._buffer:
            if stream == self.stdout:
                sys.stdout.write(line)
            else:
                sys.stderr.write(line)


class StreamHandler(io.TextIOWrapper):
    def __init__(
        self, var: ContextVar[TextIO], log_var: ContextVar[TextIO]
    ) -> None:
        self._var = var
        self._log_var = log_var

    def read(self, size: Optional[int] = None) -> str:
        raise io.UnsupportedOperation("can't read from a memorypipe")

    def write(self, data: str) -> int:
        fd = self._log_var.get()
        # fast check to avoid the expensive regex
        if not isinstance(fd, NoOpWriter):
            fd.write(ANSI_ESCAPE_CODE_RE.sub("", data))
        return self._var.get().write(data)

    def flush(self) -> None:
        fd = self._log_var.get()
        # fast check to avoid the expensive regex
        if not isinstance(fd, NoOpWriter):
            fd.flush()
        self._var.get().flush()


@contextmanager
def instrument_streams() -> Generator[None, None, None]:
    STDOUT.set(sys.stdout)
    STDERR.set(sys.stderr)
    LOG_FILE.set(NoOpWriter())

    with redirect_stdout(StreamHandler(STDOUT, LOG_FILE)), redirect_stderr(
        StreamHandler(STDERR, LOG_FILE)
    ):
        yield


@contextmanager
def redirect_streams(stdout: TextIO, stderr: TextIO) -> Iterator[None]:
    stdout_token = STDOUT.set(stdout)
    stderr_token = STDERR.set(stderr)

    try:
        yield
    finally:
        STDOUT.reset(stdout_token)
        STDERR.reset(stderr_token)


@contextmanager
def log_file(path: Optional[Path]) -> Iterator[None]:
    with ExitStack() as stack:
        if path is None:
            fd: TextIO = NoOpWriter()
        else:
            fd = stack.enter_context(path.open("w"))

        token = LOG_FILE.set(fd)

        try:
            yield
        finally:
            LOG_FILE.reset(token)
