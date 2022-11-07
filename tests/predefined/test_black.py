from .mixins import BaseFormatterTest


class TestBlack(BaseFormatterTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import black

register_managed_step(black())
register_managed_step(
    black(additional_arguments=[]),
    name="black:fix",
    run_by_default=False,
)
"""
    autofix_step = "black:fix"
    invalid_file = "x =  1"
    valid_file = "x = 1\n"
