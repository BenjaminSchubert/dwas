import json
import sys
from pathlib import Path

import pytest

from .._utils import cli, using_project
from .mixins import BaseStepTest


@using_project("predefined/examples/package")
class TestPackage(BaseStepTest):
    @pytest.fixture
    def expected_output(self):
        return "it worked!"

    def test_exposes_sdists_and_wheels(self, cache_path):
        cli(cache_path=cache_path, steps=["output_artifacts"])
        artifacts = json.loads(Path("artifacts.json").read_text("utf-8"))
        assert list(artifacts.keys()) == ["sdists", "wheels"]
        assert Path(artifacts["sdists"][0]).name == "test-package-0.0.0.tar.gz"
        assert (
            Path(artifacts["wheels"][0]).name
            == "test_package-0.0.0-py3-none-any.whl"
        )

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
