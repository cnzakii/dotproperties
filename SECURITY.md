# Security policy

Security fixes are provided for the latest released version.

## Reporting a vulnerability

Do not report a suspected vulnerability in a public issue.
[Report it privately through GitHub Security Advisories](https://github.com/cnzakii/dotproperties/security/advisories/new).
Include the affected version, a minimal reproducer, the impact, and any known
workaround.

## Parser boundary

`dotproperties` treats input as data. It does not evaluate expressions,
instantiate tagged objects, expand variables, follow includes, or access
external resources.

The package intentionally follows `Properties.load()` in not imposing a total
input-size, logical-line, or entry-count limit. Applications that accept
untrusted input must enforce suitable limits before parsing. Reports of
unexpectedly excessive resource use for a bounded input are welcome.
