# html5lib-tests corpus

A third-party corpus of HTML serializer tests, vendored from the html5lib-tests
project and reused to stress-test `prettify_html`.

## Contents

- `data/*.test` — the vendored test files, **verbatim** from html5lib-tests.
  Despite the `.test` extension they are **JSON** (html5lib's convention). Do not
  hand-edit or reformat them: they are pinned byte-for-byte to the upstream commit
  below, and some of their whitespace is the actual test data (the whitespace
  cases). Use the updater to change them.
- `LICENSE` — the upstream MIT license these files are distributed under.

## Provenance

- Source: https://github.com/html5lib/html5lib-tests (the `serializer/` directory)
- Commit: `224991ec10db04f056a89eed8b0bd8695fd2950e`

## Usage

`tests/test_html5lib_corpus.py` loads each file, reuses only the `expected` HTML
strings as inputs to `prettify_html`, and checks them against the render-invariance
and idempotence oracle in `tests/invariants.py`. Inputs that lxml and html5lib
parse differently — bare doctypes, stray end tags, and other document-structure
fragments a content pretty-printer never emits — are filtered out at load time, and
a test guards against the kept set silently shrinking. The everyday test run is
fully offline and deterministic; it never fetches anything.

## Updating

Rolling the corpus forward is a deliberate, reviewed step. Run the updater, then
review the diff and run the suite before committing:

```bash
python3 dev-scripts/update_html5lib_corpus.py             # latest master
python3 dev-scripts/update_html5lib_corpus.py --ref v1.1  # a tag or commit SHA
```

It re-downloads `data/*.test` (and `LICENSE`) at the resolved commit, records that
commit above, and reports which files it added, updated, removed, or left
unchanged. If new upstream cases fail, decide consciously: fix the serializer (a
real find), tune the load-time filter, or exclude the case with a note.
