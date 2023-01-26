from typing import Callable, Dict, List, Optional, Sequence

from .._exceptions import BaseDwasException
from .._inspect import get_location
from .._pipeline import get_pipeline
from .parametrize import build_parameters, parametrize
from .steps import Step, StepRunner


def register_step(
    func: Step,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    passenv: Optional[List[str]] = None,
    setenv: Optional[Dict[str, str]] = None,
) -> Step:
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

                def my_step(step: StepRunner): ...

                register_step(my_step)

            and it will be available as ``my_step``.

    :param description:

        An optional description of what the current step does

        In order to help developers on your project, adding descriptions to
        various steps can make it easier to understand what they should use.

        For example:

        .. code-block::

            register_step(your_step, description="This step does something")
            # The description here will be:
            #   "This step does something"

        The description will be added to all steps generated here unless you
        also parametrize them with a description. In which case, only the top
        level group created will use the description passed.

        The other steps will use the parametrized description.

        In the case of multiple steps, the description will also be formatted
        with the various arguments passed.

        For example:

        .. code-block::

            register_step(
                parametrize("python", ["3.9", "3.10"])(test),
                description="Run tests for python {python}",
            )
            # Will give the following descriptions:
            #   - test: "Run tests for python {python}"
            #   - test[3.9]: "Run tests for python 3.9"
            #   - test[3.10]: "Run tests for python3.10"

        Or if you want to give a separate description for each:

        .. code-block::

            register_step(
                parametrize(
                    ("builder", "description"),
                    [
                        ("html", "Build html documentation"),
                        ("linkcheck", "Check documentation links are valid"),
                    ]
                )(sphinx_step),
                name="docs",
                description="Build and check documentation"
            )
            # Will give the following descriptions:
            #   - docs: Build and check documentation
            #   - docs[html]: Build html documentation
            #   - docs[linkcheck]: Check documentation links are valid

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
    :param passenv: A list of environment variables to pass through to the step.
    :param setenv: A list of environment variables to set in the context of the
                   step.
    :return: The step that was passed as argument.
    :raises BaseDwasException: If no :python:`name` is passed and the :python:`func`
                               parameter does not have a :python:`__name__`
                               attribute.
    """
    pipeline = get_pipeline()

    if name is None:
        name = getattr(func, "__name__", None)
        if name is None:
            raise BaseDwasException(
                f"the step at {get_location(func)} does not implement `__name__`"
                " and `name` was not passed as an argument"
            )

    func = build_parameters(
        python=python,
        requires=requires,
        run_by_default=run_by_default,
        passenv=passenv,
        setenv=setenv,
    )(func)

    pipeline.register_step(name, description, func)
    return func


def register_managed_step(
    func: Step,
    dependencies: Optional[Sequence[str]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    passenv: Optional[List[str]] = None,
    setenv: Optional[Dict[str, str]] = None,
) -> Step:
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
    :param description: An optional description of what the current step does
    :param python: The python version to use for this step
    :param requires: The list of steps this step depends on
    :param run_by_default: Whether to run by default or not
    :param passenv: A list of environment variables to pass through to the step.
    :param setenv: A list of environment variables to set in the context of the
                   step.
    :return: The step that was passed as argument.
    :raises BaseDwasException: If the :python:`func` passed already has a
                               :python:`setup` attribute defined.
    """
    if hasattr(func, "setup"):
        raise BaseDwasException(
            f"the step at {get_location(func)} already implements `setup`,"
            " cannot override it to install dependencies."
            " You can add `step.install(*dependencies)` inside your setup"
            " function to handle them."
        )

    # pylint: disable=redefined-outer-name
    def install(step: StepRunner, dependencies: str) -> None:
        step.install(*dependencies)

    setattr(func, "setup", install)
    if dependencies is not None:
        func = parametrize("dependencies", [dependencies])(func)

    return register_step(
        func,
        name=name,
        description=description,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
        passenv=passenv,
        setenv=setenv,
    )


def register_step_group(
    name: str,
    requires: List[str],
    description: Optional[str] = None,
    run_by_default: Optional[bool] = None,
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
    :param description: An optional description of what the current step does
    :param run_by_default: Whether to run this step by default or not
    """
    pipeline = get_pipeline()
    pipeline.register_step_group(name, requires, description, run_by_default)


def step(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    passenv: Optional[List[str]] = None,
    setenv: Optional[Dict[str, str]] = None,
) -> Callable[[Step], Step]:
    """
    Register the decorated :term:`step` and make it available to the pipeline.

    This is a convenience wrapper calling :py:func:`register_step` on
    the decorated object.

    :param name: The name used to refer to this step
    :param description: An optional description of what the current step does
    :param python: The python version to use in this step
    :param requires: The list of steps that this step depends on
    :param run_by_default: Whether this step should run by default or not
    :param passenv: A list of environment variables to pass through to the step.
    :param setenv: A list of environment variables to set in the context of the
                   step.
    """

    def wrapper(func: Step) -> Step:
        register_step(
            func,
            name=name,
            description=description,
            python=python,
            requires=requires,
            run_by_default=run_by_default,
            passenv=passenv,
            setenv=setenv,
        )
        return func

    return wrapper


def managed_step(
    dependencies: Sequence[str],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    passenv: Optional[List[str]] = None,
    setenv: Optional[Dict[str, str]] = None,
) -> Callable[[Step], Step]:
    """
    Register the decorated :term:`step`, and handle installing its dependencies.

    This is a convenience wrapper calling :py:func:`register_managed_step` on
    the decorated object.

    :param dependencies: A list of dependencies to install as a setup phase.
    :param name: The name used to refer to this step
    :param description: An optional description of what the current step does
    :param python: The python version to use in this step
    :param requires: The list of steps that this step depends on
    :param run_by_default: Whether this step should run by default or not
    :param passenv: A list of environment variables to pass through to the step.
    :param setenv: A list of environment variables to set in the context of the
                   step.
    """

    def wrapper(func: Step) -> Step:
        register_managed_step(
            func,
            dependencies,
            name=name,
            description=description,
            python=python,
            requires=requires,
            run_by_default=run_by_default,
            passenv=passenv,
            setenv=setenv,
        )
        return func

    return wrapper
