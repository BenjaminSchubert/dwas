from __future__ import annotations

import inspect
import itertools
import logging
import os
import shutil
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from .._dependency_injection import call_with_parameters
from .._exceptions import BaseDwasException
from .._runners import VenvRunner
from .steps import (
    Step,
    StepRunner,
    StepWithArtifacts,
    StepWithCleanup,
    StepWithDependentSetup,
    StepWithSetup,
)

if TYPE_CHECKING:
    import subprocess

    from .._config import Config
    from .._pipeline import Pipeline


LOGGER = logging.getLogger(__name__)


class BaseStepHandler(ABC):
    def __init__(
        self,
        name: str,
        pipeline: Pipeline,
        requires: list[str] | None = None,
        run_by_default: bool | None = None,
        description: str | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.requires = requires if requires is not None else []
        self.run_by_default = (
            run_by_default if run_by_default is not None else True
        )
        self._pipeline = pipeline

    @abstractmethod
    def clean(self) -> None:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def set_user_args(self, args: list[str]) -> None:
        pass

    @abstractmethod
    def _execute_dependent_setup(self, current_step: BaseStepHandler) -> None:
        pass

    @abstractmethod
    def _get_artifacts(self, key: str) -> list[Any]:
        pass


class StepHandler(BaseStepHandler):
    def __init__(
        self,
        name: str,
        func: Step,
        pipeline: Pipeline,
        python_spec: str | None,
        requires: list[str] | None = None,
        run_by_default: bool | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
        passenv: list[str] | None = None,
        setenv: dict[str, str] | None = None,
    ) -> None:
        super().__init__(name, pipeline, requires, run_by_default, description)

        self.name = name

        self._func = func
        step_environment = self._resolve_environ(passenv, setenv)
        self._venv_runner = VenvRunner(
            self.name,
            python_spec,
            self.config,
            step_environment,
            proc_manager=self._pipeline.proc_manager,
        )
        self._step_runner = StepRunner(self)

        if parameters is None:
            self.parameters: dict[str, Any] = {
                "step": self._step_runner,
                "user_args": None,
            }
        else:
            for param in ["step", "user_args"]:
                if param in parameters:
                    raise BaseDwasException(
                        f"Cannot instantiate step {name}: '{param}' cannot be"
                        "used as a parameter name. It is reserved by the"
                        " StepHandler."
                    )

            self.parameters = parameters
            self.parameters["step"] = self._step_runner
            self.parameters["user_args"] = None

    @property
    def config(self) -> Config:
        return self._pipeline.config

    @property
    def python(self) -> str:
        return self._venv_runner.python

    def set_user_args(self, args: list[str]) -> None:
        step_signature = inspect.signature(self._func)
        if "user_args" not in step_signature.parameters:
            LOGGER.warning(
                "Step '%s' was passed user arguments but does not handle them.",
                self.name,
            )
        self.parameters["user_args"] = args

    def get_artifacts(self, key: str) -> list[Any]:
        return list(
            itertools.chain.from_iterable(
                [
                    # Pylint check here is wrong, it's still an instance of our class
                    # pylint: disable=protected-access
                    self._pipeline.get_step(  # noqa: SLF001
                        requirement
                    )._get_artifacts(key)
                    for requirement in self.requires
                ]
            )
        )

    def install(self, *packages: str) -> None:
        self._venv_runner.install(*packages)

    def run(
        self,
        command: list[str],
        *,
        cwd: str | bytes | os.PathLike[str] | os.PathLike[bytes] | None = None,
        env: dict[str, str] | None = None,
        external_command: bool = False,
        silent_on_success: bool = False,
    ) -> subprocess.CompletedProcess[None]:
        return self._venv_runner.run(
            command,
            cwd=cwd,
            env=env,
            external_command=external_command,
            silent_on_success=silent_on_success,
        )

    def execute(self) -> None:
        if self.config.skip_setup:
            LOGGER.debug("Skipping setup phase")
        else:
            self._venv_runner.prepare()

            if isinstance(self._func, StepWithSetup):
                call_with_parameters(self._func.setup, self.parameters.copy())

        if self.config.skip_run:
            LOGGER.debug("Skipping run")
            return

        for requirement in self.requires:
            # Pylint check here is wrong, it's still an instance of our class
            # pylint: disable=protected-access
            self._pipeline.get_step(  # noqa: SLF001
                requirement
            )._execute_dependent_setup(self)

        call_with_parameters(self._func, self.parameters.copy())

    def clean(self) -> None:
        if isinstance(self._func, StepWithCleanup):
            call_with_parameters(self._func.clean, self.parameters.copy())

        self._venv_runner.clean()

        with suppress(FileNotFoundError):
            shutil.rmtree(self._step_runner.cache_path)

    def _execute_dependent_setup(self, current_step: BaseStepHandler) -> None:
        assert isinstance(current_step, StepHandler)

        if isinstance(self._func, StepWithDependentSetup):
            LOGGER.debug("Injecting dependency setup from %s", self.name)
            self._func.setup_dependent(
                self._step_runner,
                # Pylint check here is wrong, it's still an instance of our class
                # pylint: disable=protected-access
                current_step._step_runner,  # noqa: SLF001
            )

    def _get_artifacts(self, key: str) -> list[Any]:
        if isinstance(self._func, StepWithArtifacts):
            all_artifacts = self._func.gather_artifacts(self._step_runner)
        else:
            LOGGER.debug("Step %s does not provide any artifacts", self.name)
            all_artifacts = {}

        artifacts = all_artifacts.get(key, [])
        if not artifacts:
            LOGGER.warning(
                "No artifact provided for key '%s' by step '%s'",
                key,
                self.name,
            )
        return artifacts

    def _resolve_environ(
        self, passenv: list[str] | None, setenv: dict[str, str] | None
    ) -> dict[str, str]:
        base_env = {}
        if setenv:
            base_env.update(setenv)
        if passenv:
            for key in passenv:
                if key in base_env:
                    LOGGER.warning(
                        "Step %s has %s both passed as `passenv` and `setenv`."
                        " `setenv` takes precedence.",
                        self.name,
                        key,
                    )
                    continue

                val = os.getenv(key)
                if val is None:
                    LOGGER.debug(
                        "Step %s requested a passthrough of environment"
                        " variable %s, but it is not in the environment",
                        self.name,
                        key,
                    )
                    continue

                base_env[key] = val

        return base_env


class StepGroupHandler(BaseStepHandler):
    def clean(self) -> None:
        pass

    def execute(self) -> None:
        LOGGER.debug("Step %s is a meta step. Nothing to do", self.name)

    def set_user_args(self, args: list[str]) -> None:
        for requirement in self.requires:
            self._pipeline.get_step(requirement).set_user_args(args)

    def _execute_dependent_setup(self, current_step: BaseStepHandler) -> None:
        for requirement in self.requires:
            # Pylint check here is wrong, it's still an instance of our class
            # pylint: disable=protected-access
            self._pipeline.get_step(  # noqa: SLF001
                requirement
            )._execute_dependent_setup(current_step)

    def _get_artifacts(self, key: str) -> list[Any]:
        return list(
            itertools.chain.from_iterable(
                [
                    # Pylint check here is wrong, it's still an instance of our class
                    # pylint: disable=protected-access
                    self._pipeline.get_step(  # noqa: SLF001
                        requirement
                    )._get_artifacts(key)
                    for requirement in self.requires
                ]
            )
        )
