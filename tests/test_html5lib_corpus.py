"""Render-invariance over an external, unbiased corpus (html5lib-tests).

We reuse the `expected` HTML strings from html5lib's serializer tests as inputs
(see `corpus/html5lib/SOURCE.md`), keep only the ones lxml and html5lib parse
identically, and assert the same invariants as the rest of the suite.
"""

import json
import unittest
from pathlib import Path

import lxml.html

from tests import invariants

_CORPUS_DIR = Path(__file__).parent / "corpus" / "html5lib"


def _well_formed(html):
    # Keep only inputs lxml and html5lib parse identically: a plain lxml
    # round-trip must not change what html5lib renders. This drops document-
    # structure fragments (bare doctypes, stray end tags) that a content
    # pretty-printer never encounters, which would otherwise register as parser
    # divergence rather than serializer defects.
    try:
        roundtrip = lxml.html.tostring(
            lxml.html.fromstring(html), with_tail=False
        ).decode()
    except Exception:
        return False
    return invariants.render_signature(html) == invariants.render_signature(roundtrip)


def load_corpus():
    """Return (kept_inputs, skipped_count) from the vendored html5lib tests."""
    inputs = []
    for path in sorted((_CORPUS_DIR / "data").glob("*.test")):
        for test in json.loads(path.read_text()).get("tests", []):
            for expected in test.get("expected", []):
                if "<" in expected and expected not in inputs:
                    inputs.append(expected)
    kept = [html for html in inputs if _well_formed(html)]
    return kept, len(inputs) - len(kept)


KEPT_INPUTS, SKIPPED_COUNT = load_corpus()


class Html5libCorpusTest(unittest.TestCase):
    def test_corpus_is_non_trivial(self):
        # Guard against the loader silently going empty, e.g. a path or format
        # change dropping every input.
        self.assertGreater(len(KEPT_INPUTS), 100)

    def test_corpus_is_invariant(self):
        for html in KEPT_INPUTS:
            with self.subTest(html=html):
                invariants.assert_prettify_invariant(html)
