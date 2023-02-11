import io
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from contextvars import ContextVar
from typing import Generator, Iterator, List, Optional, TextIO, Tuple

_STDOUT = ContextVar[TextIO]("_STDOUT")
_STDERR = ContextVar[TextIO]("_STDERR")


class MemoryPipe(io.TextIOWrapper):
    def __init__(self, writer: "PipePlexer") -> None:
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
        self,
        var: ContextVar[TextIO],
    ) -> None:
        self._var = var

    def read(self, size: Optional[int] = None) -> str:
        raise io.UnsupportedOperation("can't read from a memorypipe")

    def write(self, data: str) -> int:
        return self._var.get().write(data)

    def flush(self) -> None:
        self._var.get().flush()


@contextmanager
def instrument_streams() -> Generator[None, None, None]:
    _STDOUT.set(sys.stdout)
    _STDERR.set(sys.stderr)

    with redirect_stdout(StreamHandler(_STDOUT)), redirect_stderr(
        StreamHandler(_STDERR)
    ):
        yield


@contextmanager
def redirect_streams(stdout: TextIO, stderr: TextIO) -> Iterator[None]:
    stdout_token = _STDOUT.set(stdout)
    stderr_token = _STDERR.set(stderr)

    try:
        yield
    finally:
        _STDOUT.reset(stdout_token)
        _STDERR.reset(stderr_token)
