import logging
from contextvars import ContextVar
from types import TracebackType
from typing import Any, Optional, TextIO, Tuple, Type, Union, cast

from colorama import Back, Fore, Style, init

from ._io import ANSI_ESCAPE_CODE_RE


class ColorFormatter(logging.Formatter):
    COLOR_MAPPING = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: "",
        logging.WARN: Fore.YELLOW,
        logging.ERROR: Fore.RED + Style.BRIGHT,
        logging.FATAL: Back.RED + Fore.WHITE + Style.BRIGHT,
    }

    def formatMessage(self, record: logging.LogRecord) -> str:
        cast(Any, record).level_color = self.COLOR_MAPPING[record.levelno]
        return super().formatMessage(record)

    def formatException(
        self,
        ei: Union[
            Tuple[Type[BaseException], BaseException, Optional[TracebackType]],
            Tuple[None, None, None],
        ],
    ) -> str:
        output = super().formatException(ei)
        output = f"{Fore.CYAN}\ndwas > " + "\ndwas > ".join(
            output.splitlines()
        )
        return output


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
    colors: bool,
    tty_output: ContextVar[TextIO],
    log_file: ContextVar[TextIO],
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
