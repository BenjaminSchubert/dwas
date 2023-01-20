.. TODO::
    move the code examples into another directory and show some of their output.


Getting Started
===============

With ``dwas`` :doc:`installed <installation>`, the next question is now, how do
you configure and use it?

To get started, you need a ``dwasfile.py`` at the root of your project. This
guide will help you through writing your first file.

In this example, we will guide you through writing a ``dwasfile.py`` that runs
``pytest`` against your project.

We will increase the complexity of the setup as we go, to show some of the
constructs that ``dwas`` offers. For a complete example, you can always have a
look at ``dwas``' `own dwasfile.py`_.


1. Running pytest with the current python version
-------------------------------------------------

We will now define a :term:`step` that runs ``pytest``:

.. code-block:: python
    :linenos:

    # The first thing is to import dwas, which will make available all the
    # public API.
    import dwas

    # This registers the step and makes it available to dwas.
    # Additionally, it tells dwas that it requires dependencies, and list the
    # ones that need to be installed.
    #
    # Note that if no dependency was required, you could have used
    # `@dwas.step()` instead.
    @dwas.managed_step(dependencies=["pytest"])
    # This defined the actual step, for dwas, a step is simply a function (or
    # a callable class)
    def pytest(step: dwas.StepRunner) -> None:
        step.run(["pytest"])

And this is enough to run ``pytest`` in the current directory.

You can see now that dwas recognizes this step and that it would run by default:

.. code-block:: shell

    dwas --list

And you can obviously run the step itself:

.. code-block:: shell

    dwas
    # Or, if you want to run this specific step:
    dwas pytest


2. Running against multiple python versions (parametrization)
-------------------------------------------------------------

While the first example is already useful, we often want to run pytest against
multiple versions of python, to ensure our programs is compatible.

We will show here how to do it, leveraging another construct of ``dwas``,
namely parametrization of steps.

In this example, we will run against python 3.8 to 3.11:

.. code-block:: python
    :linenos:

    import dwas

    # As before, we register the step
    @dwas.managed_step(dependencies=["pytest"])
    # We now leverage a second decorator, to parametrize the step such that
    # it runs against
    # Note that the order of both decorators does not matter.
    @dwas.parametrize("python", ["3.8", "3.9", "3.10", "3.11"])
    # And as before, our method calling pytest
    def pytest(step: dwas.StepRunner) -> None:
        step.run(["pytest"])

And as before, you can see the resulting steps by running:

.. code-block:: shell

    dwas --list

You can note this time, that we have 5 steps defined, a ``pytest`` one, that,
when referenced, will run all pytest steps, and 4 steps like ``pytest[version]``,
which can be used to reference each individual steps.

Now try running some of them:

.. code-block:: shell

    # Runs all steps, by default
    dwas
    # Runs pytest and all it's dependencies
    dwas pytest
    # Run only against python3.11
    dwas pytest[3.11]


3. Using predefined (provided) step generators
----------------------------------------------

While being able to write all your steps manually is great, if you have many
different projects, it can be tedious to write the same code every time. For
this, ``dwas`` provides some predefined, commonly used steps. Other packages
can provide some too if wanted.

Here, we will see how to use the ``pytest`` step provided by ``dwas`` itself:

.. code-block:: python
    :linenos:

    import dwas
    # New import, all predefined steps by dwas
    import dwas.predefined

    # Since we do not defined a method, we use `register_managed_step` instead
    # here. It is functionally the same, but slightly nicer on reading.
    dwas.register_managed_step(
        # Here, we parametrize again the pytest step to run against all versions
        dwas.parametrize("python", ["3.8", "3.9", "3.10", "3.11"])(
            # And here, we add the predefined step for pytest
            dwas.predefined.pytest(),
        ),
        dependencies=["pytest"],
    )

Which is functionally almost equivalent to the previous ``pytest`` step we have
defined, though this step has more functionality. See
:py:func:`dwas.predefined.pytest` for the full documentation about this step.


4. Dependencies between steps
-----------------------------

.. TODO::

    Provide an example project to clone for this, it's too much for users to
    write on their own

While all the previous examples focused on a single step, there is often cases
where you might want to have dependencies between them, for example, to avoid
doing some work multiple times, or to gather data from multiple steps.

In this example. we will show how to easily:

- Build a source distribution and wheel for your current python package
- Run pytest with multiple versions of python against it
- Give coverage report for all the tests.

This assumes you have such a project handy. If you don't, you can follow
looking at ``dwas``' `own dwasfile.py`_.

.. code-block:: python
    :linenos:

    import dwas
    import dwas.predefined

    # A new step, this one builds the current package, and, when declared as
    # a dependency of another step, will install it in the virtual environment
    # of the dependent, before it runs.
    dwas.register_managed_step(dwas.predefined.package())

    # Our well known pytest step, note the new `requires` config!
    dwas.register_managed_step(
        # Here, we parametrize again the pytest step to run against all versions
        dwas.parametrize("python", ["3.8", "3.9", "3.10", "3.11"])(
            # And here, we add the predefined step for pytest
            dwas.predefined.pytest(),
        ),
        dependencies=["pytest"],
        # Declare the dependency on the previous step, this ensures that the
        # package will be installed before we run tests.
        requires=["package"],
    )

    # And finally coverage reports for all our tests
    dwas.register_managed_step(
        dwas.predefined.coverage(),
        requires=["pytest"],
        dependencies=["coverage"],
    )


If you now try to list steps, you should this time see quite a few more:

.. code-block:: shell

    dwas --list


Next Steps
----------

Once you have understood the concepts here, the next steps would be to look at
:py:mod:`dwas' public API <dwas>` and it's sibling
:py:mod:`provided predefined steps <dwas.predefined>`.
For a real example, ``dwas``' `own dwasfile.py`_ is also a good resource.

If you think anything is missing from this starting guide or have suggestions
on how to improve it, please `submit an issue`_ or open a pull request.
