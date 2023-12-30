from typing import Any, Dict, Optional, Tuple

from sphinx.application import Sphinx
from sphinx.ext.autodoc import Options


# ruff: noqa: ARG001
def cleanup_signatures(  # pylint: disable=unused-argument
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: Options,
    signature: Optional[str],
    return_annotation: Optional[str],
) -> Optional[Tuple[str, Optional[str]]]:
    if name == "dwas.StepRunner":
        # Hide the __init__ signature for dwas.StepRunner, it's meant to be
        # private
        return ("()", return_annotation)
    return None


def setup(app: Sphinx) -> Dict[str, Any]:
    app.connect("autodoc-process-signature", cleanup_signatures)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
