from typing import List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import (
    Step,
    StepHandler,
    parametrize,
    register_managed_step,
    set_defaults,
)


@set_defaults(
    {
        "dependencies": ["isort[colors]"],
        "additional_arguments": ["--check-only", "--diff"],
        "files": ["."],
    }
)
class Isort(Step):
    __name__ = "isort"

    def __call__(
        self,
        step: StepHandler,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        if step.config.colors:
            additional_arguments.append("--color")

        step.run(["isort", *additional_arguments, *files])


def isort(
    *,
    name: Optional[str] = None,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
    dependencies: Optional[List[str]] = None,
) -> None:
    isort_ = Isort()

    if files is not None:
        isort_ = parametrize("files", [files], ids=[""])(isort_)
    if additional_arguments is not None:
        isort_ = parametrize(
            "additional_arguments", [additional_arguments], ids=[""]
        )(isort_)

    register_managed_step(
        isort_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
