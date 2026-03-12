import pytest

from .mixins import BaseLinterWithAutofixTest


class TestRuffCheck(BaseLinterWithAutofixTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import ruff

register_managed_step(ruff())
register_managed_step(
    ruff(additional_arguments=["check", "--fix"]),
    name="ruff:fix",
    run_by_default=False,
)
"""
    invalid_file = """\
from pathlib import Path
import os
"""
    valid_file = '"""This is a token file"""\n'
    autofix_step = "ruff:fix"

    expected_valid_output = "All checks passed!"
    expected_invalid_output = "Remove unused import: `pathlib.Path`"


class TestRuffFormat(BaseLinterWithAutofixTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import ruff

register_managed_step(ruff(additional_arguments=["format", "--diff"]))
register_managed_step(
    ruff(additional_arguments=["format"]),
    name="ruff:fix",
    run_by_default=False,
)
"""
    autofix_step = "ruff:fix"
    invalid_file = "x =  1"
    valid_file = "x = 1\n"

    expected_stream = "stderr"
    expected_valid_output = "2 files already formatted"
    expected_invalid_output = "1 file would be reformatted"

    @pytest.mark.skip("ruff format does not support colored output")
    def test_respects_color_settings(self):
        pass  # pragma: nocover
