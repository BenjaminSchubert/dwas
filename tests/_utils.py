import functools
import logging
import re
import sys
from contextlib import contextmanager
from contextvars import Context
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, List, Optional, TypeVar, Union

import pytest
from _pytest.capture import FDCapture, MultiCapture

from dwas.__main__ import main
from tests import TESTS_PATH

_T = TypeVar("_T")
ANSI_COLOR_CODES_RE = re.compile(r"\x1B\[\dm")


# TODO: this could be done via ParamSpec but it's only python3.10+
def isolated_context(func: Callable[..., _T]) -> Callable[..., _T]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> _T:
        context = Context()
        return context.run(func, *args, **kwargs)

    return wrapper


# TODO: this could be done via ParamSpec but it's only python3.10+
@contextmanager
def isolated_logging() -> Iterator[None]:
    logger = logging.getLogger()
    old_handlers = logger.handlers
    logger.handlers = []

    try:
        yield
    finally:
        for handler in logger.handlers:
            # Simplified from `logging.shutdown`
            handler.acquire()
            handler.flush()
            handler.close()
            handler.release()

        logger.handlers = old_handlers


def using_project(project: str) -> Callable[[_T], _T]:
    def wrapper(func):
        func = pytest.mark.project(TESTS_PATH / project)(func)
        func = pytest.mark.usefixtures("project")(func)
        return func

    return wrapper


@dataclass(frozen=True)
class Result:
    exc: Optional[SystemExit]
    stdout: str
    stderr: str


@isolated_context
def execute(args: List[str], expected_status: int = 0) -> Result:
    """
    Runs dwas in an isolated context and returns the result from the run.

    In most cases, you'll want to use the below `cli` instead, which
    will take care of building the cli correctly for you.
    """
    capture = MultiCapture(out=FDCapture(1), err=FDCapture(2), in_=None)
    capture.start_capturing()

    exception = None
    # See https://github.com/python/typeshed/issues/8513#issue-1333671093
    exit_code: Union[str, int, None] = 0

    try:
        with isolated_logging():
            main(args)
    except SystemExit as exc:
        if exc.code != 0:
            exit_code = exc.code
            exception = exc
    finally:
        out, err = capture.readouterr()
        capture.stop_capturing()

        print(out)
        print(err, file=sys.stderr)

    assert exit_code == expected_status
    return Result(exc=exception, stdout=out, stderr=err)


def cli(
    *,
    steps: Optional[List[str]] = None,
    cache_path: Path,
    colors: Optional[bool] = None,
    except_steps: Optional[List[str]] = None,
    expected_status: int = 0,
) -> Result:
    args = ["--verbose"]

    if colors is None or colors:
        args.append("--color")
    else:
        args.append("--no-color")

    if except_steps is not None:
        args.append(f"--except={','.join(except_steps)}")

    args.append(f"--cache-path={cache_path}")

    if steps is not None:
        args.extend(steps)

    return execute(args, expected_status)
