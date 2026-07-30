# Contributing to dotproperties

Bug fixes, tests, documentation, compatibility findings, performance
improvements, and simplifications are welcome. Please open an issue before
adding public API or changing format behavior. Report vulnerabilities through
[SECURITY.md](SECURITY.md), not a public issue.
Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Development setup

Install Git and [uv](https://docs.astral.sh/uv/), then run:

```console
git clone https://github.com/cnzakii/dotproperties.git
cd dotproperties
uv sync --locked
```

The project supports Python 3.10 through 3.14, including free-threaded CPython
3.14t, and uses Python 3.12 for local development. Continuous integration also
tests the unreleased 3.15 and 3.15t previews. A JDK is optional locally; the
interoperability suite runs in continuous integration with Eclipse Temurin 8,
11, 17, 21, and 25.

## Running checks

```console
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked ty check
uv build
```

With a working `java` and `javac` on `PATH`, `uv run --locked pytest` also
compiles and runs the Java reference used by the interoperability tests.

Add tests for observable behavior changes. Use Google-style docstrings for
public APIs, keep supported Python and Java versions free of platform-specific
path or shell assumptions, and include reproducible measurements with
performance claims.

## Releases

`dotproperties` uses `X.Y.Z` versions. Before 1.0, increment the minor version
for new public behavior or intentional compatibility changes and the patch
version for backward-compatible fixes.

Every release starts with a pull request that updates `__version__` in
`src/dotproperties/__init__.py` and moves the relevant changelog entries under
`## [X.Y.Z] - YYYY-MM-DD`. After its required checks pass, tag the merge commit:

```console
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

The tag verifies the version and changelog, rebuilds and smoke-tests the
distribution, publishes to PyPI through Trusted Publishing, and creates a
GitHub release. Published PyPI files are immutable; correct a broken release
with a new version.

By contributing, you agree that your contribution is licensed under the
project's [MIT License](LICENSE).
