"""Executable contract for `prettify_html`.

Each test states one guarantee the pretty-printer makes, or one it deliberately
does not make. The README documents the same contract in prose; keep the two in
sync.
"""

import unittest

import jinjabread
from tests import invariants


class PrettifyContractTest(unittest.TestCase):
    def test_preserves_how_the_page_renders(self):
        """The output renders identically to the input.

        This is the core guarantee. `tests/test_prettify_invariants.py` checks it
        exhaustively over a corpus and generated inputs; this is one example.
        """
        invariants.assert_prettify_invariant(
            '<p>one <em>two</em> three <a href="/x">link</a>.</p>'
        )

    def test_is_idempotent(self):
        """Prettifying already-pretty output changes nothing."""
        once = jinjabread.prettify_html("<div><p>hi</p><p>bye</p></div>")
        self.assertEqual(once, jinjabread.prettify_html(once))

    def test_keeps_preformatted_content_verbatim(self):
        """`pre`, `textarea`, `script`, and `style` content is left untouched."""
        text = "<pre>  two  spaces\tand a tab  </pre>\n"
        self.assertEqual(text, jinjabread.prettify_html(text))

    def test_adds_no_wrapper_around_a_fragment(self):
        """A body-level fragment is emitted as-is, with no wrapper element added."""
        self.assertEqual(
            "<p>\n  a\n</p>\n<p>\n  b\n</p>\n",
            jinjabread.prettify_html("<p>a</p><p>b</p>"),
        )

    def test_parses_and_repairs_markup(self):
        """It is rendering-preserving, not byte-preserving.

        Every page round-trips through lxml's HTML parser, so unclosed and
        misnested tags come back well-formed, matching how a browser reads the
        input. Invalid structure is not preserved verbatim.
        """
        self.assertEqual(
            "<p>\n  unclosed <b>bold</b>\n</p>\n",
            jinjabread.prettify_html("<p>unclosed <b>bold"),
        )
        self.assertEqual(
            "<b><i>x</i></b>\n",
            jinjabread.prettify_html("<b><i>x</b></i>"),
        )

    def test_emits_a_doctype_for_a_whole_document(self):
        """A whole document is emitted as a complete document with a doctype."""
        out = jinjabread.prettify_html("<html><body><p>hi</p></body></html>")
        self.assertTrue(out.startswith("<!DOCTYPE html>\n<html>"))

    def test_treats_a_document_level_fragment_as_a_document(self):
        """A lone document-level element, such as a `<script>`, becomes a document.

        Only body-level content is emitted as a fragment. An element that belongs
        in the document head, such as a standalone `<script>`, is promoted to a
        full document with html/head and a doctype.
        """
        out = jinjabread.prettify_html("<script>x = 1</script>")
        self.assertTrue(out.startswith("<!DOCTYPE html>"))
        self.assertIn("<head>", out)
