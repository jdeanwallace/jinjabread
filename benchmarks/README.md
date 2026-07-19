# Benchmarks

Manual, run-when-curious performance checks. Not part of CI — perf is
machine-dependent, so a threshold assertion would just be flaky.

## HTML pretty-printing

`benchmark_prettify.py` times `prettify_html` against the HTML pretty-printers
people commonly reach for, across a few input sizes, reporting each one's absolute
cost (ms/call) and its cost relative to `jinjabread`.

```bash
python benchmarks/benchmark_prettify.py
```

The comparison pretty-printers are **not** project dependencies — they're only for
these curiosity benchmarks, so install whichever ones you want included and the
benchmark discovers them at runtime (anything missing is skipped with a hint). The
versions these numbers were measured against:

- **BeautifulSoup**, **prettierfier**, **HTML Tidy** — in-process Python, via pip:

  ```bash
  pip install beautifulsoup4==4.15.0 prettierfier==1.0.3 pytidylib==0.3.2
  ```

- **HTML Tidy** also needs the system `libtidy` shared library (HTML Tidy 5.8.0):
  `brew install tidy-html5` (macOS) or your distro's tidy runtime package
  (Debian/Ubuntu: `apt install libtidy5deb1`). `pytidylib` loads it at runtime.
- **Prettier** and **js-beautify** — Node on your PATH:

  ```bash
  npm install -g prettier@3.9.5 js-beautify@2.0.3
  ```

  They are timed inside a single Node process via `node_bench.js`, so their figures
  exclude Node startup and are comparable to the in-process ones.

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
141 cases (install the comparison libraries above, then reproduce with `python
benchmarks/capabilities.py`). jinjabread is the
reference row — it meets all three by construction, since that's what its tests
enforce — and the rest is where the off-the-shelf options fall short:

- **lxml `pretty_print`** — fast and already a dependency, but doesn't normalize
  messy input and is badly non-idempotent (16/141 — re-prettifying keeps changing
  it), and injects whitespace around inline elements (render-invariant 125/141).
  Misses 1–3.
- **bs4 `.prettify()`** — normalizes and is idempotent, but puts every tag on its
  own line, breaking inline rendering (render-invariant 125/141 — the original
  bug). Misses 2.
- **prettierfier** — nearly render-invariant (138/141) and idempotent, but it is a
  post-processor: it does *not* normalize messy input (it leaves the blank lines and
  ragged indentation), and it's unmaintained (Py3.7, raw-string parsing). Misses 1.
- **HTML Tidy** (`pytidylib`) — fast and normalizes, but rewrites a fragment into a
  whole document (adds doctype/html/head/body), which changes the structure
  (render-invariant 1/141) — it's a document cleaner, not an in-place
  pretty-printer. Misses 2.
- **Prettier** (Node) — the gold-standard formatter, normalizes and is
  whitespace-aware, but errors on 21/141 of our fragment inputs and isn't fully
  render-invariant or idempotent here (116/141, 120/141). Misses 2, 3.
- **js-beautify** (Node) — render-invariant (133/141) and idempotent, but doesn't
  normalize messy input. Misses 1.

Every one of these fails at least one of the three requirements — which is why
jinjabread has its own serializer instead of wrapping one of them.

Packaging is a secondary point, not the deciding one: Prettier and js-beautify need
a Node runtime and HTML Tidy needs the system libtidy library, which is friction for
`pip install jinjabread`. (jinjabread already depends on lxml — a C library shipped
as wheels — so the bar is "a normal pip dependency", not "pure Python".)
