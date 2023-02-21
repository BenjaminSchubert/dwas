Installation
============

``dwas`` requires a python interpreter to run. It support python 3.9 or higher.

There are multiple ways of installing ``dwas``. If you have a preferred method of
installing python cli packages, you can obviously stick to it, otherwise, some
ways are described below.

You can find ``dwas`` on `PyPI`_.

Via pipx
--------

If you want to install to install ``dwas`` in an entirely isolated environment,
you can use `pipx`_. See `it's documentation <pipx_>`_ for how to install it on
your system.

Once you have pipx installed, you can install ``dwas`` like:

.. code-block:: shell

    pipx install dwas


Via pip
-------

If you do not wish to use pipx, or if you prefer to install it globally for
your user, or even in a virtual environment, you can then install it via pip:

.. code-block:: shell

    # Here PYTHON_VERSION is the version for which you want to install ``dwas``.
    # Remember that it needs at least python3.8. In a virtual environment, using
    # `python` should be enough.
    python${PYTHON_VERSION} -m pip install dwas


Installing an unreleased version
--------------------------------

If you want to install an unreleased version of ``dwas``, you can install it
from the repository:

.. code-block:: shell

    git clone https://github.com/BenjaminSchubert/dwas
    # Remove the -e if you don't want to install it in editable mode.
    pip install -e dwas/
