import functools
import logging
from contextvars import Context
from typing import Any, Callable, TypeVar

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
