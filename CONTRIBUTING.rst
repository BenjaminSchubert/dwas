Contributing
============


Proposing Changes
-----------------

When thinking about adding a feature or making a non trivial change, please
start by `opening an issue <https://github.com/BenjaminSchubert/dwas/issues/new>`_, so
we can discuss it beforehand.

For small changes, or bug fixes, feel free to make a pull request directly if you
prefer. An issue is welcome too if you prefer first.



Working on ``dwas``
-------------------

``dwas`` uses itself, if you are already familiar with how it works, you should
feel at home here.

Testing, Linting, etc
^^^^^^^^^^^^^^^^^^^^^

To view the full list of actions you can make on this repository, you can always
use ``dwas --list``, but here are the most important ones:

- ``dwas fix``, to fix all auto fixable errors on the project
- ``dwas lint``, to run all linters
- ``dwas pytest``, to run all tests against ``dwas``
- ``dwas docs``, to build and validate the docs
- ``dwas ci``, to run all checks like the CI.

Repository layout
^^^^^^^^^^^^^^^^^

The code is found under ``./src``, tests under ``./tests`` and docs under
``./docs``.


Making Releases
---------------

1. Preparing the release
^^^^^^^^^^^^^^^^^^^^^^^^

The first step is to prepare the release. For this:

#. Update the version in ``./pyproject.toml`` to the new version
#. update the ``./CHANGELOG.rst`` to add information about the new release.
   Important entries would be ``BUG FIXES``, ``Features`` and
   ``Breaking Changes``. Please also add a summary of the changes at the start.
#. Push those changes and open a pull request with it.

2. Publishing the release
^^^^^^^^^^^^^^^^^^^^^^^^^

Once the release is on the main branch, the release can be made:

#. Add a tag with the resulting commit, and sign it:
   ``git checkout main && git pull && git tag -s v<version>``
#. Push the commit: ``git push <upstream> v<version>``
#. Build and publish the pypi wheels:
   ``TWINE_USERNAME=__token__ TWINE_PASSWORD=<token> dwas --clean twine:upload``

   Note that the release needs to be signed.

#. Make the release on GitHub

   For this, you will need to go on the tag that was pushed, and hit
   ``create new release``, copy the changelog entry and name the release with its
   version. Note that you will need to transform the changelog entry to markdown,
   as ReST is not supported there.

   You will also need to upload both wheel and sdist to the release.

#. Ensure that the documentation was built on readthedocs, and that it points
   to the new tag by default.
