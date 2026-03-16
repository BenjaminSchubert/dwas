Changelog
=========


0.0.8
-----

Features
^^^^^^^^

- Add support to set environment variables on a runner. This can be useful for
  steps with dependents to inject some information into their dependents.


0.0.7
-----

Bug fixes
^^^^^^^^^

- Fix the calling of ``uv`` when it is not installed next to the python interpreter.
  For user-site installation, it was failing to find it.


0.0.6
-----

The project is now marked as alpha instead of pre-alpha, it's been used for a
while and is relatively stable.

Breaking Changes
^^^^^^^^^^^^^^^^

- Use ``uv build`` instead of ``python -m build`` in the
  `package <https://dwas.readthedocs.io/en/latest/api/dwas.predefined.html#dwas.predefined.package>`_
  step, for faster runs.
  This will require registering the step as ``dwas.step()`` instead of
  ``dwas.managed_step()`` if you don't need custom dependencies.

Features
^^^^^^^^

- Add support for python3.14
- Allow installing dependencies from a lock file using
  `uv sync <https://dwas.readthedocs.io/en/latest/api/dwas.html#dwas.StepRunner.install>`_

Bug fixes
^^^^^^^^^

- Fix the scheduler to not fail in some cases where multiple steps depended on
  the same one that failed

Miscellaneous
^^^^^^^^^^^^^

- Use uv instead of pip and virtualenv to setup the environments. This provides
  faster setup for each step.


0.0.5
-----

Features
^^^^^^^^

- Official support for python 3.13
- Automatically detect and enable colors on GitLab CI


0.0.4
-----

Features
^^^^^^^^

- Official support python3.12
- Provide a `ruff <https://dwas.readthedocs.io/en/latest/api/dwas.predefined.html#dwas.predefined.ruff>`_
  predefined step

Bug fixes
^^^^^^^^^

- The logs directory will not be removed automatically if it's been specified.
  This is to avoid removing user directories which might contain other files.
- Now support newer docformatter versions which return non-zero exit codes when
  files are changed.


0.0.3
-----

This release focuses on compatibility and user experience.

The highlights are:

- A new interactive frontend for a nicer feedback when using ``dwas`` on the cli
- Wider support for various python version. Added 3.8 support and other
  interpreters
- Support for MacOS

Features
^^^^^^^^

- Store logs into files to allow inspecting after the run. Additionally, those
  will always have debug information in them
- Added support for python 3.8
- Added support pypy and other python implementations
- Added official support for MacOS
- Support running ``dwas`` like ``python -m dwas``
- Allow passing a ``cwd`` argument to ``step.run``

Miscellaneous
^^^^^^^^^^^^^

- Stop showing times at the millisecond precision, it's too verbose
- ``dwas`` now uses ``virtualenv`` instead of ``venv`` for creating the
  environments, which broadens the support for various python interpreters.
  If ``virtualenv`` supports it, ``dwas`` will


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
