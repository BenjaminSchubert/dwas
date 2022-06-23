from typing import List, Protocol, Tuple


class WriterProtocol(Protocol):
    def write(self, data: str) -> int:
        ...


class MemoryPipe:
    def __init__(self, writer: "PipePlexer") -> None:
        self._writer = writer

    def write(self, data: str) -> int:
        return self._writer.write(self, data)


class PipePlexer:
    def __init__(self) -> None:
        self.stderr = MemoryPipe(self)
        self.stdout = MemoryPipe(self)

        self._buffer: List[Tuple[MemoryPipe, str]] = []

    def write(self, stream: MemoryPipe, data: str) -> int:
        self._buffer.append((stream, data))
        return len(data)

    def dump(
        self, target_stdout: WriterProtocol, target_stderr: WriterProtocol
    ) -> None:
        for stream, line in self._buffer:
            if stream == self.stdout:
                target_stdout.write(line)
            else:
                target_stderr.write(line)
