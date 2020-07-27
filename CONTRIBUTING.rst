Contributing Guidelines
=======================

Welcome behind the curtain of Sphinx GiHub Changelog.

Instructions for contribution
-----------------------------

Set up your development environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a `virtual environment`__, and activate it.

.. __: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment

Install the project in development mode, with the dependencies:

.. code-block:: console

    (venv) $ pip install -r requirements.txt

Run the project automated tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    (venv) $ pytest  # Test the code with the current interpreter

Or

.. code-block:: console

    $ tox  # Run all the checks for all the interpreters

If you're not familiar with Pytest_, do yourself a treat and look into this fabulous
tool.

.. _Pytest: https://docs.pytest.org/en/latest/

If you don't know Tox_, have a look at their documentation, it's a very nice tool too.

.. _Tox: https://tox.readthedocs.io/en/latest/

To look at coverage in the browser after launching the tests, use:

.. code-block:: console

    $ python -m webbrowser "$(pwd)/htmlcov/index.html"

Keep your code clean
^^^^^^^^^^^^^^^^^^^^

Before committing:

.. code-block:: console

    $ tox -e format

If you've committed already, you can do a "Oops lint" commit, but the best is to run:

.. code-block:: console

    $ git rebase -i --exec 'tox -e format' origin/master

This will run all code formatters on each commits, so that they're clean.
If you've never done an `interactive rebase`_ before, it may seem complicated, so you
don't have to, but... Learn it, it's really cool !

.. _`interactive rebase`: https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History

You can also install a ``pre-commit``
hook which makes sure that all your commits are created clean:

.. code-block:: console

    cat > .git/hooks/pre-commit <<EOF
    #!/bin/bash -e
    exec ./pre-commit-hook
    EOF
    chmod +x .git/hooks/pre-commit

If ``tox`` is installed inside your ``virtualenv``, you may want to activate the
``virtualenv`` in ``.git/hooks/pre-commit``:

.. code-block:: bash

    #!/bin/bash -e
    source /path/to/venv/bin/activate
    exec ./pre-commit-hook

This will keep you from creating a commit if there's a linting problem.

In addition, an editorconfig_ file will help your favorite editor to respect
this project's coding style. It is automatically used by most famous IDEs, such as
Pycharm and VS Code.

.. _editorconfig: https://editorconfig.org/

Build the documentation
^^^^^^^^^^^^^^^^^^^^^^^

Without spell checking:

.. code-block:: console

    $ tox -e docs
    $ python -m webbrowser docs/_build/html/index.html

Run spell checking on the documentation:

.. code-block:: console

    $ sudo apt install enchant
    $ tox -e docs-spelling

Because of outdated software and version incompatibilities, spell checking is not
checked in the CI, and we don't require people to run it in their PR. Though, it's
always a nice thing to do. Feel free to include any spell fix in your PR, even if it's
not related to your PR (but please put it in a dedicated commit).

If you need to add words to the spell checking dictionary, it's in
``docs/spelling_wordlist.txt``. Make sure the file is alphabetically sorted!

If Sphinx's console output is localized and you would rather have it in English,
use the environment variable ``LC_ALL=C.utf-8`` (either exported or attached to the
tox process)

Core contributor additional documentation
-----------------------------------------

Issues
^^^^^^

Please remember to tag Issues with appropriate labels.

Pull Requests
^^^^^^^^^^^^^

PR labels help ``release-drafter`` pre-fill the next release draft. They're not
mandatory, but releasing will be easier if they're present.

Release a new version
^^^^^^^^^^^^^^^^^^^^^

There should be an active Release Draft with the changelog in GitHub releases. Make
relevant edits to the changelog, (see ``TODO``) including listing the migrations
for the release. Click on Release, that's it, the rest is automated.

When creating the release, GitHub will save the release info and create a tag with
the provided version. The new tag will be seen by Travis, which will then create a
wheel (using the tag as version number, thanks to our ``setup.py``), and push it
to PyPI (using the new API tokens). That tag should also trigger a ReadTheDocs
build, which will read GitHub releases (thanks to our ``changelog`` extension)
which will  write the changelog in the published documentation.
