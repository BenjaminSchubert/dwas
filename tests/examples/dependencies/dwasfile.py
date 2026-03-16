import dwas
import dwas.predefined

dwas.register_step(dwas.predefined.package())


@dwas.managed_step(None)
@dwas.parametrize("requires", (["package"], []), ids=("package", "no-package"))
@dwas.parametrize(
    ("dependencies", "dependencies_sync"),
    (
        ([], True),
        (["--requirements=pyproject.toml"], False),
        (["--only-group=dev"], True),
        (["--group=dev"], False),
        (["--only-group=other"], True),
        (["--group=other"], False),
        (["--group=dev", "--group=other"], True),
        (
            ["--group=dev", "--group=other", "--requirements=pyproject.toml"],
            False,
        ),
    ),
    ids=(
        "sync,pyproject",
        "no-sync,pyproject",
        "sync,dev-group",
        "no-sync,dev-group",
        "sync,other-group",
        "no-sync,other-group",
        "sync,all",
        "no-sync,all",
    ),
)
def dependencies(step: dwas.StepRunner) -> None:
    step.run(["uv", "pip", "list", "--format=json"], external_command=True)
