"""jinjabread's own HTML pretty-printer.

`prettify_html` re-serializes generated HTML with readable indentation, using a
custom lxml-based serializer that distinguishes inline, block, and preformatted
content. It is deliberately not an off-the-shelf tool: BeautifulSoup's
`prettify` reflows inline elements and breaks their rendering, and lxml's
`pretty_print`, `etree.indent`, and the `prettierfier` package inject
rendering-affecting whitespace or fail to normalize messy Jinja/Markdown input.

Three terms carry the whole design, and keeping them straight is the entire
correctness story:

Piece
    One item of inline content: a fragment of text, or a single inline element
    together with the text that trails it (its tail).

Inline run (also called an inline sequence)
    A maximal, contiguous group of pieces that render together on one line. A
    run is atomic. The serializer never breaks a line inside a run and never
    changes the whitespace between its pieces, because either edit changes what
    a browser shows: `one <em>two</em> three` must not become `one twothree`.
    This is where the "never change the rendering" guarantee lives.

Segment
    What an element's content splits into: either an inline run, laid out on one
    line, or a single block-level child, given its own line and serialized
    recursively. Block boundaries collapse whitespace, so segments (unlike the
    runs inside them) are free to reflow.
"""

import importlib
import re
import html
import lxml.html

# HTML phrasing (inline) elements. Their contents are never reflowed and the
# whitespace directly around them is significant, so we keep them, and any text
# adjacent to them, on a single line to avoid altering how they render.
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

# Elements whose content is whitespace-sensitive or raw (non-HTML) text. They
# are emitted verbatim, exactly as parsed, so their content is never collapsed,
# re-indented, or re-escaped.
OPAQUE_TAGS = frozenset({"pre", "textarea", "script", "style"})

# Block elements kept on a single line when their whole content is one inline
# run, e.g. `<li>One</li>`. Their leading and trailing whitespace is
# insignificant, so compacting them only tightens the output.
COMPACT_TAGS = frozenset(
    {"caption", "dd", "dt", "figcaption", "li", "option", "td", "th", "title"}
)

VOID_TAGS = lxml.html.defs.empty_tags
INDENT = "  "


def is_comment_or_pi(node):
    """Return whether `node` is a comment or processing instruction.

    lxml represents these with a callable `tag` instead of a string. They have
    no element children to lay out, so the serializer emits them verbatim.
    """
    return not (hasattr(node, "tag") and isinstance(node.tag, str))


def is_inlineable(node):
    """Return whether `node` can sit inside a single-line inline run.

    Text and comments always can. An element can only if it is a phrasing
    element whose descendants are themselves all inlineable, so nothing inside
    it forces a line break that would push it onto its own line.
    """
    if is_comment_or_pi(node):
        return True
    tag = node.tag.lower()
    if tag in OPAQUE_TAGS:
        return False
    if tag in VOID_TAGS:
        return tag in INLINE_TAGS
    if tag not in INLINE_TAGS:
        return False
    return all(is_inlineable(child) for child in node)


# Inside an attribute value, an ampersand needs escaping only when it could
# begin a character reference: when a letter, digit, or "#" follows it. Every
# other "&" is a literal, so a Tailwind class like `[&>p]:prose` is not mangled.
_REFERENCE_AMPERSAND = re.compile(r"&(?=[A-Za-z0-9#])")


def escape_attribute(value):
    """Escape a double-quoted attribute value minimally.

    Only the closing `"` and reference-starting ampersands would be misread; `<`,
    `>`, and single quotes are safe inside a double-quoted value. Text content is
    fully escaped elsewhere; attributes use this lighter touch so values like a
    Tailwind class `[&>p]:prose` are not mangled.
    """
    return _REFERENCE_AMPERSAND.sub("&amp;", value).replace('"', "&quot;")


def render_attributes(node):
    """Render an element's attributes in the author's original order.

    Values are escaped minimally (see `escape_attribute`), staying well-formed
    without over-escaping characters that browsers accept literally.
    """
    return "".join(
        f' {name}="{escape_attribute(value)}"' for name, value in node.attrib.items()
    )


def inline_pieces(node):
    """Return an element's content as an ordered list of inline pieces.

    Each piece is a ("text", str) fragment or a ("node", element) child, in
    document order, including the text that trails each child (its tail).
    """
    pieces = []
    if node.text:
        pieces.append(("text", node.text))
    for child in node:
        pieces.append(("node", child))
        if child.tail:
            pieces.append(("text", child.tail))
    return pieces


def render_inline_run(pieces):
    """Render a run of inline pieces onto a single line.

    A run collapses interior whitespace to single spaces and trims its outer
    edges, because the run sits between block-edge newlines. But it keeps every
    space between two pieces, so adjacent words and elements never merge. This
    is the atomic unit of the serializer: never insert a line break inside a run
    and never drop a space between its pieces, or the browser renders it
    differently.
    """
    parts = []
    pending_space = False
    for kind, value in pieces:
        if kind == "text":
            collapsed = re.sub(r"\s+", " ", value)
            stripped_text = collapsed.strip()
            if not stripped_text:
                pending_space = pending_space or bool(collapsed)
                continue
            if (pending_space or collapsed.startswith(" ")) and parts:
                parts.append(" ")
            parts.append(html.escape(stripped_text, quote=False))
            pending_space = collapsed.endswith(" ")
        else:
            if pending_space and parts:
                parts.append(" ")
            parts.append(render_inline_element(value))
            pending_space = False
    return "".join(parts)


def render_inline_element(node):
    """Render a single inline element and its content on one line."""
    if is_comment_or_pi(node):
        return lxml.html.tostring(node, with_tail=False).decode()
    tag = node.tag.lower()
    attributes = render_attributes(node)
    if tag in VOID_TAGS:
        return f"<{tag}{attributes}/>"
    return f"<{tag}{attributes}>{render_inline_run(inline_pieces(node))}</{tag}>"


def partition_into_segments(node):
    """Split an element's content into an ordered list of segments.

    Each segment is either an ("inline", run) pair, whose run is a maximal
    sequence of consecutive inline pieces to render on one line, or a ("block",
    child) pair for a child that gets its own line and is serialized
    recursively. Grouping the inline pieces into runs first is what preserves
    their whitespace; only the block boundaries between segments are free to
    reflow.
    """
    segments = []
    run = []

    def flush_run():
        if run:
            segments.append(("inline", run.copy()))
            run.clear()

    if node.text:
        run.append(("text", node.text))
    for child in node:
        if is_inlineable(child):
            run.append(("node", child))
        else:
            flush_run()
            segments.append(("block", child))
        if child.tail:
            run.append(("text", child.tail))
    flush_run()
    return segments


def render_node(node, depth):
    """Serialize a node and its subtree, indenting block structure at `depth`.

    Comments and preformatted/raw elements are emitted verbatim and void
    elements self-close. Every other element is split into segments (see
    `partition_into_segments`) and laid out either as a single inline run or as
    block children on their own indented lines.
    """
    if is_comment_or_pi(node):
        return lxml.html.tostring(node, with_tail=False).decode()
    tag = node.tag.lower()
    if tag in OPAQUE_TAGS:
        # Emit whitespace-sensitive and raw-text elements verbatim, as parsed.
        return lxml.html.tostring(node, with_tail=False).decode()

    attributes = render_attributes(node)
    if tag in VOID_TAGS:
        return f"<{tag}{attributes}/>"

    open_tag = f"<{tag}{attributes}>"
    close_tag = f"</{tag}>"
    is_inline = tag in INLINE_TAGS
    indent = depth * INDENT
    child_indent = (depth + 1) * INDENT

    segments = partition_into_segments(node)
    if not any(kind == "block" for kind, _ in segments):
        run = render_inline_run(segments[0][1]) if segments else ""
        if not run:
            return (
                open_tag + close_tag
                if is_inline
                else f"{open_tag}\n{indent}{close_tag}"
            )
        # Inline elements, and compact block elements (COMPACT_TAGS), stay on
        # one line when their whole content is a single inline run.
        if is_inline or tag in COMPACT_TAGS:
            return f"{open_tag}{run}{close_tag}"
        return f"{open_tag}\n{child_indent}{run}\n{indent}{close_tag}"

    parts = [open_tag]
    for kind, value in segments:
        if kind == "block":
            parts.append(f"\n{child_indent}{render_node(value, depth + 1)}")
        else:
            run = render_inline_run(value)
            if run:
                parts.append(f"\n{child_indent}{run}")
    parts.append(close_tag if is_inline else f"\n{indent}{close_tag}")
    return "".join(parts)


def prettify_html(text):
    """Pretty-print `text` without changing how it renders."""
    if not text:
        return ""

    root = lxml.html.fromstring(text)
    if root.tag == "html":
        # A full document, or a document-level fragment the parser promoted (for
        # example a lone <head> or <script>): emit it with a doctype, as lxml
        # resolved it. Output ends with a trailing newline, as text files should.
        return "<!DOCTYPE html>\n" + render_node(root, 0) + "\n"

    # A body-level fragment. lxml.html.fromstring wraps multiple roots or
    # leading text in a synthetic <div>/<span>; re-parse and render the
    # top-level pieces so that injected wrapper never reaches the output. A
    # single-rooted fragment renders identically either way.
    wrapper = lxml.html.fragment_fromstring(text, create_parent="div")
    rendered = []
    for kind, value in partition_into_segments(wrapper):
        if kind == "block":
            rendered.append(render_node(value, 0))
        else:
            run = render_inline_run(value)
            if run:
                rendered.append(run)
    return "\n".join(rendered) + "\n" if rendered else ""


def load_page_class(dot_path):
    parts = dot_path.rsplit(".", 2)
    if len(parts) != 2:
        raise TypeError("Invalid page type.")
    module = importlib.import_module(parts[0])
    return getattr(module, parts[1])


def find_index_file(path):
    for index_path in path.glob("index.*"):
        if not index_path.is_file():
            continue
        return index_path
    raise FileNotFoundError(
        f"Index file not found: {(path / 'index.*').relative_to(path).as_posix()}"
    )
