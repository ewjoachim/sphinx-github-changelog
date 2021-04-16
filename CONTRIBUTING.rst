Contributing
============

You're welcome to come and bake delicious macaroons with us :)

This project uses Poetry_, pre-commit_ and tox_. We recommand installing those with
pipx_.

.. _Poetry: https://python-poetry.org/
.. _pre-commit: https://pre-commit.com
.. _pipx: https://pipxproject.github.io/pipx/installation/
.. _tox: https://tox.readthedocs.io/en/latest/

There are multiple ways of interacting with the project.

I just want to run the CI checks locally
----------------------------------------

.. code-block:: console

    $ tox

Of course, you can launch a single environment (see ``tox.ini`` for details on each
environment). For a full run, you'll need to have all the Python versions that this lib
supports, installed locally (but it's ok to do a partial run, that's why the CI is for).

I want to run the code quality tools
------------------------------------

Assuming you installed ``pre-commit``, use ``pre-commit run``.
But assuming you installed ``pre-commit``, run ``pre-commit install`` and you'll have
the linters run on commit, which is more practical.

I want a venv to play locally
-----------------------------

.. code-block:: console

    $ poetry install

Look at ``poetry env use python3.X`` if you want to work on a specific Python version.

I want to run the the tests
---------------------------

The easiest way to run the tests on a single python version is:

.. code-block:: console

    $ poetry run pytest

I want a quicker feedback loop
------------------------------

Create a virtualenv with a version of python of your choice (or skip this step if you're
ok working with a virtualenv built with your default ``python3``)

.. code-block:: console

    $ poetry shell

From here, you can launch commands directly, such as ``pytest``

I want to build the documentation
---------------------------------

Build with:

.. code-block:: console

    $ tox -e docs
    $ python -m webbrowser docs/_build/html/index.html

Run spell checking on the documentation (optional):

.. code-block:: console

    $ sudo apt install enchant
    $ tox -e docs-spelling

Because of outdated software and version incompatibilities, spell checking is not
checked in the CI, and we don't require people to run it in their PR. Though, it's
always a nice thing to do. Feel free to include any spell fix in your PR, even if it's
not related to your PR (but please put it in a dedicated commit).

If you need to add words to the spell checking dictionary, it's in
``docs/spelling_wordlist.txt``. Make sure the file is alphabetically sorted.

If Sphinx's console output is localized and you would rather have it in English,
use the environment variable ``LC_ALL=C.utf-8`` (either exported or attached to the
``tox`` process)

I want to hack around
---------------------

You're invited to hack around! We have set up those tools to ease usual developpement
but we're always doing our best so that you can remove the top layers and work
the way you prefer. For example: you can use ``pytest`` or ``black`` as-is, without
all the tools. It's even recommanded to remove layers when things become complicated.

The base commands are in the ``scripts/`` folder. Those scripts are the lowest-level
actions, they consider you have already figured out your virtualenv, dependencies etc.

Core contributor additional documentation
-----------------------------------------

Release a new version
^^^^^^^^^^^^^^^^^^^^^

There should be an active Release Draft with the changelog in GitHub releases. Make
relevant edits to the changelog. Click on Release, that's it, the rest is automated.

When creating the release, GitHub will save the release info and create a tag with the
provided version. The new tag will be seen by GitHub Actions, which will then create a
wheel (using the tag as version number, thanks to our ``setup.py``), and push it to PyPI
(using the new API tokens). That tag should also trigger a ReadTheDocs build, which will
read GitHub releases which will write the changelog in the published documentation.

.. note::

    If you need to edit the name or body of a release in the GitHub UI, don't forget to
    also rebuild the stable and latest doc on readthedocs__.

.. __: https://readthedocs.org/projects/pypitokens/
