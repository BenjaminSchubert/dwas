import pytest

from .._utils import using_project
from .mixins import BaseStepTest


@using_project("predefined/examples/sphinx")
class TestPackage(BaseStepTest):
    @pytest.fixture
    def expected_output(self):
        return "The HTML pages are in"
