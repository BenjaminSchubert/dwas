from __future__ import annotations

import logging
from types import MappingProxyType, TracebackType
from typing import TYPE_CHECKING, Any, TextIO, cast

from colorama import Back, Fore, Style, init

from ._io import ANSI_ESCAPE_CODE_RE

if TYPE_CHECKING:
    from contextvars import ContextVar


class ColorFormatter(logging.Formatter):
    # We need to follow camel case style
    # ruff: noqa: N802

    COLOR_MAPPING = MappingProxyType(
        {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: "",
            logging.WARN: Fore.YELLOW,
            logging.ERROR: Fore.RED + Style.BRIGHT,
            logging.FATAL: Back.RED + Fore.WHITE + Style.BRIGHT,
        }
    )

    def formatMessage(self, record: logging.LogRecord) -> str:
        cast(Any, record).level_color = self.COLOR_MAPPING[record.levelno]
        return super().formatMessage(record)

    def formatException(
        self,
        ei: tuple[type[BaseException], BaseException, TracebackType | None]
        | tuple[None, None, None],
    ) -> str:
        output = super().formatException(ei)
        return f"{Fore.CYAN}\ndwas > " + "\ndwas > ".join(output.splitlines())


class NoColorFormatter(logging.Formatter):
    def formatMessage(self, record: logging.LogRecord) -> str:
        msg = super().formatMessage(record)
        return ANSI_ESCAPE_CODE_RE.sub("", msg)


class ContextStreamHandler(logging.StreamHandler):  # type: ignore[type-arg]
    _stream: ContextVar[TextIO]

    @property  # type: ignore[override]
    def stream(self) -> TextIO:
        return self._stream.get()

    @stream.setter
    def stream(self, value: ContextVar[TextIO]) -> None:
        self._stream = value


def setup_logging(
    level: int,
    tty_output: ContextVar[TextIO],
    log_file: ContextVar[TextIO],
    *,
    colors: bool,
) -> None:
    nocolor_formatter = NoColorFormatter(
        fmt="dwas > [%(levelname)s] %(message)s"
    )

    if colors:
        init(strip=False)
        stderr_formatter: logging.Formatter = ColorFormatter(
            fmt=(
                f"{Fore.CYAN}{Style.DIM}dwas >{Style.RESET_ALL}"
                f" %(level_color)s%(message)s{Style.RESET_ALL}"
            )
        )
    else:
        stderr_formatter = nocolor_formatter

    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    stderr_handler = ContextStreamHandler(tty_output)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(stderr_formatter)
    logger.addHandler(stderr_handler)

    logfile_handler = ContextStreamHandler(log_file)
    logfile_handler.setFormatter(nocolor_formatter)
    logger.addHandler(logfile_handler)
