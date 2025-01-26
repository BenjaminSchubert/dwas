# pylint: disable=invalid-name

# TODO: validate defaults values documented from predefined classes's defaults
# TODO: can we automate the generation of the 'defaults' values for our methods?
# TODO: validate code blocks, especially examples

import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path

from jinja2.filters import FILTERS

DOCS_PATH = Path(__file__).parent
EXTENSIONS_PATH = DOCS_PATH / "_extensions"
SRC_PATH = DOCS_PATH.parent.joinpath("src")

sys.path.append(str(EXTENSIONS_PATH))


##
# Project Metadata
##
_project_metadata = metadata.metadata("dwas")
project = _project_metadata["Name"]
release = _project_metadata["Version"]
author = _project_metadata["Author-email"]
# pylint: disable=redefined-builtin
copyright = "2022, Benjamin Schubert"  # noqa: A001

html_context = {
    "github_user": "BenjaminSchubert",
    "github_repo": "dwas",
    "github_version": "main",
    "conf_py_path": "/docs/",
}
rtd_version_type = os.getenv("READTHEDOCS_VERSION_TYPE")
if rtd_version_type == "external":
    # Likely a PR build, link to the commit directly
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.strip()
    html_context["github_version"] = commit
elif rtd_version_type == "tag":
    html_context["github_version"] = os.environ["READTHEDOCS_VERSION_NAME"]


##
# Global configuration
##
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    # TODO: get rid of this once we tackled all the todos
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinxcontrib.spelling",
    # Internal extensions
    "cleanup_signatures",
    "execute",
]

# Where to store our custom templates
templates_path = ["_templates"]
# Those are not source files
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Warn about everything
nitpicky = True
nitpick_ignore = [
    ("py:class", "dwas._steps.parametrize.T"),
    ("py:class", "dwas._steps.handlers.StepHandler"),
]
suppress_warnings = [
    # See https://github.com/sphinx-doc/sphinx/issues/12589
    "autosummary.import_cycle",
]

linkcheck_ignore = [
    "https://pypi.org/project/dwas/#history",
]

# Theme options
html_theme = "furo"
highlight_language = "python3"
pygments_style = "styles.AnsiDefaultStyle"
pygments_dark_style = "styles.AnsiMonokaiStyle"

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

# Extlinks
extlinks = {
    "repofile": (
        "https://github.com/{github_user}/{github_repo}/tree/{github_version}/%s".format(
            **html_context
        ),
        "repo %s",
    ),
}
extlinks_detect_hardcoded_links = True

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
.. _coverage.py: https://coverage.readthedocs.io/en/latest/
.. _docformatter: https://github.com/PyCQA/docformatter/
.. _mypy: https://mypy.readthedocs.io/en/stable/
.. _pylint: https://pylint.pycqa.org/en/latest/
.. _pytest: https://docs.pytest.org/en/stable/
.. _ruff: https://docs.astral.sh/ruff/
.. _sphinx:  https://www.sphinx-doc.org/
.. _twine: https://twine.readthedocs.io/en/stable/
.. _the Unimport formatter: https://unimport.hakancelik.dev/
.. _the manylinux project: https://github.com/pypa/manylinux
.. _github actions: https://github.com/features/actions
.. _pipx: https://pipx.pypa.io/stable/
.. _PyPI: https://pypi.org/project/dwas/
.. _tox: https://tox.wiki/
.. _nox: https://nox.thea.codes/
.. _Invoke: https://www.pyinvoke.org/
.. _own dwasfile.py: https://github.com/BenjaminSchubert/dwas/blob/main/dwasfile.py
"""

# Spelling config
spelling_show_suggestions = True
spelling_word_list_filename = str(DOCS_PATH / "_spelling_allowlist.txt")


##
# Custom jinja filters
##
# NOTE: sphinx doesn't allow us adding filters in a standard way, so we
#       modify the global environment here
def module_path(module: str) -> str:
    path = SRC_PATH / module.replace(".", "/")
    if path.is_dir():
        path = path / "__init__.py"

    assert path.exists()
    return str(path.relative_to(SRC_PATH.parent))


FILTERS["module_path"] = module_path
