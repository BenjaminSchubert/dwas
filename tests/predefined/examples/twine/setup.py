from setuptools import setup

setup(
    long_description="Just a test project",
    long_description_content_type="text/x-rst",
    name="test-package",
    packages=["test_project"],
    package_dir={"test_project": "src/test_project"},
)
