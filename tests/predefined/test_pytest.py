import pytest

from .._utils import cli, using_project
from .mixins import BaseStepTest


@using_project("predefined/examples/pytest")
class TestPytest(BaseStepTest):
    @pytest.fixture
    def expected_output(self):
        return "1 passed"

    def test_can_pass_parameters(self, cache_path):
        result = cli(
            cache_path=cache_path,
            steps=["pytest", "--", "--collect-only"],
        )
        assert "1 test collected" in result.stdout
