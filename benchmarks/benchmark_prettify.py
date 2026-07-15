#!/usr/bin/env python3
"""Time prettify_html against the HTML pretty-printers people reach for.

A manual, run-when-curious benchmark — not part of CI (perf is machine-dependent,
so a threshold assertion would be flaky). Each pretty-printer is timed end-to-end
(HTML string in -> pretty string out, i.e. parse + serialize, which is what a build
actually pays) across a few input sizes.

This is context, not a verdict: the tools do not produce the same output. lxml's
`pretty_print` doesn't normalize whitespace (it does less), `bs4.prettify` breaks
inline elements, and `prettierfier` post-processes already-clean input. The popular
non-Python tools (Prettier, js-beautify, HTML Tidy) run out of process (Node/C), so
a per-call in-process comparison would only measure process startup; they are left
out (Prettier is timed separately if it is on PATH, clearly labelled).

Install the optional comparison libraries to include them:

    uv sync --group bench
    python benchmarks/benchmark_prettify.py

HTML Tidy additionally needs the system libtidy library; Prettier needs Node on
PATH. Both are skipped with a hint when absent.
"""

import shutil
import subprocess
import timeit

from jinjabread.utils import prettify_html


def _make_page(sections):
    block = (
        "<section>\n"
        "  <h2>A heading</h2>\n"
        "  <p>Prose with <a href='/x'>a link</a>, <em>emphasis</em>, and "
        "<code>inline code</code> — plus a (parenthetical <a href='/y'>link</a>).</p>\n"
        "  <ul><li>One</li><li>Two</li><li>Three</li></ul>\n"
        "  <pre><code>def f():\n    return 1\n</code></pre>\n"
        "</section>\n"
    )
    return "<main>\n" + block * sections + "</main>\n"


INPUTS = {
    "small": "<p>Hello <a href='/x'>world</a>, this is <em>fine</em>.</p>",
    "medium": _make_page(5),
    "large": _make_page(250),
}


def in_process_printers():
    printers = {"jinjabread": prettify_html}

    import lxml.etree
    import lxml.html

    printers["lxml pretty_print"] = lambda h: lxml.etree.tostring(
        lxml.html.fromstring(h), pretty_print=True, encoding="unicode"
    )

    try:
        import bs4

        printers["bs4 prettify"] = lambda h: bs4.BeautifulSoup(
            h, "html.parser"
        ).prettify()
    except ImportError:
        print("(bs4 skipped — `uv sync --group bench`)")

    try:
        import prettierfier

        printers["prettierfier"] = prettierfier.prettify_html
    except ImportError:
        print("(prettierfier skipped — `uv sync --group bench`)")

    try:
        from tidylib import tidy_document

        tidy_document("<p>x</p>")  # probe: raises OSError if libtidy is absent
        printers["html tidy"] = lambda h: tidy_document(h)[0]
    except ImportError:
        print("(html tidy skipped — `uv sync --group bench`)")
    except OSError:
        print("(html tidy skipped — install the system libtidy library)")

    return printers


def per_call_seconds(func, html):
    timer = timeit.Timer(lambda: func(html))
    number, _ = timer.autorange()
    return min(timer.repeat(repeat=5, number=number)) / number


def _row(name, ms, relative, note=""):
    return f"  {name:<18}{ms:>10}{relative:>14}   {note}".rstrip()


def subprocess_tools():
    # Out-of-process pretty-printers (Node): included when on PATH. Their per-call
    # time includes process startup, so it is not comparable to the in-process
    # figures — the rows are labelled accordingly.
    tools = []
    for name, argv in [
        ("prettier (node)", ["prettier", "--parser", "html"]),
        ("js-beautify (node)", ["html-beautify", "-"]),
    ]:
        binary = shutil.which(argv[0])
        if binary:
            tools.append((name, [binary, *argv[1:]]))
    return tools


def main():
    printers = in_process_printers()
    out_of_process = subprocess_tools()

    for size, html in INPUTS.items():
        print(f"\nInput: {size} ({len(html):,} bytes)")
        print(_row("pretty-printer", "ms/call", "vs jinjabread"))
        baseline = None
        for name, func in printers.items():
            seconds = per_call_seconds(func, html)
            baseline = baseline or seconds
            print(_row(name, f"{seconds * 1e3:.3f}", f"{seconds / baseline:.1f}x"))
        for name, argv in out_of_process:
            seconds = per_call_seconds(
                lambda h, a=argv: subprocess.run(
                    a, input=h, capture_output=True, text=True, check=True
                ).stdout,
                html,
            )
            print(
                _row(
                    name,
                    f"{seconds * 1e3:.3f}",
                    f"{seconds / baseline:.1f}x",
                    "out-of-process, includes startup",
                )
            )

    print("\nms/call is absolute; the last column is relative to jinjabread.")
    print("Outputs differ between tools — read this as relative cost, not a ranking.")


if __name__ == "__main__":
    main()
