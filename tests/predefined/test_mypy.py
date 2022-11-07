from .mixins import BaseLinterTest


class TestMypy(BaseLinterTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import mypy

register_managed_step(mypy(files=["src/token.py"]))
"""
    invalid_file = """\
def test() -> str:
    return 2
"""
    valid_file = '"""This is a token file"""\n'
