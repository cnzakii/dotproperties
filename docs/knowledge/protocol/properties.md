---
title: Java Properties line-oriented format
description: Normative grammar, encoding, escaping, storage, and JDK-version boundaries for java.util.Properties.
topics: [java-properties, grammar, encoding, escaping, jdk8, jdk25]
checked_at: 2026-07-31
---

# Java Properties Line-Oriented Format

## Governing Sources

The format is specified by the `load(Reader)`, `load(InputStream)`,
`store(Writer, String)`, and `store(OutputStream, String)` contracts in
[`java.util.Properties` for Java 8][jdk8] and
[`java.util.Properties` for Java 25][jdk25]. The
[Java Language Specification §3.3][jls-unicode] defines the referenced
`\uXXXX` notation, but the Properties API documents its deliberate
differences from Java source-literal escapes.

The current [OpenJDK `Properties.java` source][openjdk-properties] is observed
practice under GPLv2 with the Classpath Exception. It is useful as a reference
for edge cases and implementation shape, not source to copy into an unrelated
implementation.

These sources and runtimes have distinct roles: the Java SE API defines the
format contract, OpenJDK supplies implementation evidence for edge cases, and
Eclipse Temurin supplies the OpenJDK builds used for interoperability tests.

## Lines And Continuations

A natural line ends at LF, CR, CRLF, or end of stream. A logical line may join
natural lines when the terminator is preceded by an odd-length contiguous run
of backslashes. One backslash, the terminator, and leading space, tab, or form
feed on the following natural line are removed. An even-length run does not
continue the line.

Only ASCII space (`U+0020`), tab (`U+0009`), and form feed (`U+000C`) count as
format whitespace. A blank natural line is ignored. A comment line is ignored
when its first non-whitespace character is `#` or `!`; comment lines do not
continue, even if they end in a backslash.

## Key And Value Boundaries

After leading format whitespace is removed, the key ends before the first
unescaped `=`, `:`, space, tab, or form feed. Whitespace after the key is
discarded; one optional unescaped `=` or `:` and following whitespace are also
discarded. The remainder is the raw value. A line with no delimiter has an
empty value, and an initial delimiter permits an empty key.

Escaping makes separators and whitespace part of a key. Loading repeated keys
updates the same table, so the last value wins.

## Escape Processing

The recognized short escapes are `\t`, `\n`, `\r`, and `\f`; `\\` represents
a backslash through the general rule. `\u` must be followed by exactly four
hexadecimal digits. Only one `u` is allowed. A malformed Unicode escape is an
error.

Octal escapes are not recognized, `\b` means `b`, and a backslash before any
other character is silently discarded. Quotes do not need escaping. A
supplementary Unicode character is represented in the Java file model by two
UTF-16 surrogate escapes, such as `\uD83D\uDC10`.

## Text And Byte Streams

`load(Reader)` consumes characters supplied by the caller. `load(InputStream)`
maps each byte through ISO-8859-1. `store(OutputStream, ...)` also uses
ISO-8859-1 and escapes property characters below `U+0020` or above `U+007E`.
`store(Writer, ...)` can write Unicode characters directly.

These explicit encodings are unaffected by [JEP 400][jep400], which changed the
default charset in JDK 18. `PropertyResourceBundle(InputStream)` is a different
API: since Java 9 it attempts UTF-8 and may fall back to ISO-8859-1, whereas its
[Java 8 contract][prb8] used ISO-8859-1. That change does not alter
`Properties.load(InputStream)`.

## Storage And Version Boundaries

Both Java 8 and Java 25 store `key=value`, escape all spaces in keys and the
first leading space in a value, escape `#`, `!`, `=`, and `:`, flush the
destination, and leave it open.

When the Java `store` methods receive non-null comments, they first write `#`,
the comment text, and a line separator. CR, LF, and CRLF inside the text become
line separators. A continued comment line receives a leading `#` unless its
next character is already `#` or `!`. Java then writes a separate date comment.
The `Writer` overload can retain Unicode comments, while the `OutputStream`
overload writes comments through ISO-8859-1 and escapes characters outside
Latin-1.

Java 8 does not specify entry order. Java 25 requires the natural ordering of
keys for the normal `Properties.entrySet()` and documents the
`java.properties.date` system property for reproducible date comments. These
are storage-policy differences; the core line grammar and byte encoding remain
the same in the two API specifications.

## Project Serialization Choices

`dotproperties` keeps Java's optional header-comment structure but does not add
the storage method's automatic date comment. It uses LF for deterministic text
output, applies `ensure_ascii` to the complete document, preserves mapping order
by default, and exposes Java's UTF-16 key order through `sort_keys=True`.

OpenJDK 25 reads input through an 8192-byte or 8192-character buffer and grows
the current logical-line buffer as needed. Neither the Java API nor that
implementation sets a document-size, logical-line, or entry-count limit.

The pinned OpenJDK 8 source has one observed loading difference at the boundary
between continuations and comments. If a logical line contains no data before
a continuation and the next natural line begins with `#` or `!`, its
[`LineReader` implementation][openjdk8-properties] treats that marker as
property data. The Java 8 API contract still defines that natural line as a
comment, while the pinned [OpenJDK 11 implementation][openjdk11-properties]
ignores it. `dotproperties` follows the documented rule.

Long-term support is a vendor lifecycle designation, not part of the
line-format specification. The [Adoptium support roadmap][temurin-support]
lists Temurin 8, 11, 17, 21, and 25 as supported LTS release lines. Selecting
those versions for interoperability testing covers the runtime lines supported
by the tested OpenJDK distribution without implying different Properties
grammars.

The XML representation is a separate format with separate methods and encoding
rules. It should not be inferred from the line-oriented grammar.

[jdk8]: https://docs.oracle.com/javase/8/docs/api/java/util/Properties.html
[jdk25]: https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Properties.html
[jls-unicode]: https://docs.oracle.com/javase/specs/jls/se25/html/jls-3.html#jls-3.3
[openjdk-properties]: https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/Properties.java
[openjdk8-properties]: https://github.com/openjdk/jdk8u-dev/blob/e076e1972330d7d4f9351cd5c2f033c6fbde2b12/jdk/src/share/classes/java/util/Properties.java
[openjdk11-properties]: https://github.com/openjdk/jdk11u-dev/blob/24a7cee41dbe81cb320e900712e780c3df08bbd0/src/java.base/share/classes/java/util/Properties.java
[temurin-support]: https://adoptium.net/support/
[jep400]: https://openjdk.org/jeps/400
[prb8]: https://docs.oracle.com/javase/8/docs/api/java/util/PropertyResourceBundle.html
