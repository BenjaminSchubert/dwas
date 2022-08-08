from typing import Any, Callable, Dict, List, Optional, Sequence

from .._exceptions import BaseDwasException
from .._inspect import get_location
from .._pipeline import get_pipeline
from .handlers import StepGroupHandler, StepHandler
from .parametrize import extract_parameters, parametrize
from .steps import Step
from .steps import StepHandler as StepHandlerProtocol


def register_step(
    func: Step,
    *,
    name: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> None:
    """
    Register the provided :term:`step`.

    .. todo:: Add examples!
    .. todo: mention relation with parametrized!

    :param func: The function or class instance to register as a step
    :param name:

        The name used to refer to this step.

        If this is not provided, the :python:`func` parameter **must** have a
        :python:`__name__` attribute, which will then be used.

        .. note::

            All normal function objects in python will automatically have a
            :python:`__name__` defined as their name.

            You could thus *just* do:

            .. code-block::

                def my_step(step: StepHandler): ...

                register_step(my_step)

            and it will be available as ``my_step``.

    :param python: The python version to use in this step.

        It can be either:

        - :python:`None`, in which case it will use the same version that is used to
          run ``dwas``.
        - a version (e.g. :python:`"3.10"`), in which case cpython is assumed
        - a string (e.g. :python:`"pypy3.9"`, or :python:`"python3.10"`), in which case it will
          be used as is.

    :param requires: The list of steps that this step depends on.

        .. note::

            All dependencies will run whenever this step is requested unless
            ``--only`` or ``--except`` are used.

    :param run_by_default: Whether this step should run by default or not.
                           :python:`None` is considered as :python:`True` here.
    """
    pipeline = get_pipeline()

    if name is None:
        name = getattr(func, "__name__", None)
        if name is None:
            raise BaseDwasException(
                f"the step at {get_location(func)} does not implement `__name__`"
                " and `name` was not passed as an argument"
            )

    parameters = extract_parameters(func)
    all_run_by_default = True
    all_created = []

    for params_id, args in parameters:

        def get_from_if_not_none(
            key: str, original: Any, params_: Dict[str, Any]
        ) -> Any:
            if key in params_:
                if original is not None:
                    raise BaseDwasException(
                        f"`{key}` for {getattr(func, '__name__', name)} was"
                        " passed both in parameters and as an argument."
                        " This is invalid. Please only pass one of them."
                    )
                return params_[key]
            return original

        step_name = ""
        if len(parameters) > 1 and params_id != "":
            step_name = f"[{params_id}]"

        step_name = f"{name}{step_name}"
        current_run_by_default = get_from_if_not_none(
            "run_by_default", run_by_default, args
        )

        all_created.append(step_name)
        all_run_by_default = all_run_by_default and current_run_by_default
        pipeline.register_step(
            StepHandler(
                step_name,
                func,
                pipeline,
                get_from_if_not_none("python", python, args),
                get_from_if_not_none("requires", requires, args),
                current_run_by_default,
                args,
            )
        )

    if len(parameters) > 1:
        register_step_group(name, all_created, all_run_by_default)


def register_managed_step(
    func: Step,
    dependencies: Optional[Sequence[str]],
    *,
    name: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> None:
    """
    Register the provided :term:`step`, and handle installing its dependencies.

    A managed step is a step that depends on python packages being present in
    the environment, and this is taking care of installing the dependencies for
    it as a setup phase.

    .. seealso::

        :py:func:`register_step` has a more thorough explanation of other
        parameters.

    :param func: The function or class instance to register as a step
    :param dependencies: A list of dependencies to install as a setup phase.
                         If :python:`None`, will expect a :python:`dependencies`
                         parameter to be passed via :py:func:`parametrize`.
    :param name: The name to give to the step.
                 Defaults to :python:`func.__name__`
    :param python: The python version to use for this step
    :param requires: The list of steps this step depends on
    :param run_by_default: Whether to run by default or not
    """
    if hasattr(func, "setup"):
        # FIXME: handle nicely
        raise Exception("NOOOO")

    # pylint: disable=redefined-outer-name
    def install(step: StepHandlerProtocol, dependencies: str) -> None:
        step.install(*dependencies)

    setattr(func, "setup", install)
    if dependencies is not None:
        func = parametrize("dependencies", [dependencies], ids=[""])(func)

    register_step(
        func,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )


def register_step_group(
    name: str, requires: List[str], run_by_default: Optional[bool] = None
) -> None:
    """
    Register a :term:`step group`.

    A step group is a step that has no action and only depends on other steps.

    It allows calling multiple steps in a row or together more easily, and, when
    used together with :py:func:`parametrize`, allows calling all the steps
    generated as a single step.

    It will pass every artifacts and information from required steps to the
    caller when asked.

    :param name: The name to give to the group of step
    :param requires: The list of steps that are part of the group
    :param run_by_default: Whether to run this step by default or not
    """
    pipeline = get_pipeline()
    pipeline.register_step(
        StepGroupHandler(name, pipeline, requires, run_by_default)
    )


def step(
    *,
    name: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> Callable[[Step], Step]:
    """
    Register the decorated :term:`step` and make it available to the pipeline.

    This is a convenience wrapper calling :py:func:`register_step` on
    the decorated object.

    :param name: The name used to refer to this step
    :param python: The python version to use in this step
    :param requires: The list of steps that this step depends on
    :param run_by_default: Whether this step should run by default or not
    """

    def wrapper(func: Step) -> Step:
        register_step(
            func,
            name=name,
            python=python,
            requires=requires,
            run_by_default=run_by_default,
        )
        return func

    return wrapper


def managed_step(
    dependencies: Sequence[str],
    *,
    name: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> Callable[[Step], Step]:
    """
    Register the decorated :term:`step`, and handle installing its dependencies.

    This is a convenience wrapper calling :py:func:`register_managed_step` on
    the decorated object.

    :param dependencies: A list of dependencies to install as a setup phase.
    :param name: The name used to refer to this step
    :param python: The python version to use in this step
    :param requires: The list of steps that this step depends on
    :param run_by_default: Whether this step should run by default or not
    """

    def wrapper(func: Step) -> Step:
        register_managed_step(
            func,
            dependencies,
            name=name,
            python=python,
            requires=requires,
            run_by_default=run_by_default,
        )
        return func

    return wrapper
