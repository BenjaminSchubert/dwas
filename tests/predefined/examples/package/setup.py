from setuptools import setup

setup(
    name="test-package",
    packages=["test_project"],
    package_dir={"test_project": "src/test_project"},
)
