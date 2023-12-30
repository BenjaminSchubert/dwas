import pytest

from .mixins import BaseLinterWithAutofixTest


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

    @pytest.mark.skip("docformatter does not support colored output")
    def test_respects_color_settings(self):
        pass  # pragma: nocover
