import inspect
import logging
from typing import Any, Callable, Dict, TypeVar

from ._exceptions import BaseDwasException
from ._inspect import get_location

LOGGER = logging.getLogger(__name__)
T = TypeVar("T")


def call_with_parameters(
    func: Callable[..., T], parameters: Dict[str, Any]
) -> T:
    signature = inspect.signature(func)
    kwargs = {}

    for name, value in signature.parameters.items():
        if value.kind not in [value.POSITIONAL_OR_KEYWORD, value.KEYWORD_ONLY]:
            raise BaseDwasException(
                f"Unsupported parameter type for function '{func.__name__}'"
                f" defined in {get_location(func)}. Steps currently only support"
                " positional_or_keyword or keyword_only parameters."
            )

        try:
            kwargs[name] = parameters[name]
        except KeyError as exc:
            if value.default != value.empty:
                LOGGER.debug(
                    "No parameter specified for argument %s of %s. Using default",
                    value.name,
                    func.__name__,
                )
                continue

            actual_func = getattr(func, "__call__", func)
            func_name = actual_func.__name__
            if actual_func != func:
                func_name = f"{func.__name__}.{func_name}"

            file = inspect.getsourcefile(actual_func)
            line = inspect.getsourcelines(actual_func)[-1]
            raise BaseDwasException(
                f"Parameter '{name}' was not provided for function"
                f" '{func_name}' defined in {file}:{line}"
            ) from exc

    return func(**kwargs)
