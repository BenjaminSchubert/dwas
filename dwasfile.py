from pathlib import Path

import dwas
import dwas.predefined

REQUIREMENTS = "-rrequirements/requirements.txt"
TEST_REQUIREMENTS = "-rrequirements/requirements-test.txt"
OLDEST_SUPPORTED_PYTHON = "3.9"
SUPPORTED_PYTHONS = ["3.9", "3.10"]
PYTHON_FILES = ["src/", "tests/", "setup.py", "dwasfile.py"]
REPORTS_PATH = Path(__file__).parent.joinpath("_reports")

##
# Formatting
##
dwas.predefined.isort(files=PYTHON_FILES)
dwas.predefined.black()

# With auto fix
dwas.predefined.isort(
    name="isort:fix",
    additional_arguments=["--atomic"],
    run_by_default=False,
    files=PYTHON_FILES,
)
dwas.predefined.black(
    name="black:fix",
    additional_arguments=[],
    requires=["isort:fix"],
    run_by_default=False,
)
dwas.register_step_group(
    name="fix", requires=["isort:fix", "black:fix"], run_by_default=False
)


##
# Linting
##
dwas.predefined.mypy(
    files=PYTHON_FILES,
    dependencies=["mypy", "types-colorama", TEST_REQUIREMENTS],
    python=OLDEST_SUPPORTED_PYTHON,
)
dwas.predefined.pylint(
    files=["src", "tests"],
    dependencies=[REQUIREMENTS, TEST_REQUIREMENTS, "pylint"],
    python=OLDEST_SUPPORTED_PYTHON,
)
dwas.register_step_group("lint", ["mypy", "pylint"])

##
# Packaging
##
dwas.predefined.package(
    isolate=False, dependencies=["build", "setuptools>=61.0.0", "wheel"]
)

##
# Testing
##
dwas.predefined.pytest(
    dependencies=[TEST_REQUIREMENTS],
    requires=["package"],
    parametrize=dwas.parametrize("python", SUPPORTED_PYTHONS),
)

##
# Reports
##
dwas.predefined.coverage(
    reports=[
        ["html", f"--directory={REPORTS_PATH / 'coverage/html'}"],
        ["xml", f"-o{REPORTS_PATH / 'coverage/coverage.xml'}"],
        ["report", "--show-missing"],
    ],
    requires=["pytest"],
    dependencies=["coverage[toml]"],
)
