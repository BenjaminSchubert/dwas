import pytest

from .._utils import using_project
from .mixins import BaseStepTest


@using_project("predefined/examples/coverage")
class TestCoverage(BaseStepTest):
    @pytest.fixture
    def expected_output(self):
        return "100%"
