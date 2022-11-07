import pytest

from .._utils import using_project
from .mixins import BaseStepTest


@using_project("predefined/examples/twine")
class TestTwine(BaseStepTest):
    @pytest.fixture
    def expected_output(self):
        return "Checking"
