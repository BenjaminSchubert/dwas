from dwas import register_managed_step
from dwas.predefined import coverage, pytest

register_managed_step(
    pytest(args=["--cov", "--cov-report="]),
    dependencies=["pytest", "pytest-cov"],
)

register_managed_step(coverage(), requires=["pytest"])
