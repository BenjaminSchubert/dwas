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
        "dependencies": ["black"],
        "files": ["."],
        "additional_arguments": ["--check", "--diff", "-W1"],
    }
)
class Black(Step):
    __name__ = "black"

    def __call__(
        self,
        step: StepHandler,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        if (
            "--color" not in additional_arguments
            and "--no-color" not in additional_arguments
        ):
            color_arg = f"--{'' if step.config.colors else 'no-'}color"
            additional_arguments.append(color_arg)

        step.run(["black", *additional_arguments, *files])


def black(
    *,
    name: Optional[str] = None,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    run_by_default: bool = True,
) -> None:
    black_ = Black()

    if files is not None:
        black_ = parametrize("files", [files], ids=[""])(black_)

    if additional_arguments is not None:
        black_ = parametrize(
            "additional_arguments", [additional_arguments], ids=[""]
        )(black_)

    register_managed_step(
        black_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
