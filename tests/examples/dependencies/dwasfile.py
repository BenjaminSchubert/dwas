import dwas
import dwas.predefined

dwas.register_managed_step(dwas.predefined.package())


@dwas.managed_step(None)
@dwas.parametrize("requires", (["package"], []), ids=("package", "no-package"))
@dwas.parametrize(
    "dependencies",
    (
        ["--requirements=pyproject.toml"],
        ["--group=dev"],
        ["--group=other"],
        ["--group=dev", "--group=other", "--requirements=pyproject.toml"],
    ),
    ids=("pyproject", "dev-group", "other-group", "all"),
)
def dependencies(step: dwas.StepRunner) -> None:
    step.run(["uv", "pip", "list", "--format=json"], external_command=True)
