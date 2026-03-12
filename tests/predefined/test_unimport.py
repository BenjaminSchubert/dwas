from .mixins import BaseLinterWithAutofixTest


class TestUnimport(BaseLinterWithAutofixTest):
    dwasfile = """\
from dwas import register_managed_step
from dwas.predefined import unimport

register_managed_step(unimport())
register_managed_step(
    unimport(additional_arguments=["--diff", "--remove", "--check"]),
    name="unimport:fix",
    run_by_default=False,
)
"""

    autofix_step = "unimport:fix"
    invalid_file = "import os"
    valid_file = ""

    expected_valid_output = (
        "Congratulations there is no unused import in your project"
    )
    expected_invalid_output = "-import os"
