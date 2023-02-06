Changelog
=========

0.0.2
-----

This release focuses heavily on the CLI and how to interact with it. It's been
reworked and some breaking changes where made there, to make it more intuitive.

You can see how to use the new CLI in
`the docs <https://dwas.readthedocs.io/en/latest/cli.html>`_

Breaking Changes
^^^^^^^^^^^^^^^^

- Rework the cli to avoid having to use ``--step1``. You can now use
  ``dwas <step>`` directly
- ``--except`` now ensure that the step exists, and fails otherwise, to help
  find erroneous cli calls.
- Make ``-only`` and ``--exclude`` expand step groups to their dependencies, as
  this is more natural and expected.

Features
^^^^^^^^

- Allow passing arguments to steps
- Allow passing additional arguments through the environment variable
  ``DWAS_ADDOPTS``
- Add documentation for the CLI
- Update install guide to  recommend installing from PyPI directly

Bug Fixes
^^^^^^^^^

- Ensure dwas supports keyboard interrupts gracefully
- Fix the graph resolution to correctly keeps dependencies when intermixing
  ``--only`` and ``--except``


0.0.1
-----

Initial release for ``dwas`` with the basics to automate workflows.

Features
^^^^^^^^

The following predefined steps are available:

- black
- coverage
- docformatter
- isort
- mypy
- package (to build a PEP517 compliant package)
- pylint
- pytest
- sphinx
- twine
- unimport
