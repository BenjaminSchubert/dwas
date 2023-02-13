from .mixins import BaseFormatterTest


class TestIsort(BaseFormatterTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import isort

register_managed_step(isort())
register_managed_step(
    isort(additional_arguments=["--atomic"]),
    name="isort:fix",
    run_by_default=False,
)
"""
    autofix_step = "isort:fix"
    invalid_file = """\
from pathlib import Path
import os
"""
    valid_file = """\
import os
from pathlib import Path
"""
