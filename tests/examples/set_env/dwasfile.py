import dwas


class Step1:
    __name__ = "step1"

    def setup_dependent(
        self,
        original_step: dwas.StepRunner,  # noqa: ARG002
        current_step: dwas.StepRunner,
    ) -> None:
        current_step.set_env("INJECTED_ENV", "foobar")

    def __call__(self, step: dwas.StepRunner) -> None:
        pass


dwas.register_step(Step1())


@dwas.step(requires=["step1"])
def step2(step: dwas.StepRunner) -> None:
    step.run(["printenv", "INJECTED_ENV"], external_command=True)
