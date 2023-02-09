import logging
import re
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from types import TracebackType
from typing import Any, Generator, Optional, Tuple, Type, Union, cast

from colorama import Back, Fore, Style, init

from ._log_capture import WriterProtocol

_StderrHandler = ContextVar[logging.Handler]("_StderrHandler")


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
    ESCAPE_CODE = re.compile(r"\x1b\[\d+m")

    def formatMessage(self, record: logging.LogRecord) -> str:
        msg = super().formatMessage(record)
        return self.ESCAPE_CODE.sub("", msg)


class ContextBasedHandler(logging.Handler):
    def __init__(
        self, var: ContextVar[logging.Handler], level: int = logging.NOTSET
    ) -> None:
        super().__init__(level)
        self._var = var

    def emit(self, record: logging.LogRecord) -> None:
        self._var.get().emit(record)


def setup_logging(level: int, colors: bool) -> None:
    if colors:
        init(strip=False)
        formatter: logging.Formatter = ColorFormatter(
            fmt=(
                f"{Fore.CYAN}{Style.DIM}dwas >{Style.RESET_ALL}"
                f" %(level_color)s%(message)s{Style.RESET_ALL}"
            )
        )
    else:
        formatter = NoColorFormatter(fmt="dwas > [%(levelname)s] %(message)s")

    logger = logging.getLogger()
    logger.setLevel(level)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    _StderrHandler.set(stderr_handler)

    logger.addHandler(ContextBasedHandler(_StderrHandler))


@contextmanager
def context_handler(output: WriterProtocol) -> Generator[None, None, None]:
    previous = _StderrHandler.get()

    new_handler = logging.StreamHandler(output)
    new_handler.setFormatter(previous.formatter)
    token = _StderrHandler.set(new_handler)

    try:
        yield
    finally:
        new_handler.flush()
        new_handler.close()
        _StderrHandler.reset(token)
