#!/usr/bin/env python3
"""Time prettify_html against the HTML pretty-printers people reach for.

A manual, run-when-curious benchmark — not part of CI (perf is machine-dependent,
so a threshold assertion would be flaky). Each pretty-printer is timed end-to-end
(HTML string in -> pretty string out, i.e. parse + serialize) across a few input
sizes, taking the best of several repeats after a warm-up.

This is context, not a verdict: the tools do not produce the same output. lxml's
`pretty_print` doesn't normalize whitespace (it does less), `bs4.prettify` breaks
inline elements, and `prettierfier` post-processes already-clean input.

The Python tools are timed in this process; the Node tools (Prettier, js-beautify)
are timed inside a single Node process via node_bench.js. Every figure therefore
excludes one-off interpreter/process startup, so they are comparable.

The comparators are not project dependencies; install whichever ones you want
(anything missing is skipped with a hint). See README.md for pinned versions:

    pip install beautifulsoup4 prettierfier pytidylib   # in-process Python
    npm install -g prettier js-beautify                 # the Node pretty-printers
    python benchmarks/benchmark_prettify.py

HTML Tidy also needs the system libtidy library.
"""

import json
import os
import shutil
import subprocess
import timeit
from pathlib import Path

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
        print("(bs4 skipped — pip install beautifulsoup4)")

    try:
        import prettierfier

        printers["prettierfier"] = prettierfier.prettify_html
    except ImportError:
        print("(prettierfier skipped — pip install prettierfier)")

    try:
        from tidylib import tidy_document

        tidy_document("<p>x</p>")  # probe: raises OSError if libtidy is absent
        printers["html tidy"] = lambda h: tidy_document(h)[0]
    except ImportError:
        print("(html tidy skipped — pip install pytidylib)")
    except OSError:
        print("(html tidy skipped — install the system libtidy library)")

    return printers


def per_call_seconds(func, html):
    timer = timeit.Timer(lambda: func(html))
    number, _ = timer.autorange()
    return min(timer.repeat(repeat=5, number=number)) / number


def _row(name, ms, relative, note=""):
    return f"  {name:<18}{ms:>10}{relative:>14}   {note}".rstrip()


def node_results():
    """Steady-state per-call seconds for the Node pretty-printers: {tool: {size: s}}.

    Timed inside one Node process (node_bench.js) so the figures exclude Node
    startup and are comparable to the in-process Python ones. Returns {} with a hint
    when Node or the packages are unavailable.
    """
    node = shutil.which("node")
    npm = shutil.which("npm")
    harness = Path(__file__).with_name("node_bench.js")
    if not (node and npm and harness.exists()):
        print(
            "(prettier / js-beautify skipped — Node + `npm install -g prettier js-beautify`)"
        )
        return {}
    node_path = subprocess.run(
        [npm, "root", "-g"], capture_output=True, text=True
    ).stdout.strip()
    result = subprocess.run(
        [node, str(harness)],
        input=json.dumps(INPUTS),
        capture_output=True,
        text=True,
        env={**os.environ, "NODE_PATH": node_path},
    )
    if result.returncode != 0:
        print(
            "(prettier / js-beautify skipped — `npm install -g prettier js-beautify`)"
        )
        return {}
    return json.loads(result.stdout)


def main():
    printers = in_process_printers()
    node = node_results()

    for size, html in INPUTS.items():
        print(f"\nInput: {size} ({len(html):,} bytes)")
        print(_row("pretty-printer", "ms/call", "vs jinjabread"))
        baseline = None
        for name, func in printers.items():
            seconds = per_call_seconds(func, html)
            baseline = baseline or seconds
            print(_row(name, f"{seconds * 1e3:.3f}", f"{seconds / baseline:.1f}x"))
        for tool, per_size in node.items():
            seconds = per_size.get(size)
            if seconds is not None:
                print(
                    _row(
                        f"{tool} (node)",
                        f"{seconds * 1e3:.3f}",
                        f"{seconds / baseline:.1f}x",
                    )
                )

    print("\nms/call is absolute; the last column is relative to jinjabread.")
    print("Outputs differ between tools — read this as relative cost, not a ranking.")


if __name__ == "__main__":
    main()
