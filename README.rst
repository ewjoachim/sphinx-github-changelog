Sphinx Github Changelog: Build a sphinx changelog from GitHub Releases
======================================================================

.. image:: https://img.shields.io/pypi/v/sphinx-github-changelog?logo=pypi&logoColor=white
    :target: https://pypi.org/pypi/sphinx-github-changelog
    :alt: Deployed to PyPI

.. image:: https://img.shields.io/pypi/pyversions/sphinx-github-changelog?logo=pypi&logoColor=white
    :target: https://pypi.org/pypi/sphinx-github-changelog
    :alt: Deployed to PyPI

.. image:: https://img.shields.io/github/stars/ewjoachim/sphinx-github-changelog?logo=github
    :target: https://github.com/ewjoachim/sphinx-github-changelog/
    :alt: GitHub Repository

.. image:: https://img.shields.io/github/actions/workflow/status/ewjoachim/sphinx-github-changelog/ci.yml?logo=github&branch=main
    :target: https://github.com/ewjoachim/sphinx-github-changelog/actions?workflow=CI
    :alt: Continuous Integration

.. image:: https://img.shields.io/readthedocs/sphinx-github-changelog?logo=read-the-docs&logoColor=white
    :target: http://sphinx-github-changelog.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation

.. image:: https://img.shields.io/endpoint?logo=codecov&logoColor=white&url=https://raw.githubusercontent.com/wiki/ewjoachim/sphinx-github-changelog/coverage-comment-badge.json
    :target: https://github.com/marketplace/actions/coverage-comment
    :alt: Coverage

.. image:: https://img.shields.io/github/license/ewjoachim/sphinx-github-changelog?logo=open-source-initiative&logoColor=white
    :target: https://github.com/ewjoachim/sphinx-github-changelog/blob/master/LICENSE
    :alt: MIT License

.. image:: https://img.shields.io/badge/Contributor%20Covenant-v1.4%20adopted-ff69b4.svg
    :target: https://github.com/ewjoachim/sphinx-github-changelog/blob/master/CODE_OF_CONDUCT.md
    :alt: Contributor Covenant

Sphinx-github-changelog is a Sphinx_ plugin that builds a changelog section based on
a repository's `GitHub Releases`_ content.

.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _`GitHub Releases`: https://docs.github.com/en/github/administering-a-repository/about-releases

How ? (the short version)
=========================

In your Sphinx documentation ``conf.py``:

.. code-block:: python

    extensions = [
        ...,  # your other extensions
        "sphinx_github_changelog",
    ]

    # Provide a GitHub API token:
    # Pass the SPHINX_GITHUB_CHANGELOG_TOKEN environment variable to your build
    # OR
    # You can retrieve your token any other way you want, but of course, please
    # don't commit secrets to git, especially on a public repository
    sphinx_github_changelog_token = ...

In your documentation:

.. code-block:: restructuredtext

    .. changelog::
        :changelog-url: https://your-project.readthedocs.io/en/stable/#changelog
        :github: https://github.com/you/your-project/releases/
        :pypi: https://pypi.org/project/your-project/


See the end result for this project on ReadTheDocs__.

.. __: https://sphinx-github-changelog.readthedocs.io/en/stable/#changelog

Why ?
=====

On the way to continuous delivery, it's important to be able to release easily.
One of the criteria for easy releases is that the release doesn't require a commit and
a Pull Request. Release Pull Requests usually include 2 parts:

- Changing the version
- Updating the changelog (if you keep a changelog, let's assume you do)

Commitless releases need a way to store the version and the changelog, as close as
possible to the code, but actually **not in** the code.

Setting aside the "version" question, ``sphinx-github-changelog`` aims at providing
a good way of managing the "changelog" part:

The best solution we've found so far for the changelog is to store it in the body of
`GitHub Releases`_. That's very practical for maintainers, but it may not be the first
place people will look for it. As far as we've seen, people expect the changelog to
be:

- in the repo, in ``CHANGELOG.rst``,
- in the documentation.

Having the changelog in ``CHANGELOG.rst`` causes a few problems:

- Either each PR adds its single line of changelog, but:

  - you'll most probably run into countless merge conflicts,
  - the changelog won't tell you which contribution was part of which release

  This reduces the interest for the whole thing.

- Or your changelog is edited at release time. Maybe you're using towncrier_ for
  fragment-based changelog, but you're not doing commitless releases anymore. You could
  imagine that the release commit is done by your CI, but this can quickly become
  annoying, especially if you require Pull Requests.

But there is another way. Instead of providing the changelog, the ``CHANGELOG.rst``
file can hold a *link* to the changelog. This makes things much easier.
``sphinx-github-changelog`` encourages you to do that.

A complete toolbelt
-------------------

Alongside ``sphinx-github-changelog``, we suggest a few tools that play nice together:

- `setuptools-scm`_ will compute your version in ``setup.py`` based on git tags.
- `release-drafter`_ will keep a "Draft release" updated as you merge Pull Requests to
  your repository, so you just have to slightly adjust the release body, and create a
  tag.
- Any Continuous Integration solution should be able to listen to new tags, and build
  and upload distributions to PyPI. Don't forget to use `PyPI API tokens`_!
- And ReadTheDocs_ to host your built documentation, of course.

.. _`setuptools-scm`: https://pypi.org/project/setuptools-scm/
.. _`release-drafter`: https://help.github.com/en/github/administering-a-repository/about-releases
.. _towncrier: https://pypi.org/project/towncrier/
.. _`PyPI API tokens`: https://pypi.org/help/#token
.. _ReadTheDocs: https://readthedocs.org/

If you're using all the tools above, then releasing is simple as proof-reading the
draft GitHub Release and press "Publish Release". That's it.

Reference documentation
=======================

Extension options (``conf.py``)
-------------------------------

- ``sphinx_github_changelog_token``: GitHub API token.
  If the repository is public, the token doesn't need any special access (you
  can uncheck eveything). If the repository is private, you'll need to give
  your token enough access to read the releases. Defaults to the value of the
  environment variable ``SPHINX_GITHUB_CHANGELOG_TOKEN``. If no value is
  provided, the build will still pass but the changelog will not be built, and
  a link to the ``changelog-url`` will be displayed (if provided).

- ``sphinx_github_changelog_root_repo`` (optional): Root url to the repository,
  defaults to "https://github.com/". Useful if you're using a self-hosted GitHub
  instance.

- ``sphinx_github_changelog_graphql_url`` (optional): Url to graphql api, defaults
  to "https://api.github.com/graphql". Useful if you're using a self-hosted GitHub
  instance.

.. _ReadTheDocs: https://readthedocs.org/

Directive
---------

.. code-block:: restructuredtext

    .. changelog::
        :changelog-url: https://your-project.readthedocs.io/en/stable/changelog.html
        :github: https://github.com/you/your-project/releases/
        :pypi: https://pypi.org/project/your-project/

Attributes
~~~~~~~~~~

- ``github`` (**required**): URL to the releases page of the repository.
- ``changelog-url`` (optional): URL to the built version of your changelog.
  ``sphinx-github-changelog`` will display a link to your built changelog if the GitHub
  token is not provided (hopefully, this does not happen in your built documentation)
- ``pypi`` (optional): URL to the PyPI page of the repository. This allows the changelog
  to display links to each PyPI release.

You'll notice that each parameter here is not requested in the simplest form but as
very specific URLs from which the program extracts the needed information. This is
done on purpose. If people browse the unbuilt version of your documentation
(e.g. on GitHub or PyPI directly), they'll still be presented with links to the pages
that contain the information they will need, instead of unhelping directives.

.. Below this line is content specific to GitHub / PyPI that will not appear in the
   built doc.
.. end-of-index-doc

Check out the built version!
============================

This Readme is also built as a Sphinx documentation, and it includes the changelog.
Interested to see how it looks? Check it out on `our ReadTheDocs space`_.

.. _`our ReadTheDocs space`: https://sphinx-github-changelog.readthedocs.io/en/stable

If you encounter a bug, or want to get in touch, you're always welcome to open a
ticket_.

.. _ticket: https://github.com/peopledoc/sphinx-github-changelog/issues/new

Other links
===========

- `Code of Conduct <CODE_OF_CONDUCT.rst>`_.
- `License <LICENCE.rst>`_.
- `Contributing Guidelines <CONTRIBUTING.rst>`_.
