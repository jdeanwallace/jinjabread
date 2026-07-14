"""Property tests: pretty-printing must preserve rendering and be idempotent.

The oracle in `tests.invariants` decides correctness without a golden string, so
these tests cover far more than the hand-written snapshot tests: a curated corpus
and a hypothesis generator both assert the same invariants.
"""

import unittest

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests import invariants

# Every input must satisfy render-invariance and idempotence.
CORPUS = [
    '<p>So as a form of <a href="/x">nesting</a>, we built our own.</p>',
    "<p>one <em>two</em> three <strong>four</strong> five</p>",
    "<p>Use <code>x = 1</code> here.</p>",
    "<pre>def f():\n    return 1\n\n    return 2\n</pre>",
    "<pre><code>a = 1\n  b = 2\n\nc = 3</code></pre>",
    "<div><script>if (a &lt; b) { run(); }</script></div>",
    "<div><ul><li>One</li><li>Two</li></ul></div>",
    "<table><tr><td>a</td><td>b</td></tr></table>",
    "<div><p>first</p><p>second</p></div>",
    '<main><h1>Title</h1><p>Body with <a href="/x">a link</a>.</p></main>',
    "<div><!-- a comment -->and text after it</div>",
    # Block text adjacent to an inline element must not gain a space.
    '<p>(<a href="/x">link</a>)</p>',
    "<p>foo<em>bar</em></p>",
    "<p>line one<br/>line two</p>",
    # A block ending in an inline element must stay idempotent.
    "<p><em>a</em> <strong>b</strong></p>",
    "<p><em>a</em><strong>b</strong></p>",
    # Nested inline runs with significant inter-word whitespace.
    "<p>a <em>b <strong>c</strong> d</em> e</p>",
    # Entities in text and attributes must round-trip.
    "<p>Terms &amp; conditions: 1 &lt; 2 &gt; 0.</p>",
    '<p>See <a href="/s?a=1&amp;b=2" title="A &amp; B">results</a>.</p>',
    # A void inline element mid-sentence.
    '<p>Here is <img src="/i.png" alt="a picture"> inline.</p>',
    # Deeply nested block structure stays indented.
    "<div><section><ul><li>x</li><li>y</li></ul></section></div>",
    # Preformatted content with entities is preserved.
    "<pre>if x &lt; y &amp;&amp; y &gt; z:\n    go()\n</pre>",
]


class CorpusInvariantTest(unittest.TestCase):
    def test_corpus_is_invariant(self):
        for html in CORPUS:
            with self.subTest(html=html):
                invariants.assert_prettify_invariant(html)


# --- Generated inputs -------------------------------------------------------

_words = st.text("abcde", min_size=1, max_size=4)
_ws = st.sampled_from(["", " ", "  ", "\n", "\n  "])
_inline_tags = st.sampled_from(
    [
        "em",
        "strong",
        "code",
        "span",
        "b",
        "i",
        "mark",
        "small",
        "sub",
        "sup",
        "u",
        "abbr",
    ]
)
_flow_tags = st.sampled_from(["div", "section"])


def _wrap(tag, content):
    return f"<{tag}>{content}</{tag}>"


def _join(parts):
    return "".join(whitespace + piece for whitespace, piece in parts)


# Inline content: words, line breaks, and nested inline elements, joined with
# arbitrary (possibly significant) whitespace.
_inline = st.recursive(
    st.one_of(_words, st.just("<br/>"), st.just('<img src="x" alt="y"/>')),
    lambda kids: st.one_of(
        st.builds(_wrap, _inline_tags, kids),
        st.builds(_join, st.lists(st.tuples(_ws, kids), min_size=2, max_size=3)),
    ),
    max_leaves=6,
)

_pre = st.builds(
    lambda text: f"<pre>{text}</pre>", st.text("abc \n", min_size=1, max_size=8)
)
_paragraph = st.builds(lambda content: f"<p>{content}</p>", _inline)

# Block content: paragraphs, preformatted blocks, inline runs, and nested flow
# containers (div/section, which may legally contain blocks).
_block = st.recursive(
    st.one_of(_inline, _pre, _paragraph),
    lambda kids: st.one_of(
        st.builds(_wrap, _flow_tags, kids),
        st.builds(_join, st.lists(st.tuples(_ws, kids), min_size=2, max_size=3)),
    ),
    max_leaves=6,
)

_documents = st.builds(lambda body: f"<div>{body}</div>", _block)


class GeneratedInvariantTest(unittest.TestCase):
    @settings(
        max_examples=400,
        deadline=None,
        derandomize=True,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(html=_documents)
    def test_generated_inputs_are_invariant(self, html):
        invariants.assert_prettify_invariant(html)
