# Changelog

User-visible changes to `dotproperties` are recorded here.

## [Unreleased]

### Added

- Added `sort_keys` and `comments` serialization options for deterministic
  Java-order output and caller-controlled header comments.

### Changed

- Improved parsing and serialization performance without changing format
  behavior, including lower peak memory use for long natural lines.

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
