from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

import dotproperties

_REFERENCE_SOURCE = Path(__file__).parent / "interop" / "JavaPropertiesReference.java"


@pytest.fixture(scope="session")
def java_reference(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, Path]:
    """Compile the Java 8-compatible reference with the active JDK."""
    java = shutil.which("java")
    javac = shutil.which("javac")
    if java is None or javac is None:
        pytest.skip("Java runtime and compiler are not installed")

    probe = subprocess.run(
        [javac, "-version"],
        capture_output=True,
        check=False,
        text=True,
    )
    if probe.returncode != 0:
        pytest.skip("Java compiler is not usable")

    classes = tmp_path_factory.mktemp("java-properties-reference")
    subprocess.run(
        [str(javac), "-d", str(classes), str(_REFERENCE_SOURCE)],
        capture_output=True,
        check=True,
        text=True,
    )
    return str(java), classes


def _run_reference(
    reference: tuple[str, Path],
    arguments: Sequence[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    java, classes = reference
    return subprocess.run(
        [str(java), "-cp", str(classes), "JavaPropertiesReference", *arguments],
        capture_output=True,
        check=check,
        text=True,
    )


def _java_units(value: str) -> str:
    return value.encode("utf-16-be", errors="surrogatepass").hex().upper()


def _encoded_mapping(mapping: Mapping[str, str]) -> dict[str, str]:
    return {_java_units(key): _java_units(value) for key, value in mapping.items()}


def _read_reference_mapping(output: str) -> dict[str, str]:
    properties: dict[str, str] = {}
    for line in output.splitlines():
        key, value = line.split("\t", 1)
        properties[key] = value
    return properties


def _load_with_java(
    reference: tuple[str, Path],
    mode: str,
    source: Path,
) -> dict[str, str]:
    result = _run_reference(reference, [mode, str(source)])
    return _read_reference_mapping(result.stdout)


def _java_major_version(reference: tuple[str, Path]) -> int:
    version = _run_reference(reference, ["version"]).stdout.strip()
    return int(version.split(".", 1)[1] if version.startswith("1.") else version)


def _write_reference_mapping(mapping: Mapping[str, str], destination: Path) -> None:
    lines = (
        f"{_java_units(key)}\t{_java_units(value)}\n" for key, value in mapping.items()
    )
    destination.write_text("".join(lines), encoding="ascii")


@pytest.mark.interop
def test_java_and_python_load_the_same_byte_document(
    java_reference: tuple[str, Path],
    tmp_path: Path,
) -> None:
    document = (
        b"escaped\\ key : value\\\r\n"
        b"  continued\n"
        b"latin=ol\xe1\n"
        b"goat=\\uD83D\\uDC10\n"
        b"isolated=\\uD800\n"
        b"unknown=\\z\n"
        b"duplicate=first\n"
        b"duplicate=last\n"
        b"trailing=value\\"
    )
    source = tmp_path / "input.properties"
    source.write_bytes(document)

    assert _load_with_java(java_reference, "load-bytes", source) == _encoded_mapping(
        dotproperties.loads(document)
    )


@pytest.mark.interop
def test_empty_continuation_before_comment_documents_openjdk_8_behavior(
    java_reference: tuple[str, Path],
    tmp_path: Path,
) -> None:
    document = b"\\\n# comment after an empty continuation\n"
    source = tmp_path / "input.properties"
    source.write_bytes(document)

    python_mapping = dotproperties.loads(document)
    java_mapping = _load_with_java(java_reference, "load-bytes", source)

    assert python_mapping == {}
    if _java_major_version(java_reference) == 8:
        # The Java 8 API defines the second natural line as a comment, while
        # this pinned OpenJDK 8 LineReader parses it as property data:
        # https://docs.oracle.com/javase/8/docs/api/java/util/Properties.html#load-java.io.Reader-
        # https://github.com/openjdk/jdk8u-dev/blob/e076e1972330d7d4f9351cd5c2f033c6fbde2b12/jdk/src/share/classes/java/util/Properties.java#L421-L524
        assert java_mapping == _encoded_mapping(
            {"#": "comment after an empty continuation"}
        )
    else:
        assert java_mapping == python_mapping


@pytest.mark.interop
def test_java_and_python_load_the_same_reader_document(
    java_reference: tuple[str, Path],
    tmp_path: Path,
) -> None:
    document = "snow=☃\ngoat=🐐\nline-separator=left\u2028right\n"
    source = tmp_path / "input.properties"
    source.write_bytes(document.encode())

    assert _load_with_java(java_reference, "load-reader", source) == _encoded_mapping(
        dotproperties.loads(document)
    )


@pytest.mark.interop
def test_java_loads_python_ascii_and_unicode_output(
    java_reference: tuple[str, Path],
    tmp_path: Path,
) -> None:
    mapping = {
        "a:b": " leading value",
        "snow": "☃",
        "goat": "🐐",
        "": "",
    }

    ascii_source = tmp_path / "ascii.properties"
    ascii_source.write_bytes(
        dotproperties.dumps(
            mapping,
            sort_keys=True,
            comments="Generated\nfor Java",
        ).encode("ascii")
    )
    assert _load_with_java(
        java_reference, "load-bytes", ascii_source
    ) == _encoded_mapping(mapping)

    unicode_source = tmp_path / "unicode.properties"
    unicode_source.write_bytes(
        dotproperties.dumps(
            mapping,
            ensure_ascii=False,
            sort_keys=True,
            comments="生成",
        ).encode()
    )
    assert _load_with_java(
        java_reference, "load-reader", unicode_source
    ) == _encoded_mapping(mapping)


@pytest.mark.interop
def test_python_sort_order_matches_java_string_order(
    java_reference: tuple[str, Path],
    tmp_path: Path,
) -> None:
    mapping = {
        "\ue000": "private-use",
        "\U00010000": "supplementary",
        "\ud800": "isolated-surrogate",
        "z": "last-ascii",
        "a": "first-ascii",
    }
    document = dotproperties.dumps(mapping, sort_keys=True)
    source = tmp_path / "sorted.properties"
    source.write_text(document, encoding="ascii")

    java_order = list(_load_with_java(java_reference, "load-bytes", source))
    python_order = [_java_units(key) for key in dotproperties.loads(document)]

    assert python_order == java_order


@pytest.mark.interop
def test_python_loads_java_byte_and_writer_output(
    java_reference: tuple[str, Path],
    tmp_path: Path,
) -> None:
    mapping = {
        "a:b": " leading value",
        "snow": "☃",
        "goat": "🐐",
        "": "",
    }
    source = tmp_path / "mapping.txt"
    _write_reference_mapping(mapping, source)

    byte_output = tmp_path / "bytes.properties"
    _run_reference(java_reference, ["store-bytes", str(source), str(byte_output)])
    assert dotproperties.loads(byte_output.read_bytes()) == mapping

    writer_output = tmp_path / "writer.properties"
    _run_reference(java_reference, ["store-writer", str(source), str(writer_output)])
    assert dotproperties.loads(writer_output.read_text(encoding="utf-8")) == mapping


@pytest.mark.interop
def test_java_and_python_reject_malformed_unicode_escape(
    java_reference: tuple[str, Path],
    tmp_path: Path,
) -> None:
    source = tmp_path / "invalid.properties"
    source.write_bytes(b"key=\\u123 ")

    with pytest.raises(ValueError, match="malformed"):
        dotproperties.loads(source.read_bytes())

    result = _run_reference(
        java_reference,
        ["load-bytes", str(source)],
        check=False,
    )
    assert result.returncode != 0
    assert "IllegalArgumentException" in result.stderr
