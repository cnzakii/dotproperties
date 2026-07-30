from __future__ import annotations

from collections.abc import Mapping
from importlib.metadata import version as distribution_version
from io import BytesIO, StringIO
from typing import cast

import pytest

import dotproperties


def test_exposes_installed_distribution_version() -> None:
    assert dotproperties.__version__ == distribution_version("dotproperties")


def test_loads_java_examples_and_duplicate_keys() -> None:
    document = """\
        # comments may be indented
        ! another comment
        Truth = Beauty
         Truth:Beauty
        Truth                    :Beauty
        cheeses
        fruits = apple, banana, pear, \\
                 cantaloupe, watermelon, \\
                 kiwi, mango
    """

    assert dotproperties.loads(document) == {
        "Truth": "Beauty",
        "cheeses": "",
        "fruits": "apple, banana, pear, cantaloupe, watermelon, kiwi, mango",
    }


def test_loads_key_boundaries_and_ascii_whitespace() -> None:
    document = (
        "\\:\\==punctuation\n"
        "key\\ with\\ spaces value\n"
        "even\\\\=separator\n"
        "odd\\=key=value\n"
        "=empty-key\n"
        "\u00a0=value"
    )

    assert dotproperties.loads(document) == {
        ":=": "punctuation",
        "key with spaces": "value",
        "even\\": "separator",
        "odd=key": "value",
        "": "empty-key",
        "\u00a0": "value",
    }


def test_loads_escapes_and_unicode() -> None:
    document = (
        "short=\\t\\n\\r\\f\\b\\z\\'\\\"\\\\\\141\n"
        "snowman=\\u2603\n"
        "goat=\\uD83D\\uDC10\n"
        "raw-pair=\ud83d\udc10\n"
        "mixed-pair=\\uD83D\udc10\n"
        "isolated=\ud800\n"
    )

    assert dotproperties.loads(document) == {
        "short": "\t\n\r\fbz'\"\\141",
        "snowman": "☃",
        "goat": "🐐",
        "raw-pair": "🐐",
        "mixed-pair": "🐐",
        "isolated": "\ud800",
    }


@pytest.mark.parametrize(
    "document",
    [
        "key=\\u123",
        "key=\\u12G4",
        "key=\\uu123",
        "key=\\u123 ",
        "key=\\u\uff11\uff12\uff13\uff14",
    ],
)
def test_loads_rejects_malformed_unicode_escape(document: str) -> None:
    with pytest.raises(ValueError, match="malformed"):
        dotproperties.loads(document)


def test_loads_bytes_are_iso_8859_1_and_text_is_unicode() -> None:
    assert dotproperties.loads(b"word=ol\xe1") == {"word": "olá"}
    assert dotproperties.loads("word=你好") == {"word": "你好"}


def test_loads_only_cr_and_lf_as_natural_line_terminators() -> None:
    assert dotproperties.loads("key=left\u0085middle\u2028right\rnext=value") == {
        "key": "left\u0085middle\u2028right",
        "next": "value",
    }


def test_continuation_uses_odd_backslash_runs() -> None:
    document = (
        "odd=one" + "\\" * 3 + "\r\n  two\n"
        "even=three" + "\\" * 2 + "\n"
        "next=four\n"
        "# ignored" + "\\" + "\n"
        "last=value" + "\\"
    )

    assert dotproperties.loads(document) == {
        "odd": "one\\two",
        "even": "three\\",
        "next": "four",
        "last": "value",
    }


def test_empty_continuation_follows_openjdk_line_reader_behavior() -> None:
    assert dotproperties.loads("\\\n\t\r! comment\nkey=value") == {"key": "value"}
    assert dotproperties.loads("\\\n" * 1_000 + "key=value") == {"key": "value"}
    assert dotproperties.loads("\\") == {"": ""}


class OneByteReader(BytesIO):
    def __init__(self, data: bytes) -> None:
        super().__init__(data)
        self.read_sizes: list[int | None] = []

    def read(self, size: int | None = -1, /) -> bytes:
        self.read_sizes.append(size)
        if size is None or size < 0:
            raise AssertionError("load() attempted an unbounded read")
        return super().read(min(size, 1))


def test_load_reads_bounded_chunks_across_every_boundary() -> None:
    stream = OneByteReader(
        b"a=one\\\r\n two\nstandalone=cr\rnext=value\nunicode=\\u2603\n"
    )

    assert dotproperties.load(stream) == {
        "a": "onetwo",
        "standalone": "cr",
        "next": "value",
        "unicode": "☃",
    }
    assert stream.read_sizes
    assert all(size is not None and size > 0 for size in stream.read_sizes)
    assert not stream.closed

    text_stream = StringIO("text=already decoded")
    assert dotproperties.load(text_stream) == {"text": "already decoded"}
    assert not text_stream.closed


class InvalidReader:
    def read(self, size: int = -1, /) -> None:
        return None


def test_load_rejects_invalid_stream_chunks() -> None:
    with pytest.raises(TypeError, match="str or bytes"):
        dotproperties.load(cast(BytesIO, InvalidReader()))


class RecordingTextStream(StringIO):
    def __init__(self) -> None:
        super().__init__()
        self.flush_calls = 0

    def flush(self) -> None:
        self.flush_calls += 1
        super().flush()


def test_dump_preserves_mapping_order_and_is_java_compatible() -> None:
    mapping = {
        "snow": "☃",
        "a:b": "c=d",
        "goat": "🐐",
        " leading key": " leading value ",
    }

    assert dotproperties.dumps(mapping) == (
        "snow=\\u2603\n"
        "a\\:b=c\\=d\n"
        "goat=\\uD83D\\uDC10\n"
        "\\ leading\\ key=\\ leading value \n"
    )


def test_ensure_ascii_false_keeps_unicode_readable() -> None:
    assert dotproperties.dumps({"snow": "☃", "goat": "🐐"}, ensure_ascii=False) == (
        "snow=☃\ngoat=🐐\n"
    )


def test_round_trip_special_characters() -> None:
    mapping = {
        "": "",
        " key:=#!": " \tline\nnext\r\f\\\x00",
        "unicode": "Olá, 世界 🐐",
        "isolated-surrogate": "\ud800",
    }

    assert dotproperties.loads(dotproperties.dumps(mapping)) == mapping
    assert (
        dotproperties.loads(dotproperties.dumps(mapping, ensure_ascii=False)) == mapping
    )


def test_dump_validates_before_writing_and_leaves_stream_open() -> None:
    stream = RecordingTextStream()
    invalid = cast(Mapping[str, str], {"valid": "value", 1: "not a string"})

    with pytest.raises(TypeError, match="keys and values"):
        dotproperties.dump(invalid, stream)

    assert stream.getvalue() == ""
    assert not stream.closed

    dotproperties.dump({"key": "value"}, stream)
    assert stream.getvalue() == "key=value\n"
    assert stream.flush_calls == 0
    assert not stream.closed


def test_public_functions_reject_invalid_container_types() -> None:
    with pytest.raises(TypeError, match="str or bytes"):
        dotproperties.loads(cast(str, bytearray(b"key=value")))
    with pytest.raises(TypeError, match="mapping"):
        dotproperties.dumps(cast(Mapping[str, str], [("key", "value")]))
