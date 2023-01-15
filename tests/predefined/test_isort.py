import pytest

from .mixins import BaseFormatterTest


class TestIsort(BaseFormatterTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import isort

register_managed_step(isort())
register_managed_step(
    isort(additional_arguments=["--atomic"]),
    name="isort:fix",
    run_by_default=False,
)
"""
    autofix_step = "isort:fix"
    invalid_file = """\
from pathlib import Path
import os
"""
    valid_file = """\
import os
from pathlib import Path
"""

    @pytest.mark.parametrize(
        "enable_colors",
        [
            True,
            pytest.param(
                False,
                marks=pytest.mark.xfail(
                    reason="isort adds a trailing RESET code at the end if colorama is installed",
                ),
            ),
        ],
        ids=["colors", "no-colors"],
    )
    def test_respects_color_settings(
        self, cache_path, tmp_path, enable_colors
    ):
        super().test_respects_color_settings(
            cache_path, tmp_path, enable_colors
        )
