# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Versions are derived from git tags via `setuptools_scm`.

## [Unreleased]

### Fixed

- HTML pretty-printing no longer breaks inline (phrasing) elements. Elements such
  as `<a>`, `<em>`, `<strong>` and `<code>` are now treated as atomic: their
  contents are never reflowed and no whitespace is injected inside them or between
  them and adjacent text or punctuation (e.g. `<a href="/x">nesting</a>,` keeps the
  comma tight against the link). Block-level structure is still indented.
- Whitespace-sensitive elements (`<pre>`, `<textarea>`) and raw-text elements
  (`<script>`, `<style>`) are now preserved verbatim instead of having their
  whitespace collapsed or their content HTML-escaped.
- Significant whitespace between inline elements and neighbouring text is preserved,
  so prose like `one <em>two</em> three` no longer renders as `one twothree`.
- Pretty-printing is now idempotent: prettifying already-pretty output is a no-op.

### Changed

- Replaced the `beautifulsoup4` runtime dependency with `lxml`, which the HTML
  serializer now uses.
