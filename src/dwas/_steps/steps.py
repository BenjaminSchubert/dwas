# Those are protocols...
# pylint: disable=unused-argument

import subprocess
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
)

from .._config import Config


@runtime_checkable
class Step(Protocol):
    """
    Holds the information about a :term:`step` in the pipeline.

    A :term:`step` is essentially a function that can be called and that has a
    :python:`__name__` attribute.

    .. todo:: Add a link to a high level tutorial like getting started

    Steps can then be parametrized by the help of :py:func:`dwas.parametrize`,
    and registered using :py:func:`register_step`. at which point they are
    usable  by dwas.

    :Examples:

        A step can either be a simple function:

        .. code-block::

            @step()
            def my_step(step: StepHandler) -> None:
                step.run(["echo", "hello!"])

        Or a class:

        .. code-block::

            # NOTE: you don't need to explicitely inherit from `Step`
            class MyStep:
                def __call__(self, step: StepHandler) -> None:
                    step.run(["echo", "hello!"])

            register_step(MyStep(), name="my_step")

    .. note::

        Use whichever method you prefer. Both are supported. Classes tend to be
        easier for reusability, but functions work well if you just use them
        in your project.

        We will strive to provide both types in examples.
    """

    # XXX: pylint will complain about the *args/**kwargs with 'arguments-differ'
    #      However, this is the canonical way mypy does for callback protocols
    #      that can accept any kind of parameters.
    #      To avoid the issue, you can also not inherit from 'Step', all the
    #      type checking should still work.
    #
    #      See https://github.com/python/mypy/issues/5876.
    #
    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """
        The method to run when the :term:`step` is invoked.

        :Parameters:

            It can take any amount of parameters, that can be passed by keyword, so
            positional only arguments are not supported.

            Parameters will then be passed using parametrization, with a few specific
            parameters being reserved by the system. Namely:

            - ``step``, which is used to pass the :py:class:`StepHandler`.

            For passing other arguments, see :py:func:`dwas.parametrize` and
            :py:func:`dwas.set_defaults`.
        """


@runtime_checkable
class StepWithSetup(Step, Protocol):
    """
    Defines a :term:`step` that needs some setup that can be cached.

    In addition to having a :py:attr:`~Step.__call__` method, a :py:class:`Step`, can
    implement a :py:func:`~StepWithSetup.setup` function, that gets called
    before the method.

    This can be useful to separate the actual running of the step, from the
    necessary preparations.

    .. warning::

        the :py:attr:`setup` is meant to contain work that does not necessarily
        needs to happen at every run of your step, and can be cached in between.

    .. tip::

        When running ``dwas`` repeatedly, you can pass a ``--no-setup`` flag to
        avoid running those steps again and thus speedup your run.

        .. todo:: Link to a document that gives tips on how to run dwas effectively

    :Examples:

        A setup method can be added on a step declaration:

        .. note:: A more complete pytest example is provided as :py:func:`dwas.predefined.pytest`.

        .. tab:: Using functions

            .. code-block::

                @step()
                def pytest(step: StepHandler) -> None:
                    step.run(["pytest"])

                def install_dependencies(step: StepHandler) -> None:
                    step.run(["pip", "install", "pytest"])

                pytest.setup = install_dependencies

        .. tab:: Using a class

            .. code-block::

                class Pytest:
                    def setup(self, step: StepHandler) -> None:
                        step.run(["pip", "install", "pytest"])

                    def __call__(self, step: StepHandler) -> None:
                        step.run(["pytest"])

                register_step(Pytest(), name="pytest")

        .. tip::

                This is what :py:func:`register_managed_step` does to install your
                python dependencies.
    """

    setup: Callable[..., None]
    """
    The setup method that will be invoked before running the step.

    This step should run work that is necessary for the test to be able to run
    but that does not require running every time, as it can be skipped when
    running dwas with `--no-setup`.

    :Parameters:

        Parameters are passed to this function the same way they are passed to
        :py:func:`~Step.__call__`
    """


@runtime_checkable
class StepWithDependentSetup(Step, Protocol):
    """
    Defines a :term:`step` that will act in the context of its dependent steps.

    In addition to having a :py:func:`~Step.__call__` method, a
    :py:class:`Step` can act in the context of a dependent step, before this
    one runs.

    This allows another step to, for example, install the project it just built
    into another virtual environment.

    .. note:: This method is called *after* :py:func:`~StepWithSetup.setup`

    .. warning::

        This method is *always* called when running, and cannot be skipped like
        :py:func:`~StepWithSetup.setup` by passing ``--no-setup``.

    :Examples:

        You might want to have a step that builds a wheel of your current
        package and run your tests against it. This could be done like:

        .. note::

            A more complete packaging example is provided as
            :py:func:`dwas.predefined.package`

        .. tab:: Using functions

            .. code-block::

                @managed_step(dependencies=["build"])
                def package(step: StepHandler) -> None:
                    step.run([step.python, "-m", "build", f"--outdir={step.cache_path}"])

                def install(self, original_step: StepHandler, current_step: StepHandler) -> None:
                    wheels = list(original_step.cache_path.glob("*.whl"))
                    # Assuming this is a universal wheel
                    assert len(wheels) == 1

                    current_step.run(
                        [current_step.python, "-m", "pip", "install", str(wheels[0])],
                        silent_on_success=step.config.verbosity < 1,
                    )

                package.setup_dependent = install

                # This can now be used as a dependency
                @step(requires=["package"])
                def my_step(step: StepHandler) -> None:
                    step.run(["myproject", "--help"])

        .. tab:: Using a class

            .. code-block::

                class Package:
                    def __call__(step: StepHandler) -> None:
                        step.run([step.python, "-m", "build", f"--outdir={step.cache_path}"])

                    def setup_dependent(
                        self,
                        original_step: StepHandler,
                        current_step: StepHandler,
                    ) -> None:
                        wheels = list(original_step.cache_path.glob("*.whl"))
                        # Assuming this is a universal wheel
                        assert len(wheels) == 1

                        current_step.run(
                            [current_step.python, "-m", "pip", "install", str(wheels[0])],
                            silent_on_success=step.config.verbosity < 1,
                        )

                register_managed_step(Package(), name="package", dependencies=["build"])

                # This can now be used as a dependency
                @step(requires=["package"])
                def my_step(step: StepHandler) -> None:
                    step.run(["myproject", "--help"])
    """

    def setup_dependent(
        self,
        original_step: "StepHandler",
        current_step: "StepHandler",
    ) -> None:
        """
        Run some logic into a dependent step.

        :param original_step: The original step handler that was used when the
                              step defining this method was called.
        :param current_step: The current step handler, that contains the
                             context of the step that is going to be executed.
        """


@runtime_checkable
class StepWithArtifacts(Step, Protocol):
    """
    Defines a :term:`step` creating artifacts that can be consumed by dependent steps.

    Sometimes, you want to share artifacts between jobs. For example, you might
    have some ``pytest`` runs that generate coverage reports, and then you
    want to aggregate them together.

    This allows a programmatic interface between steps to access artifacts.
    See :py:func:`StepHandler.get_artifacts` for how to retrieve those artifacts
    from another step.

    :Examples:

        If you wanted to have multiple pytest steps, and one that aggregates
        the coverage, you could do:

        .. tip::

            This is what the provided :py:func:`dwas.predefined.pytest` step
            does.

        .. tab:: Using functions

            .. code-block::

                @step()
                @parametrize(python=["3.9", "3.10"])
                def pytest(step: StepHandler) -> None:
                    step.run(
                        ["pytest"],
                        env={
                            "COVERAGE_FILE": str(
                                step.cache_path.joinpath(step.python, "coverage")
                            ),
                        },
                    )

                def gather_artifacts(step: "StepHandler") -> Dict[str, List[Any]]:
                    return step.cache_path.joinpath(step.python, "coverage")

                pytest.gather_artifacts = gather_artifacts

        .. tab:: Using classes

            .. code-block::

                class Pytest:
                    def _get_coverage_file(self, step: StepHandler) -> str:
                        return str(step.cache_path / "reports" / "coverage")

                    def gather_artifacts(self, step: StepHandler) -> Dict[str, List[Any]]:
                        return {"coverage_files": [self._get_coverage_file(step)]}

                    def __call__(self, step: StepHandler) -> None:
                        step.run(
                            ["pytest", *args],
                            env={"COVERAGE_FILE": self._get_coverage_file(step)},
                        )

                register_step(parametrize("python", ["3.9", "3.10"])(Pytest()))

        And you could then combine and display the coverage like:

        .. code-block::

            @managed_step(dependencies=["coverage"], requires=["pytest"])
            def coverage(self, step: StepHandler) -> None:
                env = {"COVERAGE_FILE": str(step.cache_path / "coverage")}

                coverage_files = step.get_artifacts("coverage_files")
                if not coverage_files:
                    raise Exception("No coverage files provided. Can't proceed")

                step.run(["coverage", "combine", "--keep", *coverage_files], env=env)
                step.run(["coverage", "html"], env=env)

        .. tip:: The :py:func:`dwas.predefined.coverage` step does roughly this.
    """

    def gather_artifacts(self, step: "StepHandler") -> Dict[str, List[Any]]:
        """
        Gather all artifacts exposed by this step.

        :param step: The step handler that was used when running the step.
        :return: A dictionary of artifact key to a list of arbitrary data.
                 This **must** return a list, as they are merged with other
                 steps' artifacts into a single list per artifact key.
        """


class StepHandler:
    """
    Defines the manager for a :term:`step`, and provides utilities for the step to run.

    This is passed as an argument to every step that executes as ``step``.

    It provides various utilities to allow the step to run in an isolated,
    standardized environment.
    """

    name: str
    """The name of the current step"""

    python: str
    """
    The name of the current python interpreter

    .. note:: This is not the absolute path to it, just its name.
    """

    @property
    def config(self) -> Config:
        """
        The global configuration for the current run.

        At this point, you should not be modifying it. However, you can
        use it to act differently on what you are doing. For example,
        you might want to use the :py:attr:`Config.verbosity` to
        configure the output of some commands you run.
        """

    @property
    def cache_path(self) -> Path:
        """
        The path to the cache for the current step.

        This can be used to store temporary files or any other artifacts.

        This will be cleaned up and emptied before the step runs.
        """

    def get_artifacts(self, key: str) -> List[Any]:
        """
        Get the artifacts exported by previous steps for the given key.

        See :py:func:`StepWithArtifacts.gather_artifacts` for how to expose
        artifacts from a step.

        .. note::

            This only returns artifacts exported by the direct dependencies of
            the current step, and does not go recursively. Unless this depends
            on a step group, in which case it returns the artifacts of all
            dependencies in the group.

        :param key: The name of the key for which to get the artifacts
        :return: A list of artifacts, one per step providing artifacts for the
                 given key.
        """

    def install(self, *packages: str) -> None:
        """
        Install the provided packages in the current environment.

        This is a wrapper around the canonical way of installing packages in
        the provided environment (e.g. `pip`), so that users don't need to
        handle the details when changing the type of virtual environment (e.g.
        if you wanted to move to conda.).

        :param packages: which packages to install
        """

    def run(
        self,
        command: List[str],
        *,
        env: Optional[Dict[str, str]] = None,
        external_command: bool = False,
        silent_on_success: bool = False,
    ) -> subprocess.CompletedProcess[None]:
        """
        Run the provided command in the current environment.

        This method makes it's best to ensure the process' environment is
        as isolated as possible.

        It will enforce that the first argument of the command is part of the
        python virtual environment that is specially created for the current
        step (in the case when there is isolation).

        It will also ensure that the environment in which it is run is clean,
        and will only get environment entries from :py:attr:`Config.environ`.
        To add more values, use `env`.

        :param command: The command to run, as a list of arguments.
        :param env: Additional environment variables to pass to the process.
                    Those will be merged on top of the :py:attr:`Config.environ`
                    values and can override them, but not remove them.
        :param external_command: Set to true if you want to run a command that
                                 lives outside the current virtual environment.
                                 Otherwise, this will fail the command.
        :param silent_on_success: Whether to silence the command's output if it
                                  succeeds, or show it every time.
        :return: a :py:class:`subprocess.CompletedProcess` with `stderr` and
                 `stdout` set to ``None``.
        """
