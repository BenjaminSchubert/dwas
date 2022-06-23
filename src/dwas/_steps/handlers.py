import logging
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from .._config import Config
from .._dependency_injection import call_with_parameters
from .._exceptions import BaseDwasException
from .._pipeline import Pipeline
from .._runners import VenvRunner
from .steps import (
    Step,
    StepHandlerProtocol,
    StepWithDependentSetup,
    StepWithSetup,
)

LOGGER = logging.getLogger(__name__)


class BaseStepHandler(ABC):
    def __init__(
        self,
        name: str,
        pipeline: Pipeline,
        requires: List[str],
        run_by_default: bool = True,
    ) -> None:
        self.name = name
        self.requires = requires
        self.run_by_default = run_by_default
        self._pipeline = pipeline

    @abstractmethod
    def _execute(self) -> None:
        pass

    @abstractmethod
    def _execute_dependent_setup(self, current_step: "StepHandler") -> None:
        pass


class StepHandler(StepHandlerProtocol, BaseStepHandler):
    def __init__(
        self,
        name: str,
        func: Step,
        pipeline: Pipeline,
        python: Optional[str],
        requires: Optional[List[str]] = None,
        run_by_default: bool = True,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            name,
            pipeline,
            requires if requires is not None else [],
            run_by_default,
        )

        self.name = name
        self.func = func
        if python is None:
            python = f"python{sys.version_info[0]}.{sys.version_info[1]}"
        elif re.match(
            r"\d+\.\d+", python
        ):  # version specified, assume cpython
            python = f"python{python}"

        self.python = python
        if parameters is None:
            self.parameters = {"step": self}
        else:
            if "step" in parameters:
                raise BaseDwasException(
                    "'step' cannot be used as a parameter name. It is reserved by the StepHandler."
                )

            self.parameters = parameters
            self.parameters["step"] = self

        self._runner = VenvRunner(self.name, self.python, self.config)

    @property
    def config(self) -> Config:
        return self._pipeline.config

    @property
    def cache_path(self) -> Path:
        return self.config.cache_path.joinpath(
            "cache", self.name.replace("/", "-").replace(":", "-")
        )

    def install(self, *packages: str) -> None:
        self._runner.install(*packages)

    def run(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        *,
        external_command: bool = False,
        silent_on_success: bool = False,
    ) -> subprocess.CompletedProcess[None]:
        return self._runner.run(
            command,
            env=env,
            external_command=external_command,
            silent_on_success=silent_on_success,
        )

    def _execute(self) -> None:
        if self.config.skip_setup:
            LOGGER.debug("Skipping setup phase")
        else:
            self._runner.prepare()

            if isinstance(self.func, StepWithSetup):
                call_with_parameters(self.func.setup, self.parameters.copy())

        if self.config.skip_run:
            LOGGER.debug("Skipping run")
            return

        for requirement in self.requires:
            # StepHandler is a public interface, we don't want users accessing
            # this method.
            # pylint: disable=protected-access
            self._pipeline.get_requirement(
                requirement
            )._execute_dependent_setup(self)

        call_with_parameters(self.func, self.parameters.copy())

    def _execute_dependent_setup(self, current_step: "StepHandler") -> None:
        if isinstance(self.func, StepWithDependentSetup):
            LOGGER.debug("Injecting dependency setup from %s", self.name)
            self.func.setup_dependent(self, current_step)


class StepGroupHandler(BaseStepHandler):
    def _execute(self) -> None:
        LOGGER.debug("Step %s is a meta step. Nothing to do", self.name)

    def _execute_dependent_setup(self, current_step: "StepHandler") -> None:
        for requirement in self.requires:
            # StepHandler is a public interface, we don't want users accessing
            # this method.
            # pylint: disable=protected-access
            self._pipeline.get_requirement(
                requirement
            )._execute_dependent_setup(current_step)
