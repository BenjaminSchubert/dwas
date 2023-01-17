Installation
============

``dwas`` requires a python interpreter to run. It support python 3.9 or higher.

There are multiple ways of installing ``dwas``. If you have a preferred method of
installing python cli packages, you can obviously stick to it, otherwise, some
ways are described below.

.. note::

    Currently, ``dwas`` is not published on `Pypi`_, and thus needs to be
    installed from the repository.


Via pipx
--------

If you want to install to install ``dwas`` in an entirely isolated environment,
you can use `pipx`_. See `it's documentation <pipx_>`_ for how to install it on
your system.

Once you have pipx installed, you can install ``dwas`` like:

.. code-block:: shell

    pipx install git+https://github.com/BenjaminSchubert/dwas.git@main


Via pip
-------

If you do not wish to use pipx, or if you prefer to install it globally for
your user, or even in a virtual environment, you can then install it via pip:

.. code-block:: shell

    # Here PYTHON_VERSION is the version for which you want to install ``dwas``.
    # Remember that it needs at least python3.9. In a virtual environment, using
    # `python` should be enough.
    python${PYTHON_VERSION} -m pip install git+https://github.com/BenjaminSchubert/dwas.git@main
