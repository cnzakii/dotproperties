<h1 align="center">dotproperties</h1>

<p align="center">
  <strong>A zero-dependency, pure-Python reader and writer for Java Properties.</strong>
</p>

<p align="center">
  <a href="https://github.com/cnzakii/dotproperties/actions/workflows/ci.yml"><img src="https://github.com/cnzakii/dotproperties/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/dotproperties/"><img src="https://img.shields.io/pypi/v/dotproperties.svg" alt="PyPI"></a>
  <a href="https://github.com/cnzakii/dotproperties/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/Python-3.10%20to%203.14-3776AB?logo=python&amp;logoColor=white" alt="Python 3.10–3.14"></a>
  <a href="https://github.com/cnzakii/dotproperties/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/free--threaded-3.14t-3776AB?logo=python&amp;logoColor=white" alt="Free-threaded CPython 3.14t"></a>
  <a href="https://github.com/cnzakii/dotproperties/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
</p>

`dotproperties` reads and writes the classic line-oriented
`java.util.Properties` format.

It handles comments, continuations, separators, duplicate keys, Java escapes,
and UTF-16 surrogate pairs. Byte and text input follow Java's distinct
`InputStream` and `Reader` rules, and interoperability is checked against all
current Eclipse Temurin LTS lines: 8, 11, 17, 21, and 25.

## Install

Add `dotproperties` to a uv-managed project:

```console
uv add dotproperties
```

Or install it with pip:

```console
pip install dotproperties
```

Python 3.10 through 3.14 and free-threaded CPython 3.14t are supported. Python
3.15 and 3.15t previews are tested for forward compatibility until Python 3.15
is released.

## Quick start

Parse a string with `loads()`:

```python
import dotproperties

config = dotproperties.loads(
    """
    # Application settings
    host = localhost
    port: 8080
    greeting = Olá
    """
)

print(config)
```

```text
{'host': 'localhost', 'port': '8080', 'greeting': 'Olá'}
```

Serialize a mapping with `dumps()`:

```python
text = dotproperties.dumps(config)
print(text, end="")
```

```properties
host=localhost
port=8080
greeting=Ol\u00E1
```

Read and write files with `load()` and `dump()`:

```python
with open("application.properties", "rb") as fp:
    config = dotproperties.load(fp)

with open("application.properties", "w", encoding="ascii") as fp:
    dotproperties.dump(config, fp)
```

## Encoding and streams

Strings and text streams are already-decoded character input, corresponding to
Java's `Properties.load(Reader)`. Bytes and binary streams use ISO-8859-1,
matching `Properties.load(InputStream)`.

Serialization produces text and escapes every non-ASCII code point by default,
so the result is safe to write as ASCII and load through either Java path.
Keys and values must be strings.

Set `ensure_ascii=False` to retain readable Unicode:

```python
text = dotproperties.dumps({"greeting": "你好"}, ensure_ascii=False)

with open("application.properties", "w", encoding="utf-8") as fp:
    fp.write(text)
```

Load that file through a Java `Reader` using the same encoding. Passing its
UTF-8 bytes to `Properties.load(InputStream)` would apply ISO-8859-1 instead.

`load()` makes bounded-size read requests. `load()` and `dump()` leave
caller-owned streams open; `dump()` also leaves flushing to the caller and
validates the complete mapping before its first write. A malformed `\uXXXX`
escape raises `ValueError`.

`dotproperties.__version__` reports the installed package version.

## Format behavior

- Leading spaces, tabs, and form feeds are ignored. `#` and `!` begin comment
  lines after that leading whitespace; comment lines cannot be continued.
- An odd run of trailing backslashes continues a logical line. Leading format
  whitespace on the next natural line is discarded.
- The first unescaped `=`, `:`, space, tab, or form feed separates the key from
  the value. A missing value is the empty string.
- `\t`, `\n`, `\r`, `\f`, and `\uXXXX` use Java's meanings. For other escaped
  characters, Java's rule drops the backslash.
- Valid UTF-16 surrogate pairs become one Python Unicode character. Isolated
  surrogate units remain isolated and are always serialized as escapes.
- Duplicate keys use the last value, matching `Properties.load()`.

Parsing does not preserve comments or original spelling. Serialization emits
only `key=value` lines: it does not add Java's timestamp comment. Entries
follow the mapping's iteration order. Java 8 does not specify the order used by
`Properties.store()`, while Java 25 sorts ordinary `Properties` by key. The
format itself has no semantic order, so sort the mapping before serialization
only when a particular textual order is required.

XML properties, defaults chains, interpolation, and lossless document editing
are outside this package's scope.

## Safety and resource limits

The line format is data-only. Parsing does not construct Python objects from
type tags, evaluate expressions, expand variables, follow includes, or access
external resources.

Like `Properties.load()`, `dotproperties` does not impose a document-size,
logical-line, or entry-count limit. Bounded-size requests to `fp.read()` do not
cap total CPU or memory use; the result and the longest unfinished logical line
must still fit in memory. Applications accepting untrusted input should limit
it before parsing.

`dump()` prevents invalid mapping entries from causing partial output, but an
I/O failure can still interrupt a write. Applications that replace important
files should write to a temporary file and perform an atomic replacement.

## Development

The default development interpreter is Python 3.12. See
[CONTRIBUTING.md](https://github.com/cnzakii/dotproperties/blob/main/CONTRIBUTING.md)
for setup, checks, interoperability testing, and releases.
Report suspected vulnerabilities through the
[security policy](https://github.com/cnzakii/dotproperties/blob/main/SECURITY.md).
Participation is governed by the
[code of conduct](https://github.com/cnzakii/dotproperties/blob/main/CODE_OF_CONDUCT.md).

## License

`dotproperties` is available under the
[MIT License](https://github.com/cnzakii/dotproperties/blob/main/LICENSE).
