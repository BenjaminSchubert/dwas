import functools
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
