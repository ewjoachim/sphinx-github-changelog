from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def full_gfm_release_dict():
    # See https://github.com/executablebooks/MyST-Parser/issues/1136 for missing elements
    return {
        "name": "A new hope",
        "description": r"""
# Heading

*emphasis* / **strong** / ~~strikethrough~~ / <sub>sub</sub>

Emojis:
- 👍 (UTF-8)

[Contribution guidelines for this project](/docs/index.rst)

1. List
2. Next item

- Unordered
- First

- [x] #1
- [ ] https://github.com/octo-org/octo-repo/issues/740
- [ ] Add delight to the experience when all tasks are complete :tada:

> [!NOTE]
> Highlights information that users should take into account, even when skimming.

> [!TIP]
> Optional information to help a user be more successful.

> [!IMPORTANT]
> Crucial information necessary for users to succeed.

> [!WARNING]
> Critical content demanding immediate user attention due to potential risks.

> [!CAUTION]
> Negative potential consequences of an action.

| foo | bar |
| --- | --- |
| baz | bim |

> # Foo
> bar
> baz


```python
def x():
    pass
```

<details>
<summary>Details</summary>

Details

</details>

<!-- This content will not appear in the rendered Markdown -->

Let's rename \*our-new-project\* to \*our-old-project\*.

![Badge](https://img.shields.io/pypi/v/sphinx-github-changelog?logo=pypi&logoColor=white)


""",
        "url": "https://example.com",
        "tagName": "1.0.0",
        "publishedAt": "2000-01-01",
        "isDraft": False,
    }


@pytest.mark.sphinx(buildername="html", testroot="all")
def test_build(app, httpx_mock, full_gfm_release_dict):
    httpx_mock.add_response(
        url="https://api.github.com/graphql",
        method="POST",
        json={"data": {"repository": {"releases": {"nodes": [full_gfm_release_dict]}}}},
    )
    app.builder.build_all()
    expected = (Path(__file__).parent / "changelog.html").read_text()

    received = (app.outdir / "index.html").read_text()
    print(received)
    query = json.loads(httpx_mock.get_requests()[0].content)["query"]
    assert "query($owner: String!, $repo: String!)" in query
    assert expected in received


@pytest.mark.sphinx(buildername="html", testroot="error")
def test_error(app, status, warning):
    app.builder.build_all()
    assert (
        "No :github: release URL provided and unable to determine it from "
        "git remotes." in warning.getvalue()
    )
