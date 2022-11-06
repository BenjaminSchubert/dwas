"""
This module contains predefined steps that are provided in order to help reduce
duplication.

.. note::

    If you think a predefined solution should be provided for a particular
    utility, please `submit an issue`_, or contribute!

.. attention::

    All predefined steps here have safe defaults, and will not modify any
    source code unless told so. Please make sure you understand the underlying
    tools when configuring them.
"""

from ._black import black
from ._coverage import coverage
from ._docformatter import docformatter
from ._isort import isort
from ._mypy import mypy
from ._package import package
from ._pylint import pylint
from ._pytest import pytest
from ._sphinx import sphinx
from ._twine import twine
from ._unimport import unimport

__all__ = [
    "black",
    "coverage",
    "docformatter",
    "isort",
    "mypy",
    "package",
    "pylint",
    "pytest",
    "sphinx",
    "twine",
    "unimport",
]
