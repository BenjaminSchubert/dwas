import sys

import pytest

from .._utils import using_project
from .mixins import BaseStepTest


@using_project("predefined/examples/twine")
class TestTwine(BaseStepTest):
    @pytest.fixture
    def expected_output(self):
        return "Checking"

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
