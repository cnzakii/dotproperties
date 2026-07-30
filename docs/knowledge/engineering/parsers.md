---
title: Reference parser architectures
description: Observed file/string API and buffering patterns in CPython JSON, TOML, configparser, and PyYAML, with streaming design implications.
topics: [parsers, json, toml, yaml, configparser, streaming]
checked_at: 2026-07-30
---

# Reference Parser Architectures

## Standard-Library API Shape

The Python [`json` module][json-docs] exposes `load`, `loads`, `dump`, and
`dumps`; the file variants accept file-like objects and serialization produces
text. In [CPython 3.14.5][json-source], `json.load()` reads the complete
document and delegates to `loads()`.

The read-only [`tomllib` API][tomllib-docs] exposes `load` and `loads`. Its
[CPython 3.14.5 implementation][tomllib-source] also reads the complete binary
file before parsing. These implementations show that a small public API does
not determine whether the parser buffers or scans incrementally.

[`ConfigParser.read_file()`][configparser-docs] accepts an iterable of Unicode
lines. This is a closer standard-library example for a line-oriented format,
although INI grammar is not compatible with Java Properties and should not be
reused as its parser.

## YAML Stream Practice

YAML 1.2.2 explicitly defines a stream that may contain multiple documents.
[PyYAML 6.0.3's reader][pyyaml-reader] fills its raw buffer in chunks, while its
public surface offers single- and multi-document operations such as `load` and
`load_all` in the [pinned package source][pyyaml-api]. This architecture serves
a grammar and public contract that expose document streaming.

## Methodological Synthesis

Buffering is a grammar decision, not an API-naming decision:

- a whole-document grammar can reasonably implement `load()` as
  `loads(fp.read())`;
- an independently completable line grammar can use bounded file reads while
  sharing the same scanner with `loads()`;
- returning a complete mapping still requires memory proportional to the
  result, even when input buffering is bounded;
- line continuation requires buffering at least the longest unfinished logical
  line;
- a public iterator is useful only when the format and consumer can observe
  entries incrementally. If duplicate keys have last-value-wins semantics and
  the contract returns a final mapping, an iterator is a separate semantic
  choice rather than a free optimization.

For chunked line scanners, boundary tests must split CRLF, backslash runs,
Unicode escapes, separators, and arbitrary multicharacter examples across
chunks. A one-character chunk source is a compact completeness check.

[json-docs]: https://docs.python.org/3.14/library/json.html
[json-source]: https://github.com/python/cpython/blob/v3.14.5/Lib/json/__init__.py
[tomllib-docs]: https://docs.python.org/3.14/library/tomllib.html
[tomllib-source]: https://github.com/python/cpython/blob/v3.14.5/Lib/tomllib/_parser.py
[configparser-docs]: https://docs.python.org/3.14/library/configparser.html#configparser.ConfigParser.read_file
[pyyaml-reader]: https://github.com/yaml/pyyaml/blob/6.0.3/lib/yaml/reader.py
[pyyaml-api]: https://github.com/yaml/pyyaml/blob/6.0.3/lib/yaml/__init__.py
