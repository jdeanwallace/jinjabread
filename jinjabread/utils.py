import importlib
import re
import html
import dataclasses
import lxml.etree
import lxml.html

INLINE_TAGS = lxml.html.defs.special_inline_tags
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

    # Opening tag.
    yield Context(
        action="open",
        tag=tag,
        depth=depth,
        is_raw=is_raw,
        is_void=is_void,
        is_inline=is_inline,
        node=node,
    )

    # Text inside element.
    if not (is_void or is_raw) and node.text and node.text.strip():
        yield Context(
            action="text",
            tag=tag,
            depth=depth,
            is_raw=is_raw,
            is_void=is_void,
            is_inline=is_inline,
            node=node,
        )

    # Children nodes.
    if not (is_void or is_raw):
        for child in node:
            yield from traverse(child, depth + 1)

    # Closing tag.
    if not (is_void or is_raw):
        yield Context(
            action="close",
            tag=tag,
            depth=depth,
            is_raw=is_raw,
            is_void=is_void,
            is_inline=is_inline,
            node=node,
        )

    # Trailing text.
    if not is_raw and node.tail and node.tail.strip():
        yield Context(
            action="tail",
            tag=tag,
            depth=depth,
            is_raw=is_raw,
            is_void=is_void,
            is_inline=is_inline,
            node=node,
        )


def serialize(root):
    if root.tag == "html":
        yield "<!DOCTYPE html>\n"

    prev_context = None
    for context in traverse(root):
        has_children = len(context.node) > 0
        padding = context.depth * INDENT

        match context.action:
            case "open":
                if context.depth > 0 and (
                    not context.is_inline
                    and not context.is_raw
                    or not prev_context.is_inline
                    and not prev_context.is_raw
                ):
                    yield f"\n{padding}"
                if context.is_raw:
                    yield lxml.html.tostring(context.node).decode()
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
                if not context.is_inline:
                    yield f"\n{padding + INDENT}"
                # Collapse multiple whitespaces into a single whitespace.
                text = re.sub(r"\s+", " ", context.node.text)
                # Strip leading whitespace.
                text = text.lstrip()
                # Strip trailing whitespace.
                if not has_children:
                    text = text.rstrip()
                yield html.escape(text, quote=False)
            case "close":
                if not context.is_inline:
                    yield f"\n{padding}"
                yield f"</{context.tag}>"
            case "tail":
                tail = context.node.tail.strip()
                yield html.escape(tail, quote=False)

        prev_context = context


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
