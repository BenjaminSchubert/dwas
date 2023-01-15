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

    result = cli(cache_path=tmp_path, expected_status=2)
    assert expected_error in result.stderr
