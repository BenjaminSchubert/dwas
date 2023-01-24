import pytest

from ._utils import cli, execute


def test_cli_help():
    execute(["--help"])


@pytest.mark.parametrize(
    ("content", "expected_error"),
    (
        pytest.param(None, "no such file or directory", id="missing-file"),
        pytest.param("hello!", "syntax error:", id="syntax-error"),
        pytest.param(
            "import nonexistent",
            "No module named 'nonexistent'",
            id="import-error",
        ),
    ),
)
def test_handles_invalid_dwasfile_nicely(
    monkeypatch, tmp_path, content, expected_error
):
    monkeypatch.chdir(tmp_path)
    if content is not None:
        tmp_path.joinpath("dwasfile.py").write_text(content)

    result = cli(cache_path=tmp_path / ".dwas", expected_status=2)
    assert expected_error in result.stderr


def test_error_if_passing_posargs_without_step(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath("dwasfile.py").touch()

    result = cli(
        cache_path=tmp_path / ".dwas", steps=["--"], expected_status=2
    )
    assert "Can't specify '--' without specifying a step" in result.stderr


def test_error_if_requesting_a_non_existent_step(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath("dwasfile.py").touch()

    result = cli(
        cache_path=tmp_path / ".dwas", steps=["nonexistent"], expected_status=2
    )
    assert "Unkown step requested: nonexistent" in result.stderr


def test_error_if_excluded_step_does_not_exist(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath("dwasfile.py").touch()

    result = cli(
        cache_path=tmp_path / ".dwas",
        except_steps=["nonexistent"],
        expected_status=2,
    )
    assert "Unkown step excepted: nonexistent" in result.stderr


def test_can_expand_parameters_from_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath("dwasfile.py").touch()

    monkeypatch.setenv("DWAS_ADDOPTS", "--list")
    result = cli(cache_path=tmp_path / ".dwas")
    assert "Available steps" in result.stderr
