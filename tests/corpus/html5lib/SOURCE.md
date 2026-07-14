# html5lib-tests corpus

The `*.test` files here are vendored verbatim from the html5lib-tests project.

- Source: https://github.com/html5lib/html5lib-tests (the `serializer/` directory)
- Commit: `224991ec10db04f056a89eed8b0bd8695fd2950e`
- License: MIT — see `LICENSE` in this directory.

To roll this forward, run `python3 dev-scripts/update_html5lib_corpus.py`
(optionally `--ref <tag-or-sha>`), then review the diff and run the suite before
committing.

These are html5lib's serializer tests. jinjabread reuses only the `expected` HTML
strings from each test as inputs to `prettify_html`, checked against the
render-invariance and idempotence oracle in `tests/invariants.py`.

Inputs that lxml and html5lib parse differently — bare doctypes, stray end tags,
and other document-structure fragments a content pretty-printer never emits — are
filtered out at load time. The loader in `tests/test_html5lib_corpus.py` reports how
many inputs it keeps, and a test guards against the kept set silently shrinking.
