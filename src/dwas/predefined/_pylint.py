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
        "dependencies": ["pylint"],
        "additional_arguments": [],
        "files": ["."],
    }
)
class Pylint(Step):
    __name__ = "pylint"

    def __call__(
        self,
        step: StepHandler,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        if step.config.colors and not [
            p
            for p in additional_arguments
            if p.startswith("--output-format") or p.startswith("-f")
        ]:
            additional_arguments.append("--output-format=colorized")

        cmd = ["pylint", *additional_arguments, *files]
        step.run(cmd)


def pylint(
    *,
    name: str = "pylint",
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[Sequence[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[Sequence[str]] = None,
    run_by_default: bool = True,
) -> None:
    pylint_ = Pylint()

    if files is not None:
        pylint_ = parametrize("files", [files], ids=[""])(pylint_)
    if additional_arguments is not None:
        pylint_ = parametrize(
            "additional_arguments", [additional_arguments], ids=[""]
        )(pylint_)

    register_managed_step(
        pylint_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
