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

- **HTML Tidy** needs the system `libtidy` library (e.g. `apt install libtidy5deb1`
  or `brew install tidy-html5`).
- **Prettier** needs Node on your PATH; it is timed separately and labelled, since
  it runs out of process and its per-call time includes Node startup.

js-beautify has no in-process Python HTML formatter, so it is not included.

The tools don't produce identical output, so treat the numbers as relative cost,
not a ranking.
