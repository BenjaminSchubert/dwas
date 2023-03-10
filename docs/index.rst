.. todo::
    - Add tutorials for:
        - parametrizing entries
        - making simple steps
        - making reusable steps

dwas - easier developer workflow
================================

``dwas`` aims to reduce the complexity in working on foreign projects while
being powerful enough for developers working day in day out on the same project.

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

.. image:: https://img.shields.io/github/stars/BenjaminSchubert/dwas?style=flat-square
  :target: https://pypistats.org/packages/dwas
  :alt: Package popularity

.. image:: https://github.com/BenjaminSchubert/dwas/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/BenjaminSchubert/dwas/actions/workflows/ci.yml
   :alt: checks badge

.. image:: https://codecov.io/gh/BenjaminSchubert/dwas/branch/main/graph/badge.svg?token=OK872YRU0H
   :target: https://codecov.io/gh/BenjaminSchubert/dwas

.. image:: https://img.shields.io/github/issues/BenjaminSchubert/dwas?style=flat-square
  :target: https://github.com/BenjaminSchubert/dwas/issues
  :alt: Open issues

.. image:: https://img.shields.io/github/issues-pr/BenjaminSchubert/dwas?style=flat-square
  :target: https://github.com/BenjaminSchubert/dwas/pulls
  :alt: Open pull requests


Working on any project should be friction-less, it should be easy to run tests,
formatters, linters, build documentation, etc, from a single CLI that is
discoverable and easy to use, while being powerful enough for power users.

``dwas`` aims to provide all of this and while making environments more
reproducible and isolated, without forcing the use of a containerization
environment for this.

.. note::
    Currently, ``dwas`` is very focused on python, but there are aims to make it
    more generic and useful for other languages, or projects that do not need
    virtual environments.


Getting started
---------------

.. include this to have it referenced in the main search bar, without displaying
   the full toctree with caption.
.. toctree::
    :hidden:
    :caption: Introduction

    installation.rst
    getting_started.rst
    cli.rst


If you are new to ``dwas``, the following documentations would be the best place
to start, it will get you up and running:

- :doc:`installation`
- :doc:`getting_started`
- :doc:`cli`

And the :doc:`glossary` might be useful if you have terms that you do not
understand in the current context.


Getting in touch
****************

Encountering issues with ``dwas``? Found a bug? Have suggestions for
improvements? Please feel free to get in touch and `submit an issue`_ or add
your point of view or additional information on an existing one if relevant.

Want to contribute? Please see :doc:`our contributing guide <contributing>`.


Public API
----------

Once you have installed ``dwas``, and if you want to write your own
``dwasfile.py``, this is the public API that is provided:

.. autosummary::
    :toctree: api/
    :caption: Public API
    :template: autosummary/public_api.rst

    dwas
    dwas.predefined

Other resources
---------------

``dwas`` exists in a rich ecosystem, with plenty of high quality tools
available. If ``dwas`` does not fit exactly your needs, maybe one of the
following ones might. They were all influential with regards to ``dwas``
design:

- `tox`_, is a generic virtual environment management and test command line tool
  that is highly tailored for python project development. It is very similar to
  ``dwas`` and provides good isolation of environments. However, it relies on
  configuration and not code to describe environments and does not handle some
  constructs that ``dwas`` provides, like automatically running dependencies of
  environments (or, as ``dwas`` calls them, steps).

- `nox`_ is similar in spirit to both ``dwas`` and ``tox``, and, like ``dwas``,
  it relies on a python file to configure environments. It however does not
  provide as good isolation by default as ``dwas`` does, and does not handle
  parallel tasks as well.

- `Invoke`_ is a more general-purpose task execution library, and is more
  similar to ``Make`` in that regard. It however, does not provide any
  predefined tasks, specific to some workflows, like ``dwas`` does.


.. include this to have it referenced in the main search bar:
.. toctree::
    :caption: Appendix
    :hidden:

    changelog.rst
    contributing.rst
    glossary.rst
    genindex.rst
