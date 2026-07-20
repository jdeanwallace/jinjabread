#!/usr/bin/env python3
"""Grade the HTML pretty-printers against jinjabread's correctness bar.

A manual, run-when-curious companion to benchmark_prettify.py. It runs each
available pretty-printer over the test corpus through the render-invariance and
idempotence oracle from tests/invariants.py, and probes whether it normalizes
messy input, the properties jinjabread needs. See README.md for the per-tool
tradeoffs this produces. The comparators are not project dependencies; install
whichever ones you want (see README.md for pinned versions):

    pip install beautifulsoup4 prettierfier pytidylib   # in-process Python
    npm install -g prettier js-beautify                 # the Node pretty-printers
    python benchmarks/capabilities.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark_prettify import in_process_printers
from tests import invariants
from tests.test_html5lib_corpus import KEPT_INPUTS
from tests.test_prettify_invariants import CORPUS

CASES = CORPUS + KEPT_INPUTS
MESSY = "<div>\n\n   <p>Hi  <a href='/x'>x</a></p>\n\n\n   <ul>\n<li>a</li>\n    <li>b</li></ul></div>"


def _node_formatter(argv):
    binary = shutil.which(argv[0])
    if not binary:
        return None
    return lambda h: subprocess.run(
        [binary, *argv[1:]], input=h, capture_output=True, text=True, check=True
    ).stdout


def formatters():
    # jinjabread is the first row, as the reference: it meets the bar by
    # construction. The rows that matter are where the alternatives fall short.
    tools = dict(in_process_printers())
    for name, argv in [
        ("prettier", ["prettier", "--parser", "html"]),
        ("js-beautify", ["html-beautify", "-"]),
    ]:
        formatter = _node_formatter(argv)
        if formatter:
            tools[name] = formatter
    return tools


def grade(formatter):
    render = idempotent = errors = 0
    for html in CASES:
        try:
            pretty = formatter(html)
            render += invariants.render_signature(html) == invariants.render_signature(
                pretty
            )
            idempotent += formatter(pretty) == pretty
        except Exception:
            errors += 1
    try:
        normalizes = not re.search(r"\n[ \t]*\n[ \t]*\n", formatter(MESSY))
    except Exception:
        normalizes = None
    return render, idempotent, errors, normalizes


def main():
    total = len(CASES)
    columns = f"  {'pretty-printer':<18}{'render-inv':>12}{'idempotent':>12}{'errors':>8}{'normalizes':>12}"
    print(columns)
    for name, formatter in formatters().items():
        render, idempotent, errors, normalizes = grade(formatter)
        shown = {True: "yes", False: "no", None: "?"}[normalizes]
        print(
            f"  {name:<18}{f'{render}/{total}':>12}"
            f"{f'{idempotent}/{total}':>12}{errors:>8}{shown:>12}"
        )
    print("\nThe bar is render-invariance, idempotence, and normalizing messy")
    print("template output. See README.md for the per-tool tradeoffs.")


if __name__ == "__main__":
    main()
