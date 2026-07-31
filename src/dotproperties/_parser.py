"""Parse Java Properties through chunk, line, entry, and escape stages."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from typing import BinaryIO, TextIO

_CHUNK_SIZE = 8192
_HEX_DIGITS = frozenset("0123456789ABCDEFabcdef")
_WHITESPACE = " \t\f"
_SHORT_ESCAPES = {"f": "\f", "n": "\n", "r": "\r", "t": "\t"}
_NATURAL_LINE_END = re.compile(r"\r\n?|\n")
# A separator is unescaped only after an even-length run of backslashes.
_KEY_VALUE_SEPARATOR = re.compile(r"(?<!\\)(?:\\\\)*(?P<separator>[=: \t\f])")
_SURROGATE_PAIR = re.compile(r"[\ud800-\udbff][\udc00-\udfff]")


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
        start = 0
        if skip_lf:
            skip_lf = False
            if chunk.startswith("\n"):
                start = 1

        for match in _NATURAL_LINE_END.finditer(chunk, start):
            segment = chunk[start : match.start()]
            if buffer:
                buffer.append(segment)
                yield "".join(buffer)
                buffer.clear()
            else:
                yield segment
            start = match.end()
            # A CR at the chunk boundary may be followed by LF in the next chunk.
            skip_lf = chunk[match.start()] == "\r" and start == len(chunk)

        if start < len(chunk):
            buffer.append(chunk[start:])

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
        if continued and (not line or line[0] in "#!") and not parts:
            continued = False
            continue
        if not continued and (not line or line[0] in "#!"):
            continue

        # An odd trailing run escapes the terminator. Remove exactly the final
        # continuation marker; the remaining backslashes are decoded later.
        backslashes = len(line) - len(line.rstrip("\\"))
        if backslashes % 2:
            part = line[:-1]
            if part:
                parts.append(part)
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
    match = _KEY_VALUE_SEPARATOR.search(line)
    key_end = match.start("separator") if match else len(line)

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
    escaped_surrogate = False

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
        codepoint = int(digits, 16)
        escaped_surrogate |= 0xD800 <= codepoint <= 0xDFFF
        output.append(chr(codepoint))
        index += 4

    result = "".join(output)
    if result.isascii():
        return result
    if escaped_surrogate:
        return _SURROGATE_PAIR.sub(_replace_surrogate_pair, result)
    return _normalize_surrogates(result)


def _normalize_surrogates(value: str) -> str:
    """Combine valid UTF-16 pairs while preserving isolated surrogate units."""
    try:
        value.encode()
    except UnicodeEncodeError:
        return _SURROGATE_PAIR.sub(_replace_surrogate_pair, value)
    return value


def _replace_surrogate_pair(match: re.Match[str]) -> str:
    """Combine one UTF-16 surrogate pair into its Unicode code point."""
    high, low = map(ord, match.group())
    return chr(0x10000 + ((high - 0xD800) << 10) + low - 0xDC00)
