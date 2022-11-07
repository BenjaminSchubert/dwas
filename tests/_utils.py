import functools
import logging
from contextvars import Context
from typing import Any, Callable, TypeVar

import pytest

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
