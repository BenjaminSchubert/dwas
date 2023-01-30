import inspect
from typing import Any, Callable


def get_location(obj: Any) -> str:
    try:
        file = inspect.getsourcefile(obj)
        line = inspect.getsourcelines(obj)[-1]
    except TypeError:
        file = inspect.getsourcefile(obj.__class__)
        line = inspect.getsourcelines(obj.__class__)[-1]
    return f"{file}:{line}"


def get_name(func: Callable[..., Any]) -> str:
    if inspect.isfunction(func):
        return func.__name__
    actual_func = getattr(func, "__call__")
    func_name = actual_func.__name__
    return f"{func.__class__.__name__}.{func_name}"
