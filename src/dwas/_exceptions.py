from typing import List


class BaseDwasException(Exception):
    """
    Base exception used for exceptions thrown by DWAS.

    :param message: A user-facing message explaining what happened.
    :param exit_code:

        the exit code to use for the dwas process if the exception is not caught.

        - 1 means a pipeline run failed
        - 2 means a user or configuration error
    """

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self._message = message
        self.exit_code = exit_code

    def __str__(self) -> str:
        return self._message


class FailedPipelineException(BaseDwasException):
    def __init__(
        self, n_failed_jobs: int, n_blocked_jobs: int, n_cancelled_jobs: int
    ) -> None:
        assert n_failed_jobs > 0
        message = f"{self._pluralize(n_failed_jobs)} failed"
        if n_blocked_jobs > 0:
            message += f", {self._pluralize(n_blocked_jobs)} could not run"
        if n_cancelled_jobs > 0:
            message += f", {self._pluralize(n_cancelled_jobs)} were cancelled"
        super().__init__(message, 1)

    def _pluralize(self, n_jobs: int) -> str:
        if n_jobs > 1:
            return f"{n_jobs} jobs"
        return "1 job"


class UnknownStepsException(BaseDwasException):
    def __init__(self, steps: List[str]) -> None:
        message = f"Unknown steps: {', '.join(steps)}"
        super().__init__(message)


class CyclicStepDependenciesException(BaseDwasException):
    def __init__(self, cycle: List[str]) -> None:
        message = f"Cyclic dependencies between steps: {' --> '.join(cycle)}"
        super().__init__(message)


class DuplicateStepException(BaseDwasException):
    def __init__(self, name: str) -> None:
        # TODO: can we find out which line of the config did this call?
        super().__init__(
            f"A step with the name '{name}' has already been registered"
        )


class UnavailableInterpreterException(BaseDwasException):
    def __init__(self, interpreter: str) -> None:
        super().__init__(f"Missing interpreter: {interpreter}")


class CommandNotFoundException(BaseDwasException):
    def __init__(self, command: str, path: str) -> None:
        super().__init__(
            f"The following command was not found in PATH: {command}.\n"
            f"PATH was set as: '{path}'"
        )


class CommandNotInEnvironment(BaseDwasException):
    def __init__(self, command: str) -> None:
        super().__init__(
            f"The command '{command}' is not part of the environment."
            " If this is intentional, use `external_command=True`"
        )
