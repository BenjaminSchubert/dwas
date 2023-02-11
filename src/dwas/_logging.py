import logging
import re
import sys
from types import TracebackType
from typing import Any, Optional, Tuple, Type, Union, cast

from colorama import Back, Fore, Style, init


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
    logger.addHandler(stderr_handler)
