"""Serialize mappings as Java Properties text."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import TextIO


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
    for key, value in _items(mapping):
        yield (
            _escape(key, escape_space=True, ensure_ascii=ensure_ascii)
            + "="
            + _escape(value, escape_space=False, ensure_ascii=ensure_ascii)
            + "\n"
        )


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


def _escape(value: str, *, escape_space: bool, ensure_ascii: bool) -> str:
    """Escape one field using the line format emitted by Properties.store().

    Args:
        value: The string to escape.
        escape_space: Whether every space is escaped. Keys require this, while
            values require it only for the first character.
        ensure_ascii: Whether non-ASCII characters use UTF-16 escapes.

    Returns:
        The escaped property field.
    """
    output: list[str] = []

    for index, char in enumerate(value):
        if char == " ":
            output.append("\\ " if escape_space or index == 0 else " ")
        elif char == "\\":
            output.append("\\\\")
        elif char == "\t":
            output.append("\\t")
        elif char == "\n":
            output.append("\\n")
        elif char == "\r":
            output.append("\\r")
        elif char == "\f":
            output.append("\\f")
        elif char in "=:#!":
            output.append("\\" + char)
        else:
            codepoint = ord(char)
            # Isolated surrogates cannot be written safely as ordinary Unicode,
            # even when readable non-ASCII output was requested.
            if 0xD800 <= codepoint <= 0xDFFF or (
                ensure_ascii and (codepoint < 0x20 or codepoint > 0x7E)
            ):
                output.append(_unicode_escape(codepoint))
            else:
                output.append(char)

    return "".join(output)


def _unicode_escape(codepoint: int) -> str:
    """Encode one Python code point as one or two UTF-16 escapes."""
    if codepoint <= 0xFFFF:
        return f"\\u{codepoint:04X}"

    # Java Properties stores supplementary characters as a surrogate pair.
    codepoint -= 0x10000
    high = 0xD800 | (codepoint >> 10)
    low = 0xDC00 | (codepoint & 0x3FF)
    return f"\\u{high:04X}\\u{low:04X}"
