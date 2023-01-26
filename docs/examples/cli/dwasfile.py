import dwas
import dwas.predefined

REQUIREMENTS = "-rrequirements/requirements.txt"
TEST_REQUIREMENTS = "-rrequirements/requirements-test.txt"
TYPES_REQUIREMENTS = "-rrequirements/requirements-types.txt"
OLDEST_SUPPORTED_PYTHON = "3.9"
SUPPORTED_PYTHONS = ["3.9", "3.10", "3.11"]
PYTHON_FILES = ["docs", "src/", "tests/", "setup.py", "dwasfile.py"]


##
# Formatting
##
dwas.register_managed_step(
    dwas.predefined.isort(
        additional_arguments=["--atomic"], files=PYTHON_FILES
    ),
    name="isort:fix",
    run_by_default=False,
)
dwas.register_managed_step(
    dwas.predefined.black(additional_arguments=[]),
    name="black:fix",
    requires=["isort:fix"],
    run_by_default=False,
)
dwas.register_step_group(
    name="fix",
    description="Fix all auto-fixable issues on the project",
    requires=["isort:fix", "black:fix"],
    run_by_default=False,
)


##
# Linting
##
dwas.register_managed_step(
    dwas.predefined.mypy(files=PYTHON_FILES),
    dependencies=[
        "mypy",
        TEST_REQUIREMENTS,
        TYPES_REQUIREMENTS,
    ],
    python=OLDEST_SUPPORTED_PYTHON,
)
dwas.register_managed_step(
    dwas.predefined.pylint(files=PYTHON_FILES),
    dependencies=[
        REQUIREMENTS,
        TEST_REQUIREMENTS,
        "pylint",
    ],
    python=OLDEST_SUPPORTED_PYTHON,
)
dwas.register_step_group(
    "lint", ["mypy", "pylint"], description="Run linter on the project"
)

##
# Packaging
##
dwas.register_managed_step(
    dwas.predefined.package(isolate=False),
    dependencies=["build", "setuptools>=61.0.0", "wheel"],
)

##
# Testing
##
dwas.register_managed_step(
    dwas.parametrize("description", ("Run tests for python {python}",))(
        dwas.parametrize("python", SUPPORTED_PYTHONS)(dwas.predefined.pytest())
    ),
    dependencies=[TEST_REQUIREMENTS],
    passenv=["TERM"],
    requires=["package"],
    description="Run tests for all supported python versions",
)
