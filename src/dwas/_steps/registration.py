from typing import Any, Dict, List, Optional, Protocol, Sequence

from .._exceptions import BaseDwasException
from .._inspect import get_location
from .._pipeline import get_pipeline
from .handlers import StepGroupHandler, StepHandler
from .parametrize import extract_parameters, parametrize
from .steps import Step, StepHandlerProtocol


class StepWrapper(Protocol):
    def __call__(self, func: Step) -> Step:
        ...


def register_step(
    func: Step,
    *,
    name: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> None:
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
    if hasattr(func, "setup"):
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
) -> StepWrapper:
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
) -> StepWrapper:
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
