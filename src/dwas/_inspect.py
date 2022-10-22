import inspect
from typing import Any


def get_location(obj: Any) -> str:
    try:
        file = inspect.getsourcefile(obj)
        line = inspect.getsourcelines(obj)[-1]
    except TypeError:
        file = inspect.getsourcefile(obj.__class__)
        line = inspect.getsourcelines(obj.__class__)[-1]
    return f"{file}:{line}"
