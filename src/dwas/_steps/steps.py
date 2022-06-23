# Those are protocols...
# pylint: disable=unused-argument

import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional, Protocol, runtime_checkable

from .._config import Config


@runtime_checkable
class Step(Protocol):
    __call__: Callable[..., None]


@runtime_checkable
class StepWithSetup(Step, Protocol):
    setup: Callable[..., None]


@runtime_checkable
class StepWithDependentSetup(Step, Protocol):
    # pylint: disable=redefined-outer-name
    def setup_dependent(
        self,
        original_step: "StepHandlerProtocol",
        current_step: "StepHandlerProtocol",
    ) -> None:
        ...


class StepHandlerProtocol:
    name: str
    requires: List[str]
    func: Step
    python: str
    run_by_default: bool = False

    @property
    def config(self) -> Config:
        ...

    @property
    def cache_path(self) -> Path:
        ...

    def install(self, *packages: str) -> None:
        ...

    def run(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        *,
        external_command: bool = False,
        silent_on_success: bool = False,
    ) -> subprocess.CompletedProcess[None]:
        ...
