import re
from abc import ABC, abstractmethod
from pathlib import Path

import pytest

COLOR_ESCAPE_CODE = re.compile(r"\x1b\[\d+m")


class BaseStepTest(ABC):
    @pytest.mark.usefixtures("project")
    def test_runs_successfully(self, cli, expected_output):
        result = cli([])
        assert expected_output in result.stdout

    @pytest.mark.parametrize(
        "enable_colors", [True, False], ids=["colors", "no-colors"]
    )
    @pytest.mark.usefixtures("project")
    def test_respects_color_settings(self, cli, enable_colors):
        if enable_colors:
            args = ["--colors"]
        else:
            args = ["--no-colors"]

        result = cli(args)

        if enable_colors:
            assert COLOR_ESCAPE_CODE.search(result.stdout)
        else:
            assert not COLOR_ESCAPE_CODE.search(result.stdout)


class BaseLinterTest(ABC):
    @property
    @abstractmethod
    def dwasfile(self) -> str:
        """
        The content of the dwasfile to create for each project.

        The file should contain at least one step that runs by default
        and runs the current linter against all files in the project.
        """

    @property
    @abstractmethod
    def invalid_file(self) -> str:
        """
        The content of a file that should not pass the linter tests.
        """

    @property
    @abstractmethod
    def valid_file(self) -> str:
        """
        The content of a file that should pass the linter tests.
        """

    def _make_project(self, path: Path, valid: bool = True) -> None:
        path.joinpath("dwasfile.py").write_text(self.dwasfile)

        token_file = path.joinpath("src/token.py")
        token_file.parent.mkdir(parents=True)
        if valid:
            token_file.write_text(self.valid_file)
        else:
            token_file.write_text(self.invalid_file)

    @pytest.mark.parametrize(
        "valid", [True, False], ids=["valid-project", "invalid-project"]
    )
    def test_simple_behavior(self, cli, tmp_path, valid):
        self._make_project(tmp_path, valid=valid)
        cli([], expected_status=0 if valid else 1)

    @pytest.mark.parametrize(
        "enable_colors", [True, False], ids=["colors", "no-colors"]
    )
    def test_respects_color_settings(self, cli, tmp_path, enable_colors):
        self._make_project(tmp_path, valid=False)

        if enable_colors:
            args = ["--colors"]
        else:
            args = ["--no-colors"]

        result = cli(args, expected_status=1)

        if enable_colors:
            assert COLOR_ESCAPE_CODE.search(result.stdout)
        else:
            assert not COLOR_ESCAPE_CODE.search(result.stdout)


class BaseFormatterTest(BaseLinterTest):
    @property
    @abstractmethod
    def autofix_step(self) -> str:
        """
        The name of a step that apply fixes on the project.

        It should run against all files in the project when executed.
        """

    def test_does_not_modify_by_default(self, cli, tmp_path):
        tmp_path.joinpath("dwasfile.py").write_text(self.dwasfile)

        token_file = tmp_path.joinpath("src/token.py")
        token_file.parent.mkdir()
        token_file.write_text(self.invalid_file)

        cli([], expected_status=1)
        assert token_file.read_text() == self.invalid_file

    def test_can_apply_fixes(self, cli, tmp_path):
        tmp_path.joinpath("dwasfile.py").write_text(self.dwasfile)

        token_file = tmp_path.joinpath("src/token.py")
        token_file.parent.mkdir()
        token_file.write_text(self.invalid_file)

        cli(["--step", self.autofix_step])
        assert token_file.read_text() != self.invalid_file

        # And run the default step one last time to ensure it did fix everything
        cli([])
