from .mixins import BaseLinterTest


class TestPylint(BaseLinterTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import pylint

register_managed_step(pylint(files=["src/token.py"]))
"""
    invalid_file = """\
from pathlib import Path
import os
"""
    valid_file = '"""This is a token file"""\n'
