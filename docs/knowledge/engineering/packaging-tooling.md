---
title: Python packaging and development tooling
description: Official guidance for pyproject metadata, src layout, Hatchling, uv, Ruff, ty, pytest, and typed pure-Python distributions.
topics: [packaging, pyproject, hatchling, uv, ruff, ty, pytest, src-layout]
checked_at: 2026-07-30
---

# Python Packaging And Development Tooling

## Packaging Metadata And Layout

The [Python Packaging User Guide][pyproject] strongly recommends a
`[build-system]` table and recommends `[project]` metadata for new projects.
Static metadata is the simplest option when a value does not need to be
computed. `requires-python` is the authoritative installation constraint;
classifiers are discovery metadata rather than enforcement.

The PyPA [src-layout discussion][src-layout] explains that placing import
packages below `src/` prevents the repository root from shadowing the installed
package and generally requires installation for development. A `py.typed`
marker makes inline annotations visible to type checkers under the
[typing specification][typing-distribution].

Licensing is a project-owner decision. Current PyPA guidance uses an SPDX
expression in `project.license` plus `license-files` patterns under PEP 639; a
tool should not invent a license when none has been selected.

The PyPA [single-source version discussion][single-version] identifies
`package.__version__` as the conventional runtime attribute and permits build
backends to extract it from `__init__.py`. It recommends a test comparing that
attribute with `importlib.metadata.version()` when both are exposed.

## Build And Environment Tools

[Hatchling's build documentation][hatchling] defines the PEP 517 backend as
`hatchling.build` and supports explicit `src/<package>` wheel selection.

[uv project documentation][uv-projects] treats `.python-version` as the default
development interpreter request, `requires-python` as the supported range, and
`uv.lock` as a cross-platform resolved lockfile intended for version control.
The two version declarations have different jobs and may legitimately differ.
The [`setup-uv` action][setup-uv] searches `uv.toml` and `pyproject.toml` for a
`required-version`; when none is present, it installs the latest uv release.

## Static And Test Tools

[Ruff configuration][ruff] can infer its minimum target from
`project.requires-python`; an explicit target is unnecessary when both live in
the same `pyproject.toml`. Since Ruff 0.16.0,
[`ruff format`][ruff-formatter] also discovers Markdown files and formats valid
Python fenced code blocks by default. It does not format the surrounding
Markdown prose.

[ty configuration][ty] likewise infers its Python target from the lower bound
of `requires-python`. It can discover a conventional `src/` root, while an
explicit root is useful when the package path should be unambiguous.

[`pytest` configuration][pytest] may live in `pyproject.toml`. Strict
configuration, strict marker handling, and warnings-as-errors turn misspelled
settings and unexpected warnings into test failures.

[pyproject]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
[src-layout]: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
[typing-distribution]: https://typing.python.org/en/latest/spec/distributing.html
[single-version]: https://packaging.python.org/en/latest/discussions/single-source-version/
[hatchling]: https://hatch.pypa.io/latest/config/build/
[uv-projects]: https://docs.astral.sh/uv/guides/projects/
[setup-uv]: https://github.com/astral-sh/setup-uv#install-a-required-version-or-latest-default
[ruff]: https://docs.astral.sh/ruff/configuration/
[ruff-formatter]: https://docs.astral.sh/ruff/formatter/#markdown-code-formatting
[ty]: https://docs.astral.sh/ty/python-version/
[pytest]: https://docs.pytest.org/en/stable/reference/customize.html
