import json
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
        assert Path(artifacts["sdists"][0]).name == "test_package-0.0.0.tar.gz"
        assert (
            Path(artifacts["wheels"][0]).name
            == "test_package-0.0.0-py3-none-any.whl"
        )

    def test_updates_package_on_rerun(self, tmp_path, cache_path):
        res = cli(cache_path=cache_path, steps=["check_install"])
        assert res.stdout.strip().splitlines()[-1] == "it worked!"

        tmp_path.joinpath("src/test_project/__main__.py").write_text("""\
if __name__ == "__main__":
    print("it changed!")
""")

        res = cli(cache_path=cache_path, steps=["check_install"])
        assert res.stdout.strip().splitlines()[-1] == "it changed!"

    @pytest.mark.skip(reason="uv only outputs data on stderr")
    def test_respects_color_settings(self, cache_path, enable_colors):
        pass
