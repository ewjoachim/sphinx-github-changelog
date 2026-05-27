Contributing
============

You're welcome to come and bake delicious macaroons with us :)

This project uses uv_ and prek_.

.. _uv: https://docs.astral.sh/uv/
.. _prek: https://prek.j178.dev/

There are multiple ways of interacting with the project.

I want to run the code quality tools
------------------------------------

.. code-block:: console

    # Run once:
    $ prek run --all-files

    # Install pre-commit hooks
    $ prek install


I want a venv to play locally
-----------------------------

.. code-block:: console

    $ uv sync

Use ``uv sync --python=3.x`` if you want to work on a specific Python version.

There is no need to activate ``.venv`` manually. Run project commands through
``uv run`` instead.

I want to run the tests
---------------------------

The easiest way to run the tests on a single python version is:

.. code-block:: console

    $ uv run pytest

Coverage is enforced at 100% on merged matrix coverage in CI. Branches gated by
Python-version checks do not need to be covered in every local test run, as long as
they are covered by at least one CI matrix job. When you run pytest locally, you'll get
a terminal report at the bottom as well as a more detailed HTML report in
``htmlcov/index.html``. In PRs, a summary of the coverage report is posted as a comment
by the CI.


I want to build the documentation
---------------------------------

Build with:

.. code-block:: console

    $ scripts/docs
    $ uv run python -m webbrowser docs/_build/html/index.html

If Sphinx's console output is localized, and you would rather have it in English,
use the environment variable ``export LC_ALL=C.utf-8``.

I want to hack around
---------------------

Adapt the commands in ``/scripts`` to your liking.

Core contributor additional documentation
-----------------------------------------

Release a new version
^^^^^^^^^^^^^^^^^^^^^

Make a GitHub Release. The rest is automated.

.. note::

    If you need to edit the name or body of a release in the GitHub UI, don't forget to
    also rebuild the stable and latest doc on readthedocs__.

.. __: https://readthedocs.org/projects/sphinx-github-changelog
