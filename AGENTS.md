# dotproperties

`dotproperties` is a zero-runtime-dependency Python package for the classic
line-oriented Java Properties format.

## Repository Map

- `src/dotproperties/__init__.py`: four operations and package version metadata
- `src/dotproperties/_parser.py`: chunk, line, entry, and escape parsing
- `src/dotproperties/_writer.py`: validation, ordering, and escaping
- `tests/`: observable format and stream behavior
- `docs/knowledge/`: source-based format, parser, Python, and packaging facts

## Project Invariants

- Keep runtime dependencies at zero unless a demonstrated requirement cannot be
  met by the standard library.
- Keep the public API to `load`, `loads`, `dump`, and `dumps` unless a new
  Properties semantic requires caller control.
- Treat `str` input as decoded text and byte input as ISO-8859-1.
- Keep XML, defaults chains, interpolation, timestamp comments, and lossless
  document editing out until explicitly requested.

## Compatibility

- Preserve Python 3.10 syntax and API compatibility on Linux, macOS, and
  Windows. Use Python 3.12 for the default development environment.
- Pass `str` or `bytes` command names to `shutil.which`; normalize
  `os.PathLike` values first for Python 3.10 and 3.11 on Windows.

## Working Method

- Inspect affected files, callers, public exports, types, tests, and
  configuration before changing a shared contract.
- Check `docs/knowledge/` first for external facts. Verify mutable claims
  against current primary sources, and keep specifications, official guidance,
  observed implementation behavior, and project choices distinct.
- Implement the smallest coherent change. Do not add adjacent formats,
  compatibility layers, reports, or tooling without a current requirement.
- Preserve bounded reads for file inputs. Test parser changes at the affected
  chunk, line, key/value, and escape boundaries. Validate complete mappings
  before writing so invalid input cannot leave a partial document.
- Add the smallest test that protects changed observable behavior. Do not add
  tests that only restate constants, annotations, or implementation spelling.
- Inspect the final diff for scope drift, stale documentation, personal paths,
  generated debris, and claims unsupported by the checks you ran.

## Code Review Rules

- Keep review tasks read-only unless the user also requests fixes.
- Report a finding only when it has a precise location, a governing contract
  or reproduction, a concrete consequence, consequence-based severity, and the
  smallest credible resolution.
- Do not report style preferences without a consequence, hypothetical risks
  without a present boundary, or unmeasured performance concerns.

## Verification

Run focused tests while editing, then run the complete gate:

```console
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked ty check
uv build
```
