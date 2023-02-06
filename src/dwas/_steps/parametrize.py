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

_DEFAULTS = "__dwas_defaults__"
_PARAMETERS = "__dwas_parameters__"


class ParameterConflictException(BaseDwasException):
    """
    Exception raised when values were passed multiple times for the same parameter.
    """

    def __init__(self, parameter: str, func: Callable[..., None]) -> None:
        super().__init__(
            f"A conflict was detected while parametrizing '{func.__name__}'."
            f" '{parameter}' was already specified previously"
        )


class DefaultsAlreadySetException(BaseDwasException):
    """
    Exception raised when :py:func:`set_defaults` has already been called on an object.
    """

    def __init__(self, func: Callable[..., None]) -> None:
        super().__init__(
            f"Defaults have already been set for '{func.__name__}'."
        )


class MismatchedNumberOfParametersException(BaseDwasException):
    """
    Exception raised when the number of parameters does not match the number of ids.
    """

    def __init__(self, n_args_values: int, n_args_ids: int) -> None:
        super().__init__(
            f"Error parametrizing: {n_args_values} values were passed, but"
            f" {n_args_ids} ids were given. Those two must match"
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
    """
    Parametrize the decorated :term:`step` with the provided values.

    Parametrization allows running a specific step with multiple configurations.
    For example, you might want to run a ``pytest`` step against both python3.10
    and python3.11. With parametrization you do not need to repeat the step.

    It is possible to make multiple calls to parametrize on the same step, as
    long as the parameter names do not conflict. In which case, the *product* of
    both parametrization steps will be generated.

    .. note::

        Parameters, once set for a specific argument cannot be overridden. If
        you want to provide default values, see :py:func:`set_defaults`.

    :param arg_names: The name of the argument to parametrize. Or a list of
                      names if multiple values need to be passed.
    :param args_values: A list of values to be used for the given argument. When
                       parametrizing multiple arguments at once, this becomes a
                       list of list of argument values.
    :param ids: A list of ids for each entry in arg_values.

        If not provided, it will be either:

            - "", if only one value was passed for the parametrization
            - built based on the string representation of the values, in order.

    :return: A decorator that can be applied to a step to apply the parametrization.
    :raise MismatchedNumberOfParametersException: if the number of ids and the
                                                  number of arg_values do not
                                                  match.
    :raise ParameterConflictException: if values have already been provided for
                                       a specific argument (e.g. by another
                                       parametrize call)

    :Examples:

    You might want to parametrize a single argument. In which case you can do:

    .. code-block::

        # The step needs to be applied after parametrization
        @step()
        # This step needs to run for both python 3.10 and python3.11
        @parametrize("python", ["3.10", "3.11"])
        def print_python_version(step: StepRunner) -> None:
            step.execute([self.python, "--version"])

    Or you might want to parametrize multiple arguments at once. In that case
    you can do:

    .. code-block::

        # The step needs to be applied after parametrization.
        # Note that we don't supply the usual 'dependencies' argument here, it
        # will be handled by parametrization.
        @managed_step()
        # This needs to run with:
        #   - python 3.10 against django 3.0 and 4.0
        #   - python3.11 against django 4.0
        @parametrize(
            ["python", "dependencies"],
            [
                ["3.10", ["django==3.0"]],
                ["3.10", ["django==4.0"]],
                ["3.11", ["django==4.0"]],
            ],
        )
        def test(step: StepRunner) -> None:
            step.run([self.python, "manage.py", "test"])

    And finally, you can also combine multiple parametrize calls:

    .. code-block::

        # The step needs to be applied after parametrization again.
        # Note that we don't supply the usual 'dependencies' argument here, it
        # will be handled by parametrization.
        @managed_step()
        # This needs to run with:
        #   - python3.10 and 3.11
        #   - both against django 3.0 and 4.0
        @parametrize("python", ["3.10", "3.11"])
        @parametrize("dependencies", [["django==3.0"], ["django==4.0"]])
        def test(step: StepRunner) -> None:
            step.run([self.python, "manage.py", "test"])
    """

    def _apply(func: T) -> T:
        nonlocal arg_names, args_values, ids

        if isinstance(arg_names, str):
            arg_names = [arg_names]
            args_values = [[value] for value in args_values]

        if ids is not None:
            if len(args_values) != len(ids):
                raise MismatchedNumberOfParametersException(
                    len(args_values), len(ids)
                )
        elif len(args_values) == 1:
            ids = [""]
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
    """
    Set default values for parameters on the given :term:`step`.

    Those values can be overridden by using :py:func:`parametrize`.

    Only a single call to :py:func:`set_defaults` can be made for a given
    object, trying to set it multiple times will raise a
    :py:exc:`DefaultsAlreadySetException`.

    .. seealso::

        :py:func:`parametrize` for an explanation of how parameters work.

    :param values: A dictionary of default values to set on the step
    :return: A decorator that can be applied to a step to apply the parametrization.
    :raise DefaultsAlreadySetException: If :py:func:`set_defaults` was already
                                        called on the given object.
    """

    # FIXME: allow merging defaults instead of failing if they do not conflict
    def _apply(func: T) -> T:
        if hasattr(func, _DEFAULTS):
            raise DefaultsAlreadySetException(func)

        setattr(func, _DEFAULTS, values)
        return func

    return _apply


def build_parameters(**kwargs: Any) -> Callable[[T], T]:
    """
    Generate a :py:func:`parametrize` call based on the provided parameters.

    This is a shortcut to build a single :py:func:`parametrize` call, for all
    non-:python:`None` values that are passed in.

    It will only pass the arguments as a single entry, so this will only ever
    generate a single entry.

    This is basically a shortcut for:

    .. code-block::

        for key, value in parameters.items():
            if value is not None:
                func = parametrize(key, [value])(func)

    :param kwargs: Any key/value pair to pass as a parametrize argument
    :return: A function to apply the parameters on the given step.
    """
    names = []
    values = []

    for key, value in kwargs.items():
        if value is not None:
            names.append(key)
            values.append(value)

    if names:
        return parametrize(names, [values])

    return lambda t: t


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
