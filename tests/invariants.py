"""Independent oracle for checking that pretty-printing preserves rendering.

These helpers re-derive "what does this HTML render as" from scratch, using
html5lib as a browser-accurate parser. They deliberately share no code with the
lxml-based serializer under test, so a serializer bug surfaces as a mismatch
instead of being masked by the same logic on both sides of the comparison.
"""

import re

import html5lib

from jinjabread.utils import prettify_html

# HTML phrasing (inline) elements, per the HTML specification. Whitespace inside
# and around these is significant; whitespace at block-level boundaries is not.
# This set is the reference ground truth, defined independently of the
# serializer under test.
INLINE_TAGS = frozenset(
    {
        "a",
        "abbr",
        "b",
        "bdi",
        "bdo",
        "br",
        "cite",
        "code",
        "data",
        "dfn",
        "em",
        "i",
        "img",
        "kbd",
        "mark",
        "q",
        "rp",
        "rt",
        "ruby",
        "s",
        "samp",
        "small",
        "span",
        "strong",
        "sub",
        "sup",
        "time",
        "u",
        "var",
        "wbr",
    }
)

# Elements whose text content is whitespace-sensitive or raw. Their content must
# survive pretty-printing byte for byte.
PREFORMATTED_TAGS = frozenset({"pre", "textarea", "script", "style"})


def _localname(name):
    # html5lib etree names are namespaced, e.g. "{http://www.w3.org/1999/xhtml}p".
    return name.rsplit("}", 1)[-1].lower() if isinstance(name, str) else name


def _parse(html):
    return html5lib.parse(html, treebuilder="etree", namespaceHTMLElements=False)


def visible_text(html):
    """Return the text a browser shows, with insignificant whitespace collapsed.

    Each block-level boundary becomes a single separating space, because block
    elements are visually separated regardless of source whitespace. Inline
    boundaries keep their exact spacing, so a lost or added inline space changes
    the result.
    """
    parts = []

    def walk(element):
        tag = _localname(element.tag)
        if tag in ("script", "style"):
            return
        block = tag not in INLINE_TAGS
        if block:
            parts.append(" ")
        if element.text:
            parts.append(element.text)
        for child in element:
            walk(child)
            if child.tail:
                parts.append(child.tail)
        if block:
            parts.append(" ")

    walk(_parse(html))
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def preformatted_text(html):
    """Return the verbatim text content of each whitespace-sensitive element."""
    result = []

    def walk(element):
        if _localname(element.tag) in PREFORMATTED_TAGS:
            result.append((_localname(element.tag), "".join(element.itertext())))
            return
        for child in element:
            walk(child)

    walk(_parse(html))
    return result


def tag_skeleton(html):
    """Return the element tree as nested (tag, sorted-attrs) tuples, ignoring text."""

    def represent(element):
        attrs = tuple(sorted((_localname(k), v) for k, v in element.attrib.items()))
        return (_localname(element.tag), attrs, tuple(represent(c) for c in element))

    return represent(_parse(html))


def render_signature(html):
    """Return everything about `html` that a reader would perceive."""
    return (visible_text(html), preformatted_text(html), tag_skeleton(html))


def assert_prettify_invariant(html):
    """Assert that prettifying `html` preserves rendering and is idempotent.

    Raises AssertionError describing the first violation, so it works both inside
    unittest loops and as a hypothesis property.
    """
    pretty = prettify_html(html)
    before = render_signature(html)
    after = render_signature(pretty)
    if before != after:
        raise AssertionError(
            "pretty-printing changed the rendering\n"
            f"  input:  {html!r}\n"
            f"  pretty: {pretty!r}\n"
            f"  before: {before}\n"
            f"  after:  {after}"
        )
    again = prettify_html(pretty)
    if again != pretty:
        raise AssertionError(
            "pretty-printing is not idempotent\n"
            f"  input: {html!r}\n"
            f"  once:  {pretty!r}\n"
            f"  twice: {again!r}"
        )
