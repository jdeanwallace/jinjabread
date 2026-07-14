# Benchmarks

Manual, run-when-curious performance checks. Not part of CI — perf is
machine-dependent, so a threshold assertion would just be flaky.

## HTML pretty-printing

`benchmark_prettify.py` times `prettify_html` against the HTML pretty-printers
people commonly reach for, across a few input sizes:

```bash
uv pip install beautifulsoup4 prettierfier   # optional comparison libraries
python benchmarks/benchmark_prettify.py
```

It measures the in-process Python pretty-printers — jinjabread, lxml's
`pretty_print`, `bs4.prettify`, and `prettierfier`. The other popular tools
(Prettier, js-beautify, HTML Tidy) run out of process (Node/C), so a per-call
in-process comparison isn't meaningful; Prettier is timed separately if it is on
your PATH, labelled as including process startup.

The tools don't produce identical output, so treat the numbers as relative cost,
not a ranking.
