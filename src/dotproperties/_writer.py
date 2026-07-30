"""Serialize mappings as Java Properties text."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from typing import TextIO

# Spaces are handled separately because keys escape all of them while values
# escape only a leading one. Unicode output still escapes isolated surrogates.
_ASCII_ESCAPE = re.compile(r"[^ -~]|[\\=:#!]")
_UNICODE_ESCAPE = re.compile(r"[\t\n\r\f\\=:#!\ud800-\udfff]")
# Comment markers and line endings are handled before these Unicode-only scans.
_ASCII_COMMENT_ESCAPE = re.compile(r"[^\x00-\x7f]")
_UNICODE_COMMENT_ESCAPE = re.compile(r"[\ud800-\udfff]")
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
    sort_keys: bool = False,
    comments: str | None = None,
) -> str:
    """Serialize a mapping as a Java Properties document.

    Args:
        mapping: String keys and values to serialize.
        ensure_ascii: Escape non-ASCII characters throughout the document.
        sort_keys: Sort entries by Java's UTF-16 string order.
        comments: Optional header comment. CR and CRLF are normalized to LF.

    Returns:
        A text document with each property terminated by LF.

    Raises:
        TypeError: If `mapping` or `comments` has an invalid type.
    """
    return "".join(
        _serialize_lines(
            mapping,
            ensure_ascii=ensure_ascii,
            sort_keys=sort_keys,
            comments=comments,
        )
    )


def dump(
    mapping: Mapping[str, str],
    fp: TextIO,
    /,
    *,
    ensure_ascii: bool = True,
    sort_keys: bool = False,
    comments: str | None = None,
) -> None:
    """Serialize a mapping to a text file-like object.

    The mapping is validated before output begins. The stream remains open and
    is not flushed.

    Args:
        mapping: String keys and values to serialize.
        fp: A text stream supporting `write(str)`.
        ensure_ascii: Escape non-ASCII characters throughout the document.
        sort_keys: Sort entries by Java's UTF-16 string order.
        comments: Optional header comment. CR and CRLF are normalized to LF.

    Raises:
        TypeError: If `mapping` or `comments` has an invalid type.
    """
    for line in _serialize_lines(
        mapping,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
        comments=comments,
    ):
        fp.write(line)


def _serialize_lines(
    mapping: Mapping[str, str],
    *,
    ensure_ascii: bool,
    sort_keys: bool,
    comments: str | None,
) -> Iterator[str]:
    """Validate, escape, and yield one complete property per line."""
    items = _items(mapping)
    if comments is not None and not isinstance(comments, str):
        raise TypeError("comments must be str or None")
    if sort_keys:
        items.sort(key=_java_sort_key)

    pattern = _ASCII_ESCAPE if ensure_ascii else _UNICODE_ESCAPE
    if comments is not None:
        comment_pattern = (
            _ASCII_COMMENT_ESCAPE if ensure_ascii else _UNICODE_COMMENT_ESCAPE
        )
        yield from _serialize_comments(comments, pattern=comment_pattern)

    for key, value in items:
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


def _java_sort_key(item: tuple[str, str]) -> bytes:
    """Return key bytes ordered like unsigned Java UTF-16 code units."""
    return item[0].encode("utf-16-be", errors="surrogatepass")


def _serialize_comments(comments: str, *, pattern: re.Pattern[str]) -> Iterator[str]:
    """Yield Java-style comment lines normalized to LF."""
    normalized = comments.replace("\r\n", "\n").replace("\r", "\n")
    for index, line in enumerate(normalized.split("\n")):
        prefix = "#" if index == 0 or not line.startswith(("#", "!")) else ""
        yield prefix + pattern.sub(_replace_escape, line) + "\n"


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
