import pytest

from .._utils import using_project
from .mixins import BaseStepTest


@using_project("predefined/examples/pytest")
class TestPytest(BaseStepTest):
    @pytest.fixture
    def expected_output(self):
        return "1 passed"
