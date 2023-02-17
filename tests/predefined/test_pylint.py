import sys

import pytest

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

    @pytest.mark.parametrize(
        "enable_colors",
        [
            pytest.param(
                True,
                marks=[
                    pytest.mark.xfail(
                        sys.platform == "win32",
                        reason="colors are not supported on windows",
                        strict=True,
                    )
                ],
            ),
            False,
        ],
        ids=["colors", "no-colors"],
    )
    def test_respects_color_settings(self, cache_path, enable_colors):
        super().test_respects_color_settings(cache_path, enable_colors)
