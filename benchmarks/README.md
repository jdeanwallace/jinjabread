# Benchmarks

Manual, run-when-curious performance checks. Not part of CI — perf is
machine-dependent, so a threshold assertion would just be flaky.

## HTML pretty-printing

`benchmark_prettify.py` times `prettify_html` against the HTML pretty-printers
people commonly reach for, across a few input sizes, reporting each one's absolute
cost (ms/call) and its cost relative to `jinjabread`.

```bash
uv sync --group bench          # installs the optional comparison libraries
python benchmarks/benchmark_prettify.py
```

The `bench` dependency group provides the in-process Python pretty-printers:
`bs4.prettify`, `prettierfier`, and HTML Tidy (via `pytidylib`). Two of the popular
options need something extra and are skipped (with a hint) when absent:

- **HTML Tidy** needs the system `libtidy` library (e.g. `apt install libtidy58`
  or `brew install tidy-html5`); it runs in-process via `pytidylib`.
- **Prettier** and **js-beautify** need Node on your PATH (`npm install -g prettier
  js-beautify`). They are timed inside a single Node process via `node_bench.js`, so
  their figures exclude Node startup and are comparable to the in-process ones.

The tools don't produce identical output, so treat the numbers as relative cost,
not a ranking.

## Tradeoffs vs jinjabread's needs

Speed is only half the story — the tools differ in *what they do*. jinjabread needs
three correctness properties, and no off-the-shelf tool provides all three:

1. normalize messy Jinja/Markdown output into clean, consistent indentation;
2. preserve rendering — never inject whitespace inside or around inline elements;
3. be idempotent.

The figures below come from running each tool through the test suite's
render-invariance and idempotence oracle (`tests/invariants.py`) over the corpus of
137 cases (reproduce with `python benchmarks/capabilities.py`). jinjabread is the
reference row — it meets all three by construction, since that's what its tests
enforce — and the rest is where the off-the-shelf options fall short:

- **lxml `pretty_print`** — fast and already a dependency, but doesn't normalize
  messy input and is badly non-idempotent (16/137 — re-prettifying keeps changing
  it), and injects whitespace around inline elements (render-invariant 125/137).
  Misses 1–3.
- **bs4 `.prettify()`** — normalizes and is idempotent, but puts every tag on its
  own line, breaking inline rendering (render-invariant 123/137 — the original
  bug). Misses 2.
- **prettierfier** — nearly render-invariant (134/137) and idempotent, but it is a
  post-processor: it does *not* normalize messy input (it leaves the blank lines and
  ragged indentation), and it's unmaintained (Py3.7, raw-string parsing). Misses 1.
- **HTML Tidy** (`pytidylib`) — fast and normalizes, but rewrites a fragment into a
  whole document (adds doctype/html/head/body), which changes the structure
  (render-invariant 1/137) — it's a document cleaner, not an in-place
  pretty-printer. Misses 2.
- **Prettier** (Node) — the gold-standard formatter, normalizes and is
  whitespace-aware, but errors on 21/137 of our fragment inputs and isn't fully
  render-invariant or idempotent here (112/137, 116/137). Misses 2, 3.
- **js-beautify** (Node) — render-invariant (129/137) and idempotent, but doesn't
  normalize messy input. Misses 1.

Every one of these fails at least one of the three requirements — which is why
jinjabread has its own serializer instead of wrapping one of them.

Packaging is a secondary point, not the deciding one: Prettier and js-beautify need
a Node runtime and HTML Tidy needs the system libtidy library, which is friction for
`pip install jinjabread`. (jinjabread already depends on lxml — a C library shipped
as wheels — so the bar is "a normal pip dependency", not "pure Python".)
