import inspect
from typing import Any


def get_location(obj: Any) -> str:
    file = inspect.getsourcefile(obj)
    line = inspect.getsourcelines(obj)[-1]
    return f"{file}:{line}"
