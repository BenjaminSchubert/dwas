import pytest


def test_cli_help(cli):
    cli(["--help"])


@pytest.mark.parametrize(
    ("content", "expected_error"),
    (
        pytest.param(None, "no such file or directory", id="missing-file"),
        pytest.param("hello!", "syntax error:", id="syntax-error"),
        pytest.param(
            "import nonexistent",
            "No module named \\'nonexistent\\'",
            id="import-error",
        ),
    ),
)
def test_handles_invalid_dwasfile_nicely(
    cli, monkeypatch, tmp_path, content, expected_error
):
    monkeypatch.chdir(tmp_path)
    if content is not None:
        tmp_path.joinpath("dwasfile.py").write_text(content)

    with pytest.raises(Exception) as exc_wrapper:
        cli([])

    assert expected_error in str(exc_wrapper.value)
