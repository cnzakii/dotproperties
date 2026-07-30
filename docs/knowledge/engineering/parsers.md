---
title: Text parser architecture and algorithms
description: Grammar selection, scanning, streaming, serialization, performance, and benchmarking guidance grounded in parser theory and production implementations.
topics: [parsers, automata, scanning, streaming, serialization, performance]
checked_at: 2026-07-31
---

# Text Parser Architecture And Algorithms

## Start With The Grammar

Parser families are not interchangeable performance upgrades. Select the least
powerful model that expresses the format:

- A finite-state scanner is sufficient for regular, locally decidable syntax
  such as delimiters, escapes, comments, and line continuations.
- Recursive descent, LL, or LR parsing is appropriate when recursive nesting
  and a context-free grammar are central to the format.
- A parsing expression grammar provides prioritized choice and unlimited
  lookahead. [Packrat parsing][packrat] memoizes that work for linear time at
  the cost of memory proportional to the input.
- Generalized and incremental parsers serve ambiguity, error recovery, syntax
  trees, and repeated edits. [Tree-sitter][tree-sitter] uses GLR-derived
  machinery because source editors need those properties.

Using a stronger parser than the grammar needs adds states, allocation, error
surfaces, and dependencies without lowering the fundamental cost. A parser
that must validate every input unit has an `O(n)` worst-case lower bound.
Optimization therefore reduces interpreter work, allocations, copies, and
unnecessary passes; it does not make general parsing sublinear.

Java Properties is a regular line grammar with bounded local state: whether the
previous natural line continues, the parity of a backslash run, the current
key/value boundary, and the current escape. It does not need a parser generator,
packrat memo table, syntax tree, or recursive grammar.

## Scanning And Search Algorithms

Different search algorithms solve different tokenization problems:

- A direct state machine examines every input unit and is easy to make
  incremental. In an interpreter, however, one Python loop iteration per
  character can dominate the actual grammar work.
- `str.find()` and `str.index()` move substring search into the runtime.
  CPython's [`fastsearch`][cpython-fastsearch] adaptively combines
  Boyer-Moore/Horspool techniques with the Two-Way algorithm, including
  worst-case linear behavior for larger searches.
- A compiled regular expression is useful for finding a small fixed set of
  structural characters or transforming sparse matches. Patterns used on
  untrusted input must avoid ambiguous nested repetition and other
  backtracking shapes that can cause superlinear work. [RE2][re2] illustrates
  the stronger production model of deliberately restricting features to
  guarantee linear time and bounded resources.
- KMP and Boyer-Moore-family algorithms target one non-trivial substring.
  Aho-Corasick targets many string patterns. They do not improve a grammar
  whose structural tokens are a handful of single characters.
- SIMD parsers classify many bytes at once and often separate structural
  indexing from semantic parsing. [`simdjson`][simdjson-paper] demonstrates
  this at native-code speeds, but reproducing it in Python bytecode defeats the
  technique. It becomes relevant only behind an optional native accelerator.

The practical pure-Python pattern is hybrid: let `str`, `bytes`, `re`, or
`io` perform bulk scanning in native code, then use explicit Python state only
where grammar decisions are necessary. “Single pass” is not automatically
faster if that pass executes one Python bytecode loop per character.

## Production Implementation Patterns

The standard library and established parsers use different architectures
because their grammars and contracts differ:

- The Python [`json` module][json-docs] exposes `load`, `loads`, `dump`, and
  `dumps`. Its normal CPython path uses a native scanner and encoder. The pure
  Python encoder uses compiled character-class expressions and replacement
  callbacks for escaping rather than branching over every safe character in
  Python. See the pinned [`json.encoder` source][json-encoder-source].
- [`tomllib`][tomllib-docs] reads the complete binary input, keeps a cursor into
  one string, and combines explicit parser state with `str.index()` and
  compiled expressions. Its [implementation][tomllib-source] demonstrates that
  whole-document buffering can be a deliberate grammar/API choice.
- [`ConfigParser.read_file()`][configparser-docs] consumes an iterable of text
  lines and applies line-oriented state and compiled expressions. INI remains
  a different grammar and its parser must not be reused for Properties.
- YAML is recursive and may contain multiple documents. [PyYAML's
  reader][pyyaml-reader] fills a raw buffer in chunks and feeds a scanner and
  parser; its optional LibYAML binding exists because native acceleration
  matters for that richer grammar.
- OpenJDK's [`Properties.LineReader`][openjdk-properties] uses 8192-unit input
  buffers and an explicit state machine. This is a useful semantic reference,
  but a Java/JIT character loop is not automatically the fastest equivalent in
  CPython.

These examples are evidence for design principles, not templates to copy.

## Standard-Library API Shape

Public API shape does not determine buffering. In
[CPython 3.14.5][json-source], `json.load()` reads the complete document and
delegates to `loads()`. The read-only `tomllib` API follows the same broad
shape, while `ConfigParser.read_file()` accepts an iterable of Unicode lines.

A line grammar can instead use bounded reads while sharing parsing stages
between file and string input. This is an implementation decision behind the
API, not a reason to expose an iterator prematurely.

## Incremental And Streaming Parsing

Incremental input requires every stage to define the state that crosses a chunk
boundary. For a line format this normally includes:

- an unfinished natural line;
- a CR that may be followed by LF in the next chunk;
- an unfinished logical line caused by continuation;
- any token or escape that the selected stage permits to span chunks.

Chunking the transport does not require every semantic stage to operate on
individual chunks. A clean pipeline can first produce complete natural lines,
then logical lines, then entries and decoded fields.

Do not use `str.splitlines()` when a protocol defines only CR and LF:
`splitlines()` recognizes additional Unicode separators. A fixed delimiter
scanner must encode the format's exact line-ending set.

Bounded input reads do not imply bounded parsing. Returning a complete mapping
requires memory proportional to the result, and continuation requires memory
proportional to the longest unfinished logical line. A public entry iterator is
a separate semantic feature, especially when duplicate keys are defined as
last-value-wins.

For chunked line scanners, boundary tests must split CRLF, backslash runs,
Unicode escapes, separators, and arbitrary multicharacter examples across
chunks. A one-character chunk source is a compact completeness check.

## Serialization Algorithms

Serialization has the same `O(n)` lower bound as parsing. Useful constant-factor
techniques are:

- validate caller data before output when partial output would be harmful;
- preserve safe spans unchanged and transform only characters that require an
  escape;
- use a small lookup table for fixed escapes and a slow path for computed
  Unicode escapes;
- accumulate with a list plus `"".join()` or write completed records without
  repeated string concatenation;
- avoid whole-output buffering in `dump()` unless one atomic write is part of
  the contract.

The pure Python JSON encoder's compiled-expression replacement is a good model
for sparse escaping. A hand-written state machine remains appropriate for
decoding when malformed escape detection and exact cursor movement are more
important than sparse substitution.

## Complexity And Security

For untrusted input, document expected time and retained state:

- use linear scanners or simple expressions whose repetition cannot overlap
  ambiguously;
- do not accept caller-supplied expressions as part of the grammar;
- distinguish bounded I/O requests from total CPU and memory limits;
- keep recursive parsing depth bounded when the grammar nests;
- treat packrat's linear time and linear memo storage as a tradeoff, not a free
  guarantee;
- add application-level byte, entry, or line limits when the format itself has
  none.

## Benchmark Discipline

Performance work is incomplete without semantic checks. A useful parser
benchmark must:

1. construct real delimiters and line endings rather than escaped display text;
2. assert the expected entry count and round trip before timing;
3. cover ordinary ASCII, escape-heavy, Unicode, long-line, mixed-newline, and
   chunk-boundary inputs;
4. compare the same interpreter, process conditions, and public behavior;
5. repeat measurements and report both absolute latency and relative change;
6. measure allocation or peak memory when an optimization introduces copies;
7. keep correctness tests authoritative when a faster candidate disagrees.

Small configuration files often make sub-millisecond absolute differences
irrelevant. Retain a benchmark in the repository only when the project intends
to enforce a performance budget; otherwise a one-off benchmark is sufficient
evidence for a focused change.

## Application To Java Properties

The grammar analysis implies the following suitable architecture:

- use bounded reads when incremental file input is required;
- locate exact CR/LF terminators in native code while preserving a one-bit
  cross-chunk CRLF state;
- use a simple fixed expression or state machine to locate the first unescaped
  key separator;
- use explicit logical-line and Unicode-unescape states;
- serialize by substituting only characters selected by fixed, precompiled
  expressions;
- verify implementations with differential tests, one-character chunks, real JDK
  interoperability, and several workload shapes.

KMP, Aho-Corasick, PEG/packrat, GLR, Tree-sitter, SIMD, and a native extension
do not inherently improve this small regular grammar. They become candidates
only if requirements expand to substantial substring sets, recursive or
ambiguous syntax, incremental tree editing, or native acceleration.

[json-docs]: https://docs.python.org/3.14/library/json.html
[json-source]: https://github.com/python/cpython/blob/v3.14.5/Lib/json/__init__.py
[json-encoder-source]: https://github.com/python/cpython/blob/v3.14.5/Lib/json/encoder.py
[tomllib-docs]: https://docs.python.org/3.14/library/tomllib.html
[tomllib-source]: https://github.com/python/cpython/blob/v3.14.5/Lib/tomllib/_parser.py
[configparser-docs]: https://docs.python.org/3.14/library/configparser.html#configparser.ConfigParser.read_file
[cpython-fastsearch]: https://github.com/python/cpython/blob/v3.14.5/Objects/stringlib/fastsearch.h
[pyyaml-reader]: https://github.com/yaml/pyyaml/blob/6.0.3/lib/yaml/reader.py
[openjdk-properties]: https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/Properties.java
[packrat]: https://pdos.csail.mit.edu/~baford/packrat/thesis/
[tree-sitter]: https://tree-sitter.github.io/tree-sitter/
[re2]: https://github.com/google/re2
[simdjson-paper]: https://arxiv.org/abs/1902.08318
