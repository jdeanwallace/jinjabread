import importlib
import re
import html
import dataclasses
import lxml.etree
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


@dataclasses.dataclass(kw_only=True, frozen=True)
class Context:
    action: str
    tag: str
    depth: int
    is_raw: bool
    is_void: bool
    is_inline: bool
    is_opaque: bool
    node: lxml.etree._Element


def traverse(node, depth=0):
    """Iterate through the HTML DOM.

    1. Opening tag.
    2. Text inside element.
    3. Children nodes.
    4. Closing tag.
    5. Trailing text.
    """
    is_raw = not (hasattr(node, "tag") and isinstance(node.tag, str))
    tag = "" if is_raw else node.tag.lower()
    is_void = tag in VOID_TAGS
    is_inline = tag in INLINE_TAGS
    is_opaque = tag in OPAQUE_TAGS

    def context(action):
        return Context(
            action=action,
            tag=tag,
            depth=depth,
            is_raw=is_raw,
            is_void=is_void,
            is_inline=is_inline,
            is_opaque=is_opaque,
            node=node,
        )

    # Opening tag. Void, raw and opaque nodes are leaves: their inner content is
    # either absent or emitted verbatim with the opening tag.
    yield context("open")
    is_leaf = is_void or is_raw or is_opaque

    # Text inside element.
    if not is_leaf and node.text:
        yield context("text")

    # Children nodes.
    if not is_leaf:
        for child in node:
            yield from traverse(child, depth + 1)

    # Closing tag.
    if not is_leaf:
        yield context("close")

    # Trailing text.
    if node.tail:
        yield context("tail")


def leads_with_newline(context, prev_context):
    """Whether emitting `context` starts on a fresh, indented line."""
    if context is None:
        return True
    match context.action:
        case "open":
            return context.depth > 0 and (
                not context.is_inline
                and not context.is_raw
                or prev_context is not None
                and not prev_context.is_inline
                and not prev_context.is_raw
            )
        case "text" | "close":
            return not context.is_inline
        case _:  # tail
            return False


def collapse_whitespace(text, *, keep_leading, keep_trailing):
    """Collapse whitespace runs, keeping boundary spaces only where significant.

    A boundary space is dropped at block edges (where a newline is inserted
    instead) and kept next to inline content, so words never run together.
    """
    text = re.sub(r"\s+", " ", text)
    has_leading = text.startswith(" ")
    has_trailing = text.endswith(" ")
    core = text.strip()
    if not core:
        keep = (has_leading and keep_leading) or (has_trailing and keep_trailing)
        return " " if keep else ""
    if has_leading and keep_leading:
        core = " " + core
    if has_trailing and keep_trailing:
        core = core + " "
    return core


def serialize(root):
    if root.tag == "html":
        yield "<!DOCTYPE html>\n"

    contexts = list(traverse(root))
    for index, context in enumerate(contexts):
        prev_context = contexts[index - 1] if index > 0 else None
        next_context = contexts[index + 1] if index + 1 < len(contexts) else None
        padding = context.depth * INDENT

        match context.action:
            case "open":
                if leads_with_newline(context, prev_context):
                    yield f"\n{padding}"
                if context.is_raw:
                    yield lxml.html.tostring(context.node, with_tail=False).decode()
                elif context.is_opaque:
                    # Emit the whole subtree verbatim to preserve its whitespace.
                    yield lxml.html.tostring(context.node, with_tail=False).decode()
                else:
                    attrs = "".join(
                        f' {key}="{html.escape(value, quote=True)}"'
                        for key, value in sorted(context.node.attrib.items())
                    )
                    yield f"<{context.tag}{attrs}"
                    if context.is_void:
                        yield "/"
                    yield ">"
            case "text":
                text = collapse_whitespace(
                    context.node.text,
                    keep_leading=context.is_inline,
                    keep_trailing=not leads_with_newline(next_context, context),
                )
                if text:
                    if not context.is_inline:
                        yield f"\n{padding + INDENT}"
                    yield html.escape(text, quote=False)
            case "close":
                if not context.is_inline:
                    yield f"\n{padding}"
                yield f"</{context.tag}>"
            case "tail":
                tail = collapse_whitespace(
                    context.node.tail,
                    keep_leading=context.is_inline,
                    keep_trailing=not leads_with_newline(next_context, context),
                )
                if tail:
                    yield html.escape(tail, quote=False)


def prettify_html(text):
    if not text:
        return ""

    root = lxml.html.fromstring(text)
    return "".join(serialize(root))


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
