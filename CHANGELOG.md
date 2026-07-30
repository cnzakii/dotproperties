# Changelog

User-visible changes to `dotproperties` are recorded here.

## [Unreleased]

## [0.1.0] - 2026-07-31

### Added

- `load`, `loads`, `dump`, and `dumps` for classic Java Properties.
- Installed package version available as `dotproperties.__version__`.
- Linear, chunked parsing for text and ISO-8859-1 byte streams.
- Java-compatible escapes, continuations, separators, duplicate keys, and
  UTF-16 surrogate pairs.
- Typed support for Python 3.10 through 3.14, including free-threaded CPython
  3.14t.
- Interoperability checks for Eclipse Temurin 8, 11, 17, 21, and 25.
