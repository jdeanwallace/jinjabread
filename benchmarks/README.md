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
  js-beautify`). They are timed out of process and labelled, since each call spawns
  Node, so their per-call time is dominated by process startup and is not
  comparable to the in-process figures.

The tools don't produce identical output, so treat the numbers as relative cost,
not a ranking.
