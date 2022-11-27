def test_does_not_modify_files_by_default(cli, tmp_path):
    # This code is misformatted to trigger an error
    dwasfile_content = """\
from dwas import register_managed_step
from dwas.predefined import black
register_managed_step(black())
"""
    dwasfile_path = tmp_path.joinpath("dwasfile.py")
    dwasfile_path.write_text(dwasfile_content)

    result = cli([], raise_on_error=False)
    assert result.exit_code == 1

    assert dwasfile_path.read_text() == dwasfile_content


def test_can_apply_fixes(cli, tmp_path):
    # This code is misformatted to trigger an error
    dwasfile_content = """\
from dwas import register_managed_step
from dwas.predefined import black
register_managed_step(black(additional_arguments=[]))
"""
    dwasfile_path = tmp_path.joinpath("dwasfile.py")
    dwasfile_path.write_text(dwasfile_content)

    cli([])
    assert dwasfile_path.read_text() != dwasfile_content
