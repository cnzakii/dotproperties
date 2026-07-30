"""Serialize mappings as Java Properties text."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from typing import TextIO

# Spaces are handled separately because keys escape all of them while values
# escape only a leading one. Unicode output still escapes isolated surrogates.
_ASCII_ESCAPE = re.compile(r"[^ -~]|[\\=:#!]")
_UNICODE_ESCAPE = re.compile(r"[\t\n\r\f\\=:#!\ud800-\udfff]")
_ESCAPES = {
    "\\": "\\\\",
    "\t": "\\t",
    "\n": "\\n",
    "\r": "\\r",
    "\f": "\\f",
    "=": "\\=",
    ":": "\\:",
    "#": "\\#",
    "!": "\\!",
}


def dumps(
    mapping: Mapping[str, str],
    /,
    *,
    ensure_ascii: bool = True,
) -> str:
    """Serialize a mapping as a Java Properties document.

    Args:
        mapping: String keys and values to serialize.
        ensure_ascii: Escape non-ASCII characters with `\\uXXXX` sequences.

    Returns:
        A text document with each property terminated by LF.

    Raises:
        TypeError: If `mapping` is not a mapping of strings to strings.
    """
    return "".join(_serialize_lines(mapping, ensure_ascii=ensure_ascii))


def dump(
    mapping: Mapping[str, str],
    fp: TextIO,
    /,
    *,
    ensure_ascii: bool = True,
) -> None:
    """Serialize a mapping to a text file-like object.

    The mapping is validated before output begins. The stream remains open and
    is not flushed.

    Args:
        mapping: String keys and values to serialize.
        fp: A text stream supporting `write(str)`.
        ensure_ascii: Escape non-ASCII characters with `\\uXXXX` sequences.

    Raises:
        TypeError: If `mapping` is not a mapping of strings to strings.
    """
    for line in _serialize_lines(mapping, ensure_ascii=ensure_ascii):
        fp.write(line)


def _serialize_lines(
    mapping: Mapping[str, str],
    *,
    ensure_ascii: bool,
) -> Iterator[str]:
    """Validate, escape, and yield one complete property per line."""
    pattern = _ASCII_ESCAPE if ensure_ascii else _UNICODE_ESCAPE

    for key, value in _items(mapping):
        escaped_key = pattern.sub(_replace_escape, key).replace(" ", "\\ ")
        escaped_value = pattern.sub(_replace_escape, value)
        if escaped_value.startswith(" "):
            escaped_value = "\\" + escaped_value
        yield escaped_key + "=" + escaped_value + "\n"


def _items(mapping: Mapping[str, str]) -> list[tuple[str, str]]:
    """Return validated entries in the mapping's iteration order."""
    if not isinstance(mapping, Mapping):
        raise TypeError("expected a mapping of str to str")

    # Validate a stable snapshot so dump() cannot partially write a document
    # before discovering a later non-string entry.
    items = list(mapping.items())
    for key, value in items:
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("property keys and values must be str")

    return items


def _replace_escape(match: re.Match[str]) -> str:
    """Return the Java Properties escape for one matched character."""
    char = match.group()
    replacement = _ESCAPES.get(char)
    return replacement if replacement is not None else _unicode_escape(ord(char))


def _unicode_escape(codepoint: int) -> str:
    """Encode one Python code point as one or two UTF-16 escapes."""
    if codepoint <= 0xFFFF:
        return f"\\u{codepoint:04X}"

    # Java Properties stores supplementary characters as a surrogate pair.
    codepoint -= 0x10000
    high = 0xD800 | (codepoint >> 10)
    low = 0xDC00 | (codepoint & 0x3FF)
    return f"\\u{high:04X}\\u{low:04X}"
