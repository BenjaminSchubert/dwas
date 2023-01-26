Using the CLI
=============

The CLI of ``dwas`` is the main interface with which you would normally interact.
Using it efficiently is key, and we aim to make it as natural and easy to use
as possible.

Here we will be focusing on explaining some parts of it that might not be as
easy to discover as we would like.

.. note::

    The output from the cli examples can be reproduces by running it in the
    :repofile:`docs/examples/cli <docs/examples/cli/>` directory.

But first, this is the full help for reference:


.. command-output:: dwas --help


Getting to know a project
-------------------------

When working on a new project, you often need to understand what testing setup
or documentation building exist for this project.

``dwas`` makes this easy. In order to know what automation is available for a
project, you can run:

.. command-output:: dwas --list
    :cwd: examples/cli/

You can also know which steps run in which order:

.. command-output:: dwas --list-dependencies
    :cwd: examples/cli/

It is also possible to get more information on each step, providing the project
did add a description. For this, use a more verbose mode:

.. command-output:: dwas --list --verbose
    :cwd: examples/cli/


Controlling steps execution more closely
----------------------------------------

You might sometimes want to control more explicitly which steps run or not, or
even some part of steps.

``dwas`` offer multiple ways of getting more control:

#. Preventing some steps to run using ``--except <step>``
#. Running only some specific steps using ``--only``
#. Only running the setup part of each step using ``--setup-only``
#. Skipping the setup part of each step, with ``--no-setup``
#. Aborting upon the first failure ``--fail-fast``

--except <step>
****************

For example, you might be working on writing tests, and the sources of your
project are not changing, at which point, you might not want to re-run the
packaging step. This is where ``--except`` is useful

.. code-block:: shell-session

    dwas --exclude package pytest[3.10]

--only
******

If you want to run a single (or multiple) step(s) explicitly, without any
previous one, you can use ``--only``:

.. code-block:: shell-session

    dwas --only pytest[3.9] pytest[3.10]

--setup-only
************

If you want to just run the setup phase of your steps (e.g. to create the
virtual environments and install dependencies, without running anything else),
you can use ``--setup-only``

.. code-block:: shell-session

    dwas --setup-only pytest

--no-setup
**********

This is the corollary to ``--setup-only``, and allows you to skip the setup
phase. This can be useful if you know your environments are already correct,
and you want your steps to run faster.

.. note:: dependent setup from previous step always run when using ``--no-setup``

.. code-block:: shell-session

    dwas --no-setup pytest


--fail-fast
***********

In the cases you don't want to wait when you get an error, and just want to fix
it as soon as possible, you can use ``--fail-fast``, which will abort a run at
the first issue.

.. code-block:: shell-session

    dwas --fail-fast pytest
