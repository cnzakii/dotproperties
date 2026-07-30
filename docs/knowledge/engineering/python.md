---
title: Python language and documentation conventions
description: Supported syntax, typing, public API, comments, and Google-style docstring guidance for a Python 3.10+ library.
topics: [python, typing, api-design, comments, docstrings]
checked_at: 2026-07-30
---

# Python Language And Documentation Conventions

## Compatibility Floor

The [`requires-python` project metadata field][pyproject] declares install-time
compatibility and gives development tools a lower-bound target. As of
2026-07-30, Python 3.10 remains in security support until October 2026, while
3.12 remains supported until October 2028 according to the
[Python Developer's Guide version table][versions].

Python 3.10 provides built-in generic aliases such as `dict[str, str]` and
[PEP 604 union syntax][pep604] such as `str | bytes`. A library declaring
Python 3.10 must avoid unguarded syntax and standard-library APIs introduced in
later releases. A newer development interpreter does not change that floor.

As of 2026-07-30, Python 3.15 is a prerelease with its first final release
scheduled for October 2026. Testing a prerelease demonstrates forward
compatibility, but it is distinct from declaring a released version as part of
the supported range.

## Free-Threaded CPython

[PEP 779][pep779] moved free-threaded CPython into its officially supported,
optional phase for Python 3.14. The [PyPI classifier list][classifiers] provides
four free-threading support levels. The
[Python Free-Threading Guide][free-threading-classifiers] describes level 2,
Beta, as supported use whose constraints and limitations may not yet be
completely documented; levels 3 and 4 additionally require tested, documented
multithreaded behavior.

## Public API And Typing

[PEP 8][pep8] treats names with one leading underscore as non-public and
recommends explicit public interfaces. [Typing guidance for package
authors][typing-distribution] describes the `py.typed` marker for distributions
that ship inline annotations.

Type annotations document the supported contract; runtime validation is still
needed where invalid values could create malformed or partially written output.
Use standard ABCs such as `collections.abc.Mapping` when behavior, rather than
a concrete `dict`, is the contract.

## Comments And Docstrings

[PEP 257][pep257] defines docstring conventions. The
[Google Python Style Guide][google-docstrings] asks public functions to explain
their purpose and, when useful, `Args`, `Returns`, and `Raises`. Module
docstrings describe exported behavior. Comments should explain non-obvious
intent or constraints rather than translate code into prose; the
[Google comments section][google-comments] also requires comments to remain
accurate as code changes.

The practical distinction is:

- use a docstring for a public contract;
- use a short inline comment for a surprising algorithmic or interoperability
  constraint;
- use a descriptive name instead of a comment when the code is already clear.

[pyproject]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#requires-python
[versions]: https://devguide.python.org/versions/
[pep604]: https://peps.python.org/pep-0604/
[pep779]: https://peps.python.org/pep-0779/
[classifiers]: https://pypi.org/classifiers/
[free-threading-classifiers]: https://py-free-threading.github.io/porting/#free-threading-classifier
[pep8]: https://peps.python.org/pep-0008/
[pep257]: https://peps.python.org/pep-0257/
[typing-distribution]: https://typing.python.org/en/latest/spec/distributing.html
[google-docstrings]: https://google.github.io/styleguide/pyguide.html#383-functions-and-methods
[google-comments]: https://google.github.io/styleguide/pyguide.html#385-block-and-inline-comments
