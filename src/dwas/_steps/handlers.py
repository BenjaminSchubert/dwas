import itertools
import logging
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .._config import Config
from .._dependency_injection import call_with_parameters
from .._exceptions import BaseDwasException
from .._runners import VenvRunner
from .steps import Step
from .steps import StepHandler as StepHandlerProtocol
from .steps import StepWithArtifacts, StepWithDependentSetup, StepWithSetup

if TYPE_CHECKING:
    from .._pipeline import Pipeline


LOGGER = logging.getLogger(__name__)


class BaseStepHandler(ABC):
    def __init__(
        self,
        name: str,
        pipeline: "Pipeline",
        requires: Optional[List[str]] = None,
        run_by_default: Optional[bool] = None,
    ) -> None:
        self.name = name
        self._requires = requires if requires is not None else []
        self._run_by_default: bool = (
            run_by_default if run_by_default is not None else True
        )
        self._pipeline = pipeline

    @abstractmethod
    def _execute(self) -> None:
        pass

    @abstractmethod
    def _execute_dependent_setup(self, current_step: "StepHandler") -> None:
        pass

    @abstractmethod
    def _get_artifacts(self, key: str) -> List[Any]:
        pass

    @abstractmethod
    def _gather_artifacts(self) -> Dict[str, List[Any]]:
        pass


class StepHandler(StepHandlerProtocol, BaseStepHandler):
    # FIXME: should we split the stephandler in two? One for the user-facing
    #        api, one for the internal parts?
    #
    def __init__(
        self,
        name: str,
        func: Step,
        pipeline: "Pipeline",
        python: Optional[str],
        requires: Optional[List[str]] = None,
        run_by_default: Optional[bool] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name, pipeline, requires, run_by_default)

        self.name = name
        self._func = func
        if python is None:
            # FIXME: this probably doesn't handle being installed with pypy/pyston
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
        name = self.name
        # Those chars regularly cause trouble with unescaped glob patterns and
        # such. As such, replace them with "-", hoping this does not cause
        # collisions
        for char in ["/", ":", "*", "[", "]"]:
            name = name.replace(char, "-")

        return self.config.cache_path / "cache" / name

    def get_artifacts(self, key: str) -> List[Any]:
        return list(
            itertools.chain.from_iterable(
                [
                    # StepHandler is a public interface, we don't want users accessing
                    # this method.
                    # pylint: disable=protected-access
                    self._pipeline.get_requirement(requirement)._get_artifacts(
                        key
                    )
                    for requirement in self._requires
                ]
            )
        )

    def install(self, *packages: str) -> None:
        self._runner.install(*packages)

    def run(
        self,
        command: List[str],
        *,
        env: Optional[Dict[str, str]] = None,
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

            if isinstance(self._func, StepWithSetup):
                call_with_parameters(self._func.setup, self.parameters.copy())

        if self.config.skip_run:
            LOGGER.debug("Skipping run")
            return

        for requirement in self._requires:
            # StepHandler is a public interface, we don't want users accessing
            # this method.
            # pylint: disable=protected-access
            self._pipeline.get_requirement(
                requirement
            )._execute_dependent_setup(self)

        call_with_parameters(self._func, self.parameters.copy())

    def _execute_dependent_setup(self, current_step: "StepHandler") -> None:
        if isinstance(self._func, StepWithDependentSetup):
            LOGGER.debug("Injecting dependency setup from %s", self.name)
            self._func.setup_dependent(self, current_step)

    def _get_artifacts(self, key: str) -> List[Any]:
        artifacts = self._gather_artifacts().get(key, [])
        if not artifacts:
            LOGGER.warning(
                "No artifact provided for key '%s' by step '%s'",
                key,
                self.name,
            )
        return artifacts

    def _gather_artifacts(self) -> Dict[str, List[Any]]:
        if not isinstance(self._func, StepWithArtifacts):
            LOGGER.debug("Step %s does not provide any artifacts", self.name)
            return {}

        return self._func.gather_artifacts(self)


class StepGroupHandler(BaseStepHandler):
    def _execute(self) -> None:
        LOGGER.debug("Step %s is a meta step. Nothing to do", self.name)

    def _execute_dependent_setup(self, current_step: "StepHandler") -> None:
        for requirement in self._requires:
            # StepHandler is a public interface, we don't want users accessing
            # this method.
            # pylint: disable=protected-access
            self._pipeline.get_requirement(
                requirement
            )._execute_dependent_setup(current_step)

    def _get_artifacts(self, key: str) -> List[Any]:
        return list(
            itertools.chain.from_iterable(
                [
                    # StepHandler is a public interface, we don't want users accessing
                    # this method.
                    # pylint: disable=protected-access
                    self._pipeline.get_requirement(requirement)._get_artifacts(
                        key
                    )
                    for requirement in self._requires
                ]
            )
        )

    def _gather_artifacts(self) -> Dict[str, List[Any]]:
        raise NotImplementedError("This should never get called")
