import sys

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

    @pytest.mark.parametrize(
        "valid",
        (
            pytest.param(
                True,
                id="valid-project",
                marks=pytest.mark.xfail(
                    sys.version_info >= (3, 14),
                    reason="docformatter does not support python3.14 yet",
                    strict=True,
                ),
            ),
            pytest.param(False, id="invalid-project"),
        ),
    )
    def test_simple_behavior(self, cache_path, tmp_path, valid):
        return super().test_simple_behavior(cache_path, tmp_path, valid)

    @pytest.mark.xfail(
        sys.version_info >= (3, 14),
        reason="docformatter does not support python3.14 yet",
        strict=True,
    )
    def test_can_apply_fixes(self, cache_path, tmp_path):
        return super().test_can_apply_fixes(cache_path, tmp_path)
