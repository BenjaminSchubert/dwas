import sys

import pytest

from .mixins import BaseLinterWithAutofixTest


@pytest.mark.xfail(
    sys.version_info >= (3, 14),
    reason="docformatter does not support python3.14 yet",
    strict=True,
)
class TestDocformatter(BaseLinterWithAutofixTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import docformatter

register_managed_step(docformatter())
register_managed_step(
    docformatter(
        additional_arguments=["--recursive", "--in-place"],
        expected_status_codes=[0, 3],
    ),
    name="docformatter:fix",
    run_by_default=False,
)
"""
    autofix_step = "docformatter:fix"
    invalid_file = '"""   Here are some examples."""'
    valid_file = '"""Here are some examples."""'

    expected_valid_output = ""
    expected_invalid_output = "--- before/./src/token.py"

    @pytest.mark.skip("docformatter does not support colored output")
    def test_respects_color_settings(self):
        pass  # pragma: nocover
