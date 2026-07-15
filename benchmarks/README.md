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
four things at once, and no off-the-shelf tool provides all of them:

1. normalize messy Jinja/Markdown output into clean, consistent indentation;
2. preserve rendering — never inject whitespace inside or around inline elements;
3. be idempotent;
4. run pure-Python in-process — no Node or C runtime for a Python site generator.

The correctness figures below come from running each tool through the test suite's
render-invariance and idempotence oracle (`tests/invariants.py`) over the corpus of
137 cases:

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
  pretty-printer — and needs the system libtidy C library. Misses 2 and 4.
- **Prettier** (Node) — the gold-standard formatter, normalizes and is
  whitespace-aware, but needs a Node toolchain (misses 4 for a Python generator),
  errors on 21/137 of our fragment inputs, and isn't fully render-invariant or
  idempotent here (112/137, 116/137).
- **js-beautify** (Node) — render-invariant (129/137) and idempotent, but doesn't
  normalize messy input and needs Node. Misses 1 and 4.

**jinjabread** is 137/137 render-invariant, 137/137 idempotent, normalizes, and is
pure-Python in-process. It's custom because every existing tool misses at least one
of the four needs.
