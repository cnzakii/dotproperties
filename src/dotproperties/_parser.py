"""Parse Java Properties through chunk, line, entry, and escape stages."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import BinaryIO, TextIO

_CHUNK_SIZE = 8192
_HEX_DIGITS = frozenset("0123456789ABCDEFabcdef")
_WHITESPACE = " \t\f"
_SHORT_ESCAPES = {"f": "\f", "n": "\n", "r": "\r", "t": "\t"}


def loads(data: str | bytes, /) -> dict[str, str]:
    """Parse a Java Properties document from text or bytes.

    Args:
        data: Decoded text or ISO-8859-1 bytes.

    Returns:
        A dictionary containing the parsed string keys and values.

    Raises:
        TypeError: If `data` is not `str` or `bytes`.
        ValueError: If a malformed `\\uXXXX` escape is present.
    """
    return _parse((_as_text(data),))


def load(fp: BinaryIO | TextIO, /) -> dict[str, str]:
    """Parse a Java Properties document from a file-like object.

    The stream is read with bounded-size requests and remains open.

    Args:
        fp: A binary ISO-8859-1 stream or an already-decoded text stream.

    Returns:
        A dictionary containing the parsed string keys and values.

    Raises:
        TypeError: If the stream returns values other than `str` or `bytes`.
        ValueError: If a malformed `\\uXXXX` escape is present.
    """
    return _parse(_read_chunks(fp))


def _as_text(data: str | bytes) -> str:
    """Return text, decoding byte input as ISO-8859-1."""
    if isinstance(data, str):
        return data
    if isinstance(data, bytes):
        return data.decode("iso-8859-1")
    raise TypeError("expected str or bytes")


def _read_chunks(fp: BinaryIO | TextIO) -> Iterator[str]:
    """Yield text from bounded-size reads without closing the stream."""
    while True:
        chunk = fp.read(_CHUNK_SIZE)
        if chunk == "" or chunk == b"":
            return
        yield _as_text(chunk)


def _parse(chunks: Iterable[str]) -> dict[str, str]:
    """Run the parsing pipeline and apply Java's last-value-wins rule."""
    properties: dict[str, str] = {}
    for line in _logical_lines(_natural_lines(chunks)):
        key, value = _split_key_value(line)
        properties[_unescape(key)] = _unescape(value)
    return properties


def _natural_lines(chunks: Iterable[str]) -> Iterator[str]:
    """Split chunks only on Java Properties line terminators.

    CRLF must be treated as one terminator even when CR and LF arrive in
    different input chunks. Other Unicode line separators remain data.
    """
    buffer: list[str] = []
    skip_lf = False

    for chunk in chunks:
        for char in chunk:
            if skip_lf:
                skip_lf = False
                if char == "\n":
                    continue

            if char == "\r":
                yield "".join(buffer)
                buffer.clear()
                # Delay the CRLF decision until the next character or chunk.
                skip_lf = True
            elif char == "\n":
                yield "".join(buffer)
                buffer.clear()
            else:
                buffer.append(char)

    # A non-terminated final natural line is still part of the document.
    if buffer:
        yield "".join(buffer)


def _logical_lines(lines: Iterable[str]) -> Iterator[str]:
    """Join continued natural lines and discard blank and comment lines."""
    parts: list[str] = []
    continued = False

    for natural_line in lines:
        # Only space, tab, and form feed are whitespace in this format.
        line = natural_line.lstrip(_WHITESPACE)

        # A continuation-only logical line has no property data. Discard it
        # when the next natural line is blank or a comment.
        if continued and (not line or line[0] in "#!") and not any(parts):
            parts.clear()
            continued = False
            continue
        if not continued and (not line or line[0] in "#!"):
            continue

        # An odd trailing run escapes the terminator. Remove exactly the final
        # continuation marker; the remaining backslashes are decoded later.
        backslashes = len(line) - len(line.rstrip("\\"))
        if backslashes % 2:
            parts.append(line[:-1])
            continued = True
        else:
            parts.append(line)
            yield "".join(parts)
            parts.clear()
            continued = False

    # At EOF OpenJDK omits an unmatched continuation marker but still returns
    # the logical line, even when that leaves an empty line.
    if continued:
        yield "".join(parts)


def _split_key_value(line: str) -> tuple[str, str]:
    """Find the first unescaped key terminator and the value start."""
    escaped = False
    key_end = len(line)

    for index, char in enumerate(line):
        if not escaped and (char in "=:" or char in _WHITESPACE):
            key_end = index
            break
        # Toggling handles odd and even runs of backslashes before a separator.
        escaped = not escaped if char == "\\" else False

    value_start = key_end
    while value_start < len(line) and line[value_start] in _WHITESPACE:
        value_start += 1
    if value_start < len(line) and line[value_start] in "=:":
        value_start += 1
    while value_start < len(line) and line[value_start] in _WHITESPACE:
        value_start += 1

    return line[:key_end], line[value_start:]


def _unescape(value: str) -> str:
    """Decode the restricted escape grammar used by Java Properties."""
    if "\\" not in value:
        return value if value.isascii() else _normalize_surrogates(value)

    output: list[str] = []
    index = 0

    while index < len(value):
        char = value[index]
        index += 1
        if char != "\\":
            output.append(char)
            continue

        # Logical-line assembly and key splitting never leave a trailing backslash.
        escaped = value[index]
        index += 1
        if escaped != "u":
            # Unknown escapes lose the backslash: for example, \b becomes b.
            output.append(_SHORT_ESCAPES.get(escaped, escaped))
            continue

        digits = value[index : index + 4]
        # int(..., 16) accepts surrounding whitespace and some Unicode digits;
        # Java Properties permits exactly four ASCII hexadecimal digits.
        if len(digits) != 4 or not set(digits) <= _HEX_DIGITS:
            raise ValueError("malformed \\uXXXX encoding")
        output.append(chr(int(digits, 16)))
        index += 4

    return _normalize_surrogates("".join(output))


def _normalize_surrogates(value: str) -> str:
    """Combine valid UTF-16 pairs while preserving isolated surrogate units."""
    return value.encode("utf-16-be", errors="surrogatepass").decode(
        "utf-16-be", errors="surrogatepass"
    )
