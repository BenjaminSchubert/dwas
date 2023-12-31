from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.ext.autodoc import Options


# ruff: noqa: ARG001
def cleanup_signatures(  # pylint: disable=unused-argument
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: Options,
    signature: str | None,
    return_annotation: str | None,
) -> tuple[str, str | None] | None:
    if name == "dwas.StepRunner":
        # Hide the __init__ signature for dwas.StepRunner, it's meant to be
        # private
        return ("()", return_annotation)
    return None


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect("autodoc-process-signature", cleanup_signatures)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
