.. image:: https://readthedocs.org/projects/dwas/badge/?version=latest
   :target: https://dwas.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/BenjaminSchubert/dwas/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/BenjaminSchubert/dwas/actions/workflows/ci.yml
   :alt: checks badge

.. image:: https://codecov.io/gh/BenjaminSchubert/dwas/branch/main/graph/badge.svg?token=OK872YRU0H
   :target: https://codecov.io/gh/BenjaminSchubert/dwas

.. image:: https://img.shields.io/pypi/v/dwas?style=flat-square
  :target: https://pypi.org/project/dwas/#history
  :alt: Latest version on PyPI

.. image:: https://img.shields.io/pypi/pyversions/dwas?style=flat-square
  :alt: PyPI - Python Version

.. image:: https://img.shields.io/pypi/dm/dwas?style=flat-square
  :target: https://pypistats.org/packages/dwas
  :alt: PyPI - Downloads

.. image:: https://img.shields.io/pypi/l/dwas?style=flat-square
  :target: https://opensource.org/licenses/MIT
  :alt: PyPI - License

.. image:: https://img.shields.io/github/issues/BenjaminSchubert/dwas?style=flat-square
  :target: https://github.com/BenjaminSchubert/dwas/issues
  :alt: Open issues

.. image:: https://img.shields.io/github/issues-pr/BenjaminSchubert/dwas?style=flat-square
  :target: https://github.com/BenjaminSchubert/dwas/pulls
  :alt: Open pull requests

.. image:: https://img.shields.io/github/stars/BenjaminSchubert/dwas?style=flat-square
  :target: https://pypistats.org/packages/dwas
  :alt: Package popularity


Development Workflow ASsistant
==============================

**Flexible developer workflow automation CLI in Python**

``dwas`` takes inspiration from `tox <https://tox.wiki/>`_,
`nox <https://nox.thea.codes/>`_ and `Invoke <https://www.pyinvoke.org/>`_ and
aims to delivers a middle ground, the builtin isolation of tox, together with
the scriptability of nox and the extensibility of Invoke, mixed with dependency
management and provided common use cases.

If ``dwas`` does not satisfy your use case, maybe one of those will?

⚠️ This project is currently in early development. Contributions and issues are
very welcome but compatibility may be broken at any point.


Getting Started
---------------

`A more detailed documentation <https://dwas.readthedocs.io/en/latest/>`_ is
available.


Installation
************

Currently, ``dwas`` is not published on `Pypi <https://pypi.org/>`_ and needs to
be installed from the repository. With pip, you can do the following:

.. code-block:: shell

   # Here PYTHON_VERSION is the version for which you want to install ``dwas``.
   # Remember that it needs at least python3.9. In a virtual environment, using
   # `python` should be enough.
   python${PYTHON_VERSION} -m pip install git+https://github.com/BenjaminSchubert/dwas.git@main

For more information and explanation, please see
`our docs <https://dwas.readthedocs.io/en/latest/installation.html>`__


Running dwas
************

Once installed, you can run ``dwas`` on any project with a ``dwasfile.py`` in
it.

For example, to run all default steps:

.. code-block:: shell

   dwas

Or, to list all the steps available:

.. code-block:: shell

   dwas --list

For more information on how to get started, please see
`our docs <https://dwas.readthedocs.io/en/latest/getting_started.html>`__
