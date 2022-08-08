# pylint: disable=invalid-name

# TODO: validate defaults values documented from predefined classes's defaults
# TODO: can we automate the generation of the 'defaults' values for our methods?
# TODO: validate code blocks, especially examples

import sys
from importlib import metadata
from pathlib import Path

DOCS_PATH = Path(__file__).parent
EXTENSIONS_PATH = DOCS_PATH / "_extensions"

sys.path.append(str(EXTENSIONS_PATH))

##
# Project Metadata
##
_project_metadata = metadata.metadata("dwas")
project = _project_metadata["Name"]
release = _project_metadata["Version"]
author = _project_metadata["Author-email"]
# pylint: disable=redefined-builtin
copyright = "2022, Benjamin Schubert"

##
# Global configuration
##
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    # TODO: get rid of this once we tackled all the todos
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinxcontrib.spelling",
]

# Where to store our custom templates
templates_path = ["_templates"]
# Those are not source files
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Warn about everything
nitpicky = True
nitpick_ignore = [
    ("py:class", "dwas._steps.parametrize.T"),
]

# Theme options
html_theme = "furo"
highlight_language = "python3"
pygments_style = "sphinx"
pygments_dark_style = "monokai"

# Autosummary configuration
autosummary_ignore_module_all = False
autosummary_imported_members = True
autosummary_generate = True
autodoc_default_options = {
    "autoclass_content": "class",
    "exclude-members": "__weakref__, __subclasshook__, __init__, __str__",
    "ignore-module-all": False,
    "members": True,
    "show-inheritance": True,
    "special-members": True,
}

# Intersphinx config
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# Customisation for the rst that gets generated
# Add here things that need to be reused between files
rst_prolog = """
.. role:: python(code)
    :language: python
"""

rst_epilog = """
.. _submit an issue: https://github.com/BenjaminSchubert/dwas/issues/new
.. _the Black formatter: https://black.readthedocs.io/en/stable/
.. _the isort formatter: https://pycqa.github.io/isort/
.. _coverage.py: https://coverage.readthedocs.io/en/stable/
.. _mypy: https://mypy.readthedocs.io/en/stable/
.. _pylint: https://pylint.pycqa.org/en/latest/
.. _pytest: https://docs.pytest.org/en/stable/
.. _sphinx:  https://www.sphinx-doc.org/
.. _twine: https://twine.readthedocs.io/en/stable/
.. _the manylinux project: https://github.com/pypa/manylinux
.. _github actions: https://github.com/features/actions
"""

# Spelling config
spelling_show_suggestions = True
spelling_word_list_filename = str(DOCS_PATH / "_spelling_allowlist.txt")
