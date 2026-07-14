"""jinjabread's own HTML pretty-printer.

`prettify_html` re-serializes generated HTML with readable indentation using a
custom lxml-based serializer that is inline/block/preformatted-aware. It is
deliberately NOT one of the off-the-shelf options: BeautifulSoup's `prettify`
reflows inline elements and breaks their rendering; lxml's `pretty_print` /
`etree.indent` and the `prettierfier` package inject rendering-affecting
whitespace or don't normalize messy Jinja/Markdown input.
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
# re-indented or re-escaped.
OPAQUE_TAGS = frozenset({"pre", "textarea", "script", "style"})

VOID_TAGS = lxml.html.defs.empty_tags
INDENT = "  "


def is_raw(node):
    # Comments and processing instructions have a callable tag, not a string.
    return not (hasattr(node, "tag") and isinstance(node.tag, str))


def is_inlineable(node):
    """Whether `node` can sit inside a single-line inline run.

    Text and comments always can. An element can only if it is a phrasing
    element whose descendants are themselves all inlineable, so nothing forces
    it onto its own line.
    """
    if is_raw(node):
        return True
    tag = node.tag.lower()
    if tag in OPAQUE_TAGS:
        return False
    if tag in VOID_TAGS:
        return tag in INLINE_TAGS
    if tag not in INLINE_TAGS:
        return False
    return all(is_inlineable(child) for child in node)


def render_attributes(node):
    # Preserve the author's attribute order.
    return "".join(
        f' {key}="{html.escape(value, quote=True)}"'
        for key, value in node.attrib.items()
    )


def inline_pieces(node):
    """Yield an element's content as an ordered list of inline pieces."""
    pieces = []
    if node.text:
        pieces.append(("text", node.text))
    for child in node:
        pieces.append(("node", child))
        if child.tail:
            pieces.append(("text", child.tail))
    return pieces


def render_inline_run(pieces):
    """Render inline pieces to a single line.

    Runs of whitespace collapse to one space and the run's outer edges are
    trimmed (it sits between block-edge newlines), but every space between two
    pieces is preserved, so adjacent words and elements never merge.
    """
    parts = []
    pending_space = False
    for kind, value in pieces:
        if kind == "text":
            collapsed = re.sub(r"\s+", " ", value)
            core = collapsed.strip()
            if not core:
                pending_space = pending_space or bool(collapsed)
                continue
            if (pending_space or collapsed.startswith(" ")) and parts:
                parts.append(" ")
            parts.append(html.escape(core, quote=False))
            pending_space = collapsed.endswith(" ")
        else:
            if pending_space and parts:
                parts.append(" ")
            parts.append(render_inline_element(value))
            pending_space = False
    return "".join(parts)


def render_inline_element(node):
    if is_raw(node):
        return lxml.html.tostring(node, with_tail=False).decode()
    tag = node.tag.lower()
    attributes = render_attributes(node)
    if tag in VOID_TAGS:
        return f"<{tag}{attributes}/>"
    return f"<{tag}{attributes}>{render_inline_run(inline_pieces(node))}</{tag}>"


def partition(node):
    """Split an element's content into inline runs and block-level children.

    Consecutive inline pieces (text, comments, inline elements) group into one
    run; every non-inlineable child becomes its own block segment.
    """
    segments = []
    run = []

    def flush():
        if run:
            segments.append(("inline", run.copy()))
            run.clear()

    if node.text:
        run.append(("text", node.text))
    for child in node:
        if is_inlineable(child):
            run.append(("node", child))
        else:
            flush()
            segments.append(("block", child))
        if child.tail:
            run.append(("text", child.tail))
    flush()
    return segments


def render(node, depth):
    """Serialize a node's subtree, indenting block structure at `depth`."""
    if is_raw(node):
        return lxml.html.tostring(node, with_tail=False).decode()
    tag = node.tag.lower()
    if tag in OPAQUE_TAGS:
        # Emit whitespace-sensitive elements verbatim, exactly as parsed.
        return lxml.html.tostring(node, with_tail=False).decode()

    attributes = render_attributes(node)
    if tag in VOID_TAGS:
        return f"<{tag}{attributes}/>"

    open_tag = f"<{tag}{attributes}>"
    close_tag = f"</{tag}>"
    inline = tag in INLINE_TAGS
    indent = depth * INDENT
    child_indent = (depth + 1) * INDENT

    segments = partition(node)
    if not any(kind == "block" for kind, _ in segments):
        run = render_inline_run(segments[0][1]) if segments else ""
        if not run:
            return (
                open_tag + close_tag if inline else f"{open_tag}\n{indent}{close_tag}"
            )
        if inline:
            return f"{open_tag}{run}{close_tag}"
        return f"{open_tag}\n{child_indent}{run}\n{indent}{close_tag}"

    parts = [open_tag]
    for kind, value in segments:
        if kind == "block":
            parts.append(f"\n{child_indent}{render(value, depth + 1)}")
        else:
            run = render_inline_run(value)
            if run:
                parts.append(f"\n{child_indent}{run}")
    parts.append(close_tag if inline else f"\n{indent}{close_tag}")
    return "".join(parts)


def prettify_html(text):
    if not text:
        return ""

    root = lxml.html.fromstring(text)
    doctype = "<!DOCTYPE html>\n" if root.tag == "html" else ""
    return doctype + render(root, 0)


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
