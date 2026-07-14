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

    uv pip install beautifulsoup4 prettierfier
    python benchmarks/benchmark_prettify.py
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
        print("(bs4 not installed — `uv pip install beautifulsoup4`)")

    try:
        import prettierfier

        printers["prettierfier"] = prettierfier.prettify_html
    except ImportError:
        print("(prettierfier not installed — `uv pip install prettierfier`)")

    return printers


def per_call_seconds(func, html):
    timer = timeit.Timer(lambda: func(html))
    number, _ = timer.autorange()
    return min(timer.repeat(repeat=5, number=number)) / number


def main():
    printers = in_process_printers()
    prettier = shutil.which("prettier")

    for size, html in INPUTS.items():
        print(f"\nInput: {size} ({len(html):,} bytes)")
        baseline = None
        for name, func in printers.items():
            seconds = per_call_seconds(func, html)
            baseline = baseline or seconds
            print(f"  {name:<18}{seconds * 1e3:9.3f} ms{seconds / baseline:7.1f}x")
        if prettier:
            seconds = per_call_seconds(
                lambda h: subprocess.run(
                    [prettier, "--parser", "html"],
                    input=h,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout,
                html,
            )
            print(
                f"  {'prettier (node)':<18}{seconds * 1e3:9.3f} ms{seconds / baseline:7.1f}x"
                "   (out-of-process, includes startup)"
            )

    print("\nOutputs differ between tools; read these as relative cost, not a ranking.")


if __name__ == "__main__":
    main()
