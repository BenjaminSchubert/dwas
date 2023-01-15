import functools
import logging
import sys
from contextvars import Context
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeVar, Union

import pytest
from _pytest.capture import FDCapture, MultiCapture

from dwas.__main__ import main
from dwas._subproc import set_subprocess_default_pipes
from tests import TESTS_PATH

_T = TypeVar("_T")


# TODO: this could be done via ParamSpec but it's only python3.10+
def isolated_context(func: Callable[..., _T]) -> Callable[..., _T]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> _T:
        context = Context()
        return context.run(func, *args, **kwargs)

    return wrapper


# TODO: this could be done via ParamSpec but it's only python3.10+
def isolated_logging(func: Callable[..., _T]) -> Callable[..., _T]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> _T:
        logger = logging.getLogger()
        old_handlers = logger.handlers
        logger.handlers = []

        try:
            return func(*args, **kwargs)
        finally:
            for handler in logger.handlers:
                # Simplified from `logging.shutdown`
                handler.acquire()
                handler.flush()
                handler.close()
                handler.release()

            logger.handlers = old_handlers

    return wrapper


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


def execute(args: List[str], expected_status: int = 0) -> Result:
    """
    Runs dwas in an isolated context and returns the result from the run.

    In most cases, you'll want to use the below `cli` instead, which
    will take care of building the cli correctly for you.
    """
    capture = MultiCapture(out=FDCapture(1), err=FDCapture(2), in_=None)
    capture.start_capturing()
    set_subprocess_default_pipes(sys.stdout, sys.stderr)

    exception = None
    # See https://github.com/python/typeshed/issues/8513#issue-1333671093
    exit_code: Union[str, int, None] = 0

    try:
        main(args)
    except SystemExit as exc:
        if exc.code != 0:
            exit_code = exc.code
            exception = exc
    finally:
        out, err = capture.readouterr()
        capture.stop_capturing()
        set_subprocess_default_pipes(sys.stdout, sys.stderr)
        print(out)
        print(err, file=sys.stderr)

    assert exit_code == expected_status
    return Result(exc=exception, stdout=out, stderr=err)


def cli(
    *,
    step: Optional[str] = None,
    cache_path: Path,
    colors: Optional[bool] = None,
    expected_status: int = 0,
) -> Result:
    args = ["--verbose"]

    if colors is None or colors:
        args.append("--color")
    else:
        args.append("--no-color")

    if step is not None:
        args.append(f"--step={step}")

    args.append(f"--cache-path={cache_path}")

    return execute(args, expected_status)
