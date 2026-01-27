from dataclasses import dataclass
import importlib
import re
from lxml import html, etree
from html import escape

# INLINE_TAGS = {"a", "span", "strong", "em", "b", "i", "u", "small", "abbr"}
# VOID_TAGS = {"area","base","br","col","embed","hr","img","input","link","meta","source","track","wbr"}
# PRE_TAGS = {"pre", "code"}
# INDENT = "  "
INLINE_TAGS = html.defs.special_inline_tags
VOID_TAGS = html.defs.empty_tags
INDENT = "  "


@dataclass(kw_only=True)
class Context:
    action: str
    tag: str
    depth: int
    is_raw: bool
    is_void: bool
    is_inline: bool
    node: etree._Element

# Raw node.
# Opening tag.
# Text inside element.
# Children nodes.
# Closing tag.
# Trailing text.

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
    yield Context(action="open", tag=tag, depth=depth, is_raw=is_raw, is_void=is_void, is_inline=is_inline, node=node)
    
    # Text inside element.
    if not (is_void or is_raw) and node.text and node.text.strip():
        yield Context(action="text", tag=tag, depth=depth, is_raw=is_raw, is_void=is_void, is_inline=is_inline, node=node)
    
    # Children nodes.
    if not (is_void or is_raw):
        for child in node:
            yield from traverse(child, depth + 1)
    
    # Closing tag.
    if not (is_void or is_raw):
        yield Context(action="close", tag=tag, depth=depth, is_raw=is_raw, is_void=is_void, is_inline=is_inline, node=node)
    
    # Trailing text.
    if not is_raw and node.tail and node.tail.strip():
        yield Context(action="tail", tag=tag, depth=depth, is_raw=is_raw, is_void=is_void, is_inline=is_inline, node=node)


def serialize(root):
    if root.tag == "html":
        yield "<!DOCTYPE html>\n"
    
    prev_context = None
    for context in traverse(root):
        has_children = len(context.node) > 0
        padding = context.depth * INDENT
        
        match context.action:
            case "open":
                if context.depth > 0 and (not context.is_inline and not context.is_raw
                                          or not prev_context.is_inline and not prev_context.is_raw):
                    yield f"\n{padding}"
                if context.is_raw:
                    yield html.tostring(context.node).decode()
                else:
                    attrs = "".join(f' {key}="{escape(value, quote=True)}"' for key, value in sorted(context.node.attrib.items()))
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
                yield escape(text, quote=False)
            case "close":
                if not context.is_inline:
                    yield f"\n{padding}"
                yield f"</{context.tag}>"
            case "tail":
                tail = context.node.tail.strip()
                yield escape(tail, quote=False)
        
        prev_context = context


def prettify_html(text):
    if not text:
        return ""

    root = html.fromstring(text)
    return "".join(serialize(root))


def prettify_html2(text):
    if not text:
        return ""
    @dataclass
    class Frame:
        level: int
        tag: str
        is_inline: bool

    def serialize(node, parent_frame=None, prev_frame=None):
        tag = getattr(node, "tag", None)

        # Text node.
        if tag is None:
            if node.text and node.text.strip():
                yield escape(node.text, quote=False)
            return
        
        tag = tag.lower()
        is_inline = tag in INLINE_TAGS
        has_children = len(node) > 0
        
        if parent_frame is None:
            parent_is_inline = False
            level = 0
        else:
            parent_is_inline = parent_frame.is_inline
            level = parent_frame.level + 1


        attrs = "".join(f' {key}="{escape(value, quote=True)}"' for key, value in sorted(node.attrib.items()))
        padding = INDENT * level

        # Opening tag.
        # if level > 0 and (not parent_is_inline or parent_is_inline and not is_inline):
        if level > 0 and not is_inline:
            yield f"\n{padding}"
        yield f"<{tag}{attrs}>"
        # Text inside element.
        if node.text and node.text.strip():
            if not is_inline:
                yield f"\n{padding + INDENT}"
            # Collapse multiple whitespace into a single whitespace.
            text = re.sub(r"\s+", " ", node.text)
            # Strip leading whitespace.
            text = text.lstrip()
            # Strip trailing whitespace.
            if not has_children:
                text = text.rstrip()
            yield f"{text}"
        # elif not is_inline:
        #     yield f"\n{padding + INDENT}"
        # Children elements.
        prev_frame = None
        for child in node:
            prev_frame = yield from serialize(child, parent_frame=Frame(level=level, tag=tag, is_inline=is_inline), prev_frame=prev_frame)
        # Closing tag.
        if not is_inline:
            yield f"\n{padding}"
        yield f"</{tag}>"
        # Text after element.
        if node.tail and node.tail.strip():
            tail = node.tail.strip()
            yield f"{tail}"

        return Frame(
            level=level,
            tag=tag,
            is_inline=is_inline,
        )

    root = html.fromstring(text)
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
