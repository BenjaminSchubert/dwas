import pytest


def test_does_not_modify_files_by_default(cli, tmp_path):
    # This code is misformatted to trigger an error
    dwasfile_content = """\
from dwas.predefined import unimport
import os

unimport()
"""
    dwasfile_path = tmp_path.joinpath("dwasfile.py")
    dwasfile_path.write_text(dwasfile_content)

    result = cli([], raise_on_error=False)
    assert result.exit_code == 1

    assert dwasfile_path.read_text() == dwasfile_content


def test_can_apply_fixes(cli, tmp_path):
    # This code is misformatted to trigger an error
    dwasfile_content = """\
from dwas.predefined import unimport
import os

unimport(additional_arguments=["--diff", "--remove", "--check"])
"""
    dwasfile_path = tmp_path.joinpath("dwasfile.py")
    dwasfile_path.write_text(dwasfile_content)

    cli([])
    assert dwasfile_path.read_text() != dwasfile_content


@pytest.mark.parametrize(
    "set_cache", [False, True], ids=["default-cache", "provided-cache"]
)
def test_cache_is_automatically_ignored(cli, tmp_path, set_cache):
    dwasfile_content = """\
from dwas.predefined import unimport

unimport()
"""
    dwasfile_path = tmp_path.joinpath("dwasfile.py")
    dwasfile_path.write_text(dwasfile_content)

    args = []

    # Create a misformatted file in the cache
    if set_cache:
        cache_path = tmp_path / "cache"
        args.extend(["--cache-path", str(cache_path)])
    else:
        cache_path = tmp_path / ".dwas"

    cache_path.mkdir()
    cache_path.joinpath("misformated.py").write_text("import os")

    cli(args)


@pytest.mark.parametrize(
    "set_cache", [False, True], ids=["default-cache", "provided-cache"]
)
def test_non_cache_with_same_name_is_not_ignored(cli, tmp_path, set_cache):
    dwasfile_content = """\
from dwas.predefined import unimport

unimport()
"""
    dwasfile_path = tmp_path.joinpath("dwasfile.py")
    dwasfile_path.write_text(dwasfile_content)

    args = []

    # Create a misformatted file in the cache
    if set_cache:
        cache_path = tmp_path / "cache"
        args.extend(["--cache-path", str(cache_path)])
    else:
        cache_path = tmp_path / ".dwas"

    not_cache_path = tmp_path / "not-the-cache" / cache_path.name
    not_cache_path.mkdir(parents=True)
    not_cache_path.joinpath("misformated.py").write_text("import os")

    result = cli(args, raise_on_error=False)
    assert result.exit_code == 1


def test_does_not_exclude_cache_if_not_relative(
    cli, tmp_path, tmp_path_factory
):
    dwasfile_content = """\
from dwas.predefined import unimport

unimport()
"""
    dwasfile_path = tmp_path.joinpath("dwasfile.py")
    dwasfile_path.write_text(dwasfile_content)

    cache_path = tmp_path_factory.mktemp("cache")

    # cache_path.mkdir()
    # cache_path.joinpath("misformated.py").write_text("import os")

    cli(["--cache-path", str(cache_path)])
