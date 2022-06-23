import itertools
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from .._exceptions import BaseDwasException

T = TypeVar("T", bound=Callable[..., Any])

_DEFAULTS = "_dwas_defaults"
_PARAMETERS = "_dwas_parameters"


class ParameterConflictException(BaseDwasException):
    def __init__(self, parameter: str, func: Callable[..., None]) -> None:
        super().__init__(
            f"A conflict was detected while parametrizing '{func.__name__}'."
            f" '{parameter}' was already specified previously"
        )


class DefaultsAlreadySetException(BaseDwasException):
    def __init__(self, func: Callable[..., None]) -> None:
        super().__init__(
            f"Defaults have already been set for '{func.__name__}'."
        )


class Parameter:
    def __init__(self, id_: Optional[str], parameters: Dict[str, Any]) -> None:
        self._parameters = parameters
        if id_ is None:
            id_ = ",".join(str(v) for v in parameters.values())
        self.id = id_

    def as_dict(self) -> Dict[str, Any]:
        return self._parameters.copy()

    # pylint: disable=protected-access
    @classmethod
    def merge(cls, param1: "Parameter", param2: "Parameter") -> "Parameter":
        if param1.id == "":
            id_ = param2.id
        elif param2.id == "":
            id_ = param1.id
        else:
            id_ = ",".join([param1.id, param2.id])

        for key in param2._parameters.keys():
            if key in param1._parameters:
                raise ValueError(key)

        joined_parameters = param1._parameters.copy()
        joined_parameters.update(param2._parameters)

        return cls(id_, joined_parameters)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id and self._parameters == other._parameters

    def __repr__(self) -> str:
        return f"Parameter<{self.id}>({self.as_dict()})"


@overload
def parametrize(
    arg_names: str,
    args_values: Sequence[Any],
    ids: Optional[Sequence[Optional[str]]] = None,
) -> Callable[[T], T]:
    ...


@overload
def parametrize(
    arg_names: Sequence[str],
    args_values: Sequence[Sequence[Any]],
    ids: Optional[Sequence[Optional[str]]] = None,
) -> Callable[[T], T]:
    ...


def parametrize(
    arg_names: Union[str, Sequence[str]],
    args_values: Union[Sequence[Any], Sequence[Sequence[Any]]],
    ids: Optional[Sequence[Optional[str]]] = None,
) -> Callable[[T], T]:
    def _apply(func: T) -> T:
        nonlocal arg_names, args_values, ids

        if isinstance(arg_names, str):
            arg_names = [arg_names]
            args_values = [[value] for value in args_values]

        if ids is not None:
            if len(args_values) != len(ids):
                raise BaseDwasException(
                    f"Error parametrizing: {len(args_values)} values were"
                    f" passed, but only {len(ids)} ids were given."
                )
        else:
            ids = [None] * len(args_values)

        current_parameters = [
            Parameter(id, dict(zip(arg_names, args_values)))
            for id, args_values in zip(ids, args_values)
        ]

        old_parameters = getattr(func, _PARAMETERS, [])
        if old_parameters:
            try:
                current_parameters = [
                    Parameter.merge(param1, param2)
                    for param1, param2 in itertools.product(
                        current_parameters, old_parameters
                    )
                ]
            except ValueError as exc:
                raise ParameterConflictException(exc.args[0], func) from exc

        setattr(func, _PARAMETERS, current_parameters)
        return func

    return _apply


def set_defaults(values: Dict[str, Any]) -> Callable[[T], T]:
    def _apply(func: T) -> T:
        if hasattr(func, _DEFAULTS):
            raise DefaultsAlreadySetException(func)

        setattr(func, _DEFAULTS, values)
        return func

    return _apply


def extract_parameters(
    func: Callable[..., Any]
) -> List[Tuple[str, Dict[str, Any]]]:
    defaults = getattr(func, _DEFAULTS, {})

    def _merge(parameter: Parameter) -> Dict[str, Any]:
        params = defaults.copy()
        params.update(parameter.as_dict())
        return params

    return [
        (param.id, _merge(param))
        for param in getattr(func, _PARAMETERS, [Parameter("", {})])
    ]
