from setuptools import setup  # type: ignore

setup(
    name="test-package",
    packages=["test_project"],
    package_dir={"test_project": "src/test_project"},
)
