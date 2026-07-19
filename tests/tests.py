import os
import shutil
import unittest
import tempfile
from pathlib import Path
from werkzeug.test import Client

import jinjabread


class TestHtmlMixin:

    def assertHtmlEqual(self, first, second):
        self.maxDiff = None
        return self.assertEqual(
            jinjabread.prettify_html(first), jinjabread.prettify_html(second)
        )


class TestTempWorkingDirMixin:

    def setUp(self):
        super().setUp()
        self.working_dir = Path(tempfile.mkdtemp())
        os.chdir(self.working_dir)
        self.addCleanup(shutil.rmtree, self.working_dir)


class UtilTest(TestTempWorkingDirMixin, unittest.TestCase):
    def test_find_index_file_with_empty_directory(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            jinjabread.find_index_file(self.working_dir)
        self.assertEqual("Index file not found: index.*", str(ctx.exception))

    def test_find_index_file_with_missing_index_file(self):
        (self.working_dir / "post1.html").touch()
        (self.working_dir / "post2.html").touch()

        with self.assertRaises(FileNotFoundError) as ctx:
            jinjabread.find_index_file(self.working_dir)
        self.assertEqual("Index file not found: index.*", str(ctx.exception))

    def test_find_index_file(self):
        (self.working_dir / "index.html").touch()

        self.assertEqual(
            self.working_dir / "index.html",
            jinjabread.find_index_file(self.working_dir),
        )

    def test_find_index_file_with_other_files(self):
        (self.working_dir / "index.html").touch()
        (self.working_dir / "post1.html").touch()
        (self.working_dir / "post2.html").touch()

        self.assertEqual(
            self.working_dir / "index.html",
            jinjabread.find_index_file(self.working_dir),
        )

    def test_find_index_file_with_any_suffix(self):
        (self.working_dir / "index.md").touch()
        (self.working_dir / "post1.html").touch()
        (self.working_dir / "post2.html").touch()

        self.assertEqual(
            self.working_dir / "index.md",
            jinjabread.find_index_file(self.working_dir),
        )

    def test_prettify_html_inline_tag(self):
        text = """<span>Hello</span>"""
        self.assertEqual(
            """
<span>Hello</span>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_tag_tail(self):
        text = """
        <div><span>Hello</span>.</div>
        """
        self.assertEqual(
            """
<div>
  <span>Hello</span>.
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_nested_inline_tag(self):
        text = """<span><span>Hello, World!</span></span>"""
        self.assertEqual(
            """
<span><span>Hello, World!</span></span>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_nested_inline_tags(self):
        text = """<span><span>Hello, World!</span><span>Hello, Earth!</span></span>"""
        self.assertEqual(
            """
<span><span>Hello, World!</span><span>Hello, Earth!</span></span>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_block_tag(self):
        text = """
        <p>Hello, World!</p>
        """
        self.assertEqual(
            """
<p>
  Hello, World!
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_block_tag_tail(self):
        text = """<div><div>Hello, World</div>!</div>"""
        self.assertEqual(
            """
<div>
  <div>
    Hello, World
  </div>
  !
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_nested_block_tag(self):
        text = """<div><p>Hello, World!</p><p>Hello, Earth!</p></div>"""
        self.assertEqual(
            """
<div>
  <p>
    Hello, World!
  </p>
  <p>
    Hello, Earth!
  </p>
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_multiple_root_block_tags(self):
        text = """<p>Hello, World!</p><p>Hello, Earth!</p>"""
        self.assertEqual(
            """
<p>
  Hello, World!
</p>
<p>
  Hello, Earth!
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_root_text_and_inline(self):
        text = """Hello, <b>World</b>!"""
        self.assertEqual(
            """Hello, <b>World</b>!""",
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_bare_text(self):
        text = """Just text."""
        self.assertEqual("""Just text.""", jinjabread.prettify_html(text))

    def test_prettify_html_inline_tag_wraps_block_tag(self):
        text = """<a href="#home"><div>Hello, World!</div></a>"""
        self.assertEqual(
            """
<a href="#home">
  <div>
    Hello, World!
  </div></a>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_tag_wraps_block_tags(self):
        text = (
            """<a href="#home"><div>Hello, World!</div><div>Hello, Earth!</div></a>"""
        )
        self.assertEqual(
            """
<a href="#home">
  <div>
    Hello, World!
  </div>
  <div>
    Hello, Earth!
  </div></a>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_tag_wraps_mixed_tags(self):
        text = """<a href="#home"><div>Hello, World!</div><span>Hello, Mars!</span><div>Hello, Earth!</div></a>"""
        self.assertEqual(
            """
<a href="#home">
  <div>
    Hello, World!
  </div>
  <span>Hello, Mars!</span>
  <div>
    Hello, Earth!
  </div></a>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_tag_wraps_raw_node(self):
        text = """<span><!-- Hello, World! --></span>"""
        self.assertEqual(
            """
<span><!-- Hello, World! --></span>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_tag_wraps_raw_nodes(self):
        text = """<span><!-- Hello, World! --><!-- Hello, Earth! --></span>"""
        self.assertEqual(
            """
<span><!-- Hello, World! --><!-- Hello, Earth! --></span>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_block_tag_wraps_inline_tag(self):
        text = """<div><span>Hello, World!</span></div>"""
        self.assertEqual(
            """
<div>
  <span>Hello, World!</span>
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_block_tag_wraps_inline_tags(self):
        text = """<div><span>Hello,</span><span>World!</span></div>"""
        self.assertEqual(
            """
<div>
  <span>Hello,</span><span>World!</span>
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_void_tag(self):
        text = """<hr/>"""
        self.assertEqual(
            """
<hr/>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_block_tag_wraps_raw_node(self):
        text = """<div><!-- Hello, World! --></div>"""
        self.assertEqual(
            """
<div>
  <!-- Hello, World! -->
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_block_tag_wraps_raw_nodes(self):
        text = """<div><!-- Hello, World! --><!-- Hello, Earth! --></div>"""
        self.assertEqual(
            """
<div>
  <!-- Hello, World! --><!-- Hello, Earth! -->
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html5(self):
        text = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document</title>
</head>
<body>
  
</body>
</html>
"""
        self.assertEqual(
            """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Document</title>
  </head>
  <body>
  </body>
</html>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_link_mid_sentence(self):
        text = '<p>So as a form of <a href="/x">nesting</a>, we built our own.</p>'
        self.assertEqual(
            """
<p>
  So as a form of <a href="/x">nesting</a>, we built our own.
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_em_mid_sentence(self):
        text = "<p>This is my <em>emphasised</em> point.</p>"
        self.assertEqual(
            """
<p>
  This is my <em>emphasised</em> point.
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_strong_mid_sentence(self):
        text = "<p>The <strong>end</strong>.</p>"
        self.assertEqual(
            """
<p>
  The <strong>end</strong>.
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_code_mid_sentence(self):
        text = "<p>Install with <code>pip install jinjabread</code> today.</p>"
        self.assertEqual(
            """
<p>
  Install with <code>pip install jinjabread</code> today.
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_no_space_before_punctuation(self):
        text = '<p>Click <a href="/x">here</a>.</p>'
        self.assertEqual(
            """
<p>
  Click <a href="/x">here</a>.
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_at_block_start(self):
        text = '<p><a href="/x">Home</a> is where it starts.</p>'
        self.assertEqual(
            """
<p>
  <a href="/x">Home</a> is where it starts.
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_at_block_end(self):
        text = '<p>It ends at <a href="/x">home</a></p>'
        self.assertEqual(
            """
<p>
  It ends at <a href="/x">home</a>
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_adjacent_inline_with_space(self):
        text = "<p><em>a</em> <strong>b</strong></p>"
        self.assertEqual(
            """
<p>
  <em>a</em> <strong>b</strong>
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_nested_inline_preserves_spaces(self):
        text = '<p>See <a href="/x">the <em>full</em> guide</a> now.</p>'
        self.assertEqual(
            """
<p>
  See <a href="/x">the <em>full</em> guide</a> now.
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_inline_words_keep_spaces(self):
        text = "<p>one <em>two</em> three <strong>four</strong> five</p>"
        self.assertEqual(
            """
<p>
  one <em>two</em> three <strong>four</strong> five
</p>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_nested_block_lists(self):
        text = "<div><ul><li>One</li><li>Two</li></ul></div>"
        self.assertEqual(
            """
<div>
  <ul>
    <li>One</li>
    <li>Two</li>
  </ul>
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_compact_elements(self):
        text = "<table><tr><td>Cell one</td><td>Cell <a href='/x'>two</a></td></tr></table>"
        self.assertEqual(
            """
<table>
  <tr>
    <td>Cell one</td>
    <td>Cell <a href="/x">two</a></td>
  </tr>
</table>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_compact_element_with_block_child_stays_expanded(self):
        text = "<li><p>Paragraph</p></li>"
        self.assertEqual(
            """
<li>
  <p>
    Paragraph
  </p>
</li>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_pre_preserved_byte_for_byte(self):
        text = "<pre>def f():\n    return 1\n\n\n    # three blank lines above\n</pre>"
        self.assertEqual(text, jinjabread.prettify_html(text))

    def test_prettify_html_pre_code_preserved_byte_for_byte(self):
        text = "<pre><code>a = 1\n  b = 2\n\nc = 3</code></pre>"
        self.assertEqual(text, jinjabread.prettify_html(text))

    def test_prettify_html_textarea_preserved_byte_for_byte(self):
        text = "<textarea>  keep    these\n  spaces\n</textarea>"
        self.assertEqual(text, jinjabread.prettify_html(text))

    def test_prettify_html_script_content_not_escaped(self):
        text = "<div><script>if (a < b && c > d) { run(); }</script></div>"
        self.assertEqual(
            """
<div>
  <script>if (a < b && c > d) { run(); }</script>
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_comment_tail_collapsed(self):
        text = "<div><!-- note -->after   the    comment</div>"
        self.assertEqual(
            """
<div>
  <!-- note -->after the comment
</div>
""".strip(),
            jinjabread.prettify_html(text),
        )

    def test_prettify_html_is_idempotent(self):
        for text in [
            '<p>So as a form of <a href="/x">nesting</a>, we built our own.</p>',
            "<pre>def f():\n    return 1\n</pre>",
            "<div><script>if (a < b) { run(); }</script></div>",
            "<p>one <em>two</em> three <strong>four</strong> five</p>",
            "<div><ul><li>One</li><li>Two</li></ul></div>",
            "<div><!-- note -->after the comment</div>",
            "<html><head><title>T</title></head><body><p>Hi <a href='/x'>x</a>!</p></body></html>",
        ]:
            with self.subTest(text=text):
                once = jinjabread.prettify_html(text)
                self.assertEqual(once, jinjabread.prettify_html(once))


class ConfigTest(TestTempWorkingDirMixin, unittest.TestCase):

    def test_defaults(self):
        config = jinjabread.Config.load()

        self.assertTrue(self.working_dir.name, config.project_dir.name)
        self.assertEqual("content", config.content_dir.name)
        self.assertEqual("layouts", config.layouts_dir.name)
        self.assertEqual("static", config.static_dir.name)
        self.assertEqual("public", config.output_dir.name)
        self.assertDictEqual({}, config.context)
        self.assertTrue(config.prettify_html)
        self.assertListEqual(
            [jinjabread.PageFactory, jinjabread.PageFactory],
            [type(x) for x in config.page_factories],
        )
        self.assertListEqual(
            [jinjabread.MarkdownPage, jinjabread.Page],
            [x.page_class for x in config.page_factories],
        )

    def test_with_custom_project_directory(self):
        config = jinjabread.Config.load(project_dir="mysite")

        self.assertTrue("mysite", config.project_dir.name)

    def test_config_with_missing_config_file(self):
        with self.assertRaises(FileNotFoundError):
            jinjabread.Config.load(config_file="missing.toml")

    def test_with_custom_config_file(self):
        with (self.working_dir / "custom.toml").open("w") as file:
            file.write(
                """
                output_dir = "dist"

                [context]
                  foo = "bar"
                """
            )

        config = jinjabread.Config.load(config_file="custom.toml")

        self.assertEqual("dist", config.output_dir.name)
        self.assertDictEqual({"foo": "bar"}, config.context)

    def test_ignore_unexpected_config(self):
        with (self.working_dir / "custom.toml").open("w") as file:
            file.write(
                """
                foo = "bar"

                [custom]
                  foo = "bar"
                """
            )

        jinjabread.Config.load(config_file="custom.toml")


class BuildSiteTest(TestTempWorkingDirMixin, TestHtmlMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.test_data_dir = Path(__file__).parent / "test_data"

    def test_html_content(self):
        content_path = self.working_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                <h1>Hello, World{# This is a comment #}</h1>
                """
            )

        jinjabread.build()

        self.assertHtmlEqual(
            """
            <h1>Hello, World</h1>
            """,
            Path("public/home.html").read_text(),
        )

    def test_html_content_inline_anchor_intact(self):
        content_path = self.working_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                <p>Hello, here's a <a href="#home">link</a>.</p>
                """
            )

        jinjabread.build()

        self.assertEqual(
            """
<p>
  Hello, here's a <a href="#home">link</a>.
</p>
""".strip(),
            Path("public/home.html").read_text(),
        )

    def test_html_content_extends_layout(self):
        content_path = self.working_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                {% extends 'markdown.html' %}
                {% block body %}
                <p>Blah blah blah</p>
                {% endblock body %}
                """
            )
        layout_path = self.working_dir / "layouts" / "markdown.html"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        with layout_path.open("w") as file:
            file.write(
                """
                <h1>Hello, World</h1>
                {% block body %}
                {% endblock body %}
                """
            )

        jinjabread.build()

        self.assertHtmlEqual(
            """
            <h1>Hello, World</h1>
            <p>Blah blah blah</p>
            """,
            Path("public/home.html").read_text(),
        )

    def test_html_content_includes_layout(self):
        content_path = self.working_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                <h1>Hello, World</h1>
                {% include 'message.txt' %}
                """
            )
        layout_path = self.working_dir / "layouts" / "message.txt"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        with layout_path.open("w") as file:
            file.write(
                """
                <p>Blah blah blah</p>
                """
            )

        jinjabread.build()

        self.assertHtmlEqual(
            """
            <h1>Hello, World</h1>
            <p>Blah blah blah</p>
            """,
            Path("public/home.html").read_text(),
        )
        self.assertFalse(Path("public/message.txt").exists())

    def test_html_content_includes_content(self):
        content_path = self.working_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                <h1>Hello, World</h1>
                {% include 'message.txt' %}
                """
            )
        content_path2 = self.working_dir / "content" / "message.txt"
        content_path2.parent.mkdir(parents=True, exist_ok=True)
        with content_path2.open("w") as file:
            file.write(
                """
                <p>Blah blah blah</p>
                """
            )

        jinjabread.build()

        self.assertHtmlEqual(
            """
            <h1>Hello, World</h1>
            <p>Blah blah blah</p>
            """,
            Path("public/home.html").read_text(),
        )
        self.assertTrue(Path("public/message.txt").exists())

    def test_text_content(self):
        content_path = self.working_dir / "content" / "home.txt"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("""Hello, World{# This is a comment #}""")

        jinjabread.build()

        self.assertEqual("""Hello, World""", Path("public/home.txt").read_text())

    def test_markdown_content(self):
        shutil.copytree(
            self.test_data_dir / "test_markdown_content",
            self.working_dir,
            dirs_exist_ok=True,
        )

        jinjabread.build()

        self.assertHtmlEqual(
            """
            <header>This is a header.</header>
            <main>
                <h1>My blog post</h1>
                <p>This is my story.</p>
                <p>The <strong>end</strong>.</p>
                <p>Written by John.</p>
            </main>
            <footer>This is a footer.</footer>
            """,
            Path("public/post.html").read_text(),
        )

    def test_directory_index_html_content(self):
        content_path = self.working_dir / "content" / "posts" / "index.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                <h1>Look on my Works, ye Mighty, and despair!</h1>
                {% for page in pages|sort(attribute="url_path") %}
                <p>{{ page.url_path }}</p>
                {% endfor %}
                """
            )
        content_path = self.working_dir / "content" / "posts" / "post1.html"
        with content_path.open("w") as file:
            file.write(
                """
                <p>I am post 1.</p>
                """
            )
        content_path = self.working_dir / "content" / "posts" / "post2.html"
        with content_path.open("w") as file:
            file.write(
                """
                <p>I am post 2.</p>
                """
            )
        content_path = self.working_dir / "content" / "posts" / "post3.html"
        with content_path.open("w") as file:
            file.write(
                """
                <p>I am post 3.</p>
                """
            )

        jinjabread.build()

        self.assertHtmlEqual(
            """
            <h1>Look on my Works, ye Mighty, and despair!</h1>
            <p>/posts/post1</p>
            <p>/posts/post2</p>
            <p>/posts/post3</p>
            """,
            Path("public/posts/index.html").read_text(),
        )

    def test_directory_index_markdown_content(self):
        shutil.copytree(
            self.test_data_dir / "test_directory_index_markdown_content",
            self.working_dir,
            dirs_exist_ok=True,
        )

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)
        site.generate()

        self.assertHtmlEqual(
            """
            <header>This is a header.</header>
            <main>
                <h1>Look on my Works, ye Mighty, and despair!</h1>
                <h2>Post 1</h2>
                <p>I am post 1.</p>
                <hr/>
                <h2>Post 2</h2>
                <p>I am post 2.</p>
                <hr/>
                <h2>Post 3</h2>
                <p>I am post 3.</p>
                <hr/>
            </main>
            <footer>This is a footer.</footer>
            """,
            Path("public/index.html").read_text(),
        )

    def test_directory_index_markdown_content_with_directory_siblings(self):
        shutil.copytree(
            self.test_data_dir
            / "test_directory_index_markdown_content_with_directory_siblings",
            self.working_dir,
            dirs_exist_ok=True,
        )

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)
        site.generate()

        self.assertHtmlEqual(
            """
            <header>This is a header.</header>
            <main>
                <h1>Look on my Works, ye Mighty, and despair!</h1>
                <h2>Post 1</h2>
                <p>I am post 1.</p>
                <p>Read more <a href="/post1/">here</a>.</p>
                <hr/>
                <h2>Post 2</h2>
                <p>I am post 2.</p>
                <p>Read more <a href="/post2/">here</a>.</p>
                <hr/>
                <h2>Post 3</h2>
                <p>I am post 3.</p>
                <p>Read more <a href="/post3/">here</a>.</p>
                <hr/>
            </main>
            <footer>This is a footer.</footer>
            """,
            Path("public/index.html").read_text(),
        )

    def test_markdown_content_with_custom_glob_pattern(self):
        shutil.copytree(
            self.test_data_dir / "test_markdown_content_with_custom_glob_pattern",
            self.working_dir,
            dirs_exist_ok=True,
        )

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)
        site.generate()

        self.assertHtmlEqual(
            """
            <header>This is a header.</header>
            <main>
                <h1>Post: My blog post</h1>
                <p>This is my story.</p>
                <p>The <strong>end</strong>.</p>
                <p>Written by John.</p>
            </main>
            <footer>This is a footer.</footer>
            """,
            Path("public/post1.html").read_text(),
        )
        self.assertHtmlEqual(
            """
            <header>This is a header.</header>
            <main>
                <h1>Article: My article</h1>
                <p>This is my article.</p>
                <p>The <strong>end</strong>.</p>
                <p>Written by Jimmy.</p>
            </main>
            <footer>This is a footer.</footer>
            """,
            Path("public/article1.html").read_text(),
        )

    def test_copy_static_content(self):
        content_path = self.working_dir / "content" / "dummy.jpg"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.touch()

        jinjabread.build()

        self.assertTrue(Path("public/dummy.jpg").exists())

    def test_copy_static_directory(self):
        static_path = self.working_dir / "static" / "dummy.jpg"
        static_path.parent.mkdir(parents=True, exist_ok=True)
        static_path.touch()

        jinjabread.build()

        self.assertTrue(Path("public/static/dummy.jpg").exists())

    def test_ignore_hidden_file(self):
        content_path = self.working_dir / "content" / ".hidden-file"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("Hello, World!")

        jinjabread.build()

        self.assertFalse(Path("public/.hidden-file").exists())

    def test_ignore_hidden_directory(self):
        content_path = (
            self.working_dir / "content" / ".hidden-directory" / "message.txt"
        )
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("Hello, World!")

        jinjabread.build()

        self.assertFalse(Path("public/.hidden-directory/message.txt").exists())

    def test_context_variable_precedence(self):
        with (self.working_dir / "jinjabread.toml").open("w") as file:
            file.write(
                """
                [context]
                  fee = "fie"
                  foe = "fum"

                [[pages]]
                  type = "jinjabread.Page"
                  glob_pattern = "**/*.txt"

                  [pages.context]
                    foe = "foo"

                [[pages]]
                  type = "jinjabread.Page"
                  glob_pattern = "**/*.csv"

                  [pages.context]
                    foe = "bar"
                
                [[pages]]
                  type = "jinjabread.Page"
                  glob_pattern = "**/*.html"
                """
            )

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        txt_page = site.match_page(Path("content/test.txt"))
        self.assertDictEqual(
            {
                "file_path": "test.txt",
                "url_path": "/test",
                "fee": "fie",
                "foe": "foo",
            },
            txt_page.get_context(),
        )

        csv_page = site.match_page(Path("content/test.csv"))
        self.assertDictEqual(
            {
                "file_path": "test.csv",
                "url_path": "/test",
                "fee": "fie",
                "foe": "bar",
            },
            csv_page.get_context(),
        )

        html_page = site.match_page(Path("content/test.html"))
        self.assertDictEqual(
            {
                "file_path": "test.html",
                "url_path": "/test",
                "fee": "fie",
                "foe": "fum",
            },
            html_page.get_context(),
        )

    def test_context_variables_on_root_index_page(self):
        content_path = self.working_dir / "content" / "index.html"
        content_path.parent.mkdir(parents=True)
        content_path.touch()

        content_path = self.working_dir / "content" / "about.html"
        content_path.touch()

        # Hidden files should be ignored.
        content_path = self.working_dir / "content" / ".hidden-file"
        content_path.touch()

        # Hidden directories and their contents should be ignored.
        content_path = (
            self.working_dir / "content" / ".hidden-directory" / "message.txt"
        )
        content_path.parent.mkdir(parents=True)
        content_path.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        content_page = site.match_page(Path("content/index.html"))
        self.assertDictEqual(
            {
                "file_path": "index.html",
                "url_path": "/",
                "pages": [
                    {"file_path": "about.html", "url_path": "/about"},
                ],
            },
            content_page.get_context(),
        )

    def test_context_variables_on_dir_index_page(self):
        content_path = self.working_dir / "content" / "posts" / "index.html"
        content_path.parent.mkdir(parents=True)
        content_path.touch()

        content_path = self.working_dir / "content" / "posts" / "post1.html"
        content_path.touch()

        # Hidden files should be ignored.
        content_path = self.working_dir / "content" / "posts" / ".hidden-file"
        content_path.touch()

        # Hidden directories and their contents should be ignored.
        content_path = (
            self.working_dir / "content" / "posts" / ".hidden-directory" / "message.txt"
        )
        content_path.parent.mkdir(parents=True)
        content_path.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        content_page = site.match_page(Path("content/posts/index.html"))
        self.assertDictEqual(
            {
                "file_path": "posts/index.html",
                "url_path": "/posts/",
                "pages": [
                    {"file_path": "posts/post1.html", "url_path": "/posts/post1"},
                ],
            },
            content_page.get_context(),
        )

    def test_context_variables_on_root_page(self):
        content_path = self.working_dir / "content" / "about.html"
        content_path.parent.mkdir(parents=True)
        content_path.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        content_page = site.match_page(Path("content/about.html"))
        self.assertDictEqual(
            {
                "file_path": "about.html",
                "url_path": "/about",
            },
            content_page.get_context(),
        )

    def test_context_variables_on_dir_page(self):
        content_path = self.working_dir / "content" / "posts" / "post1.html"
        content_path.parent.mkdir(parents=True)
        content_path.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        content_page = site.match_page(Path("content/posts/post1.html"))
        self.assertDictEqual(
            {
                "file_path": "posts/post1.html",
                "url_path": "/posts/post1",
            },
            content_page.get_context(),
        )


class NewSiteTest(TestTempWorkingDirMixin, unittest.TestCase):

    def test_defaults(self):
        jinjabread.new()

        self.assertTrue(Path("jinjabread.toml").exists())
        self.assertTrue(Path("content").exists())
        self.assertTrue(Path("layouts").exists())

    def test_with_custom_project_directory(self):
        jinjabread.new(project_dir="mysite")

        self.assertTrue(Path("mysite").exists())
        self.assertTrue(Path("mysite/jinjabread.toml").exists())
        self.assertTrue(Path("mysite/content").exists())
        self.assertTrue(Path("mysite/layouts").exists())


class ServeSiteTest(TestTempWorkingDirMixin, TestHtmlMixin, unittest.TestCase):

    def test_response(self):
        index_file = self.working_dir / "content" / "index.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)
        site.generate()

        client = Client(jinjabread.App(config))
        response = client.get("/")

        self.assertEqual(200, response.status_code)
        self.assertDictEqual(
            {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": "0",
            },
            dict(response.headers),
        )
        self.assertHtmlEqual("", response.get_data(as_text=True))

    def test_redirect_root_index_path(self):
        index_file = self.working_dir / "content" / "index.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)
        site.generate()

        client = Client(jinjabread.App(config))
        response = client.get("/index.html")

        self.assertEqual(302, response.status_code)
        self.assertEqual("/", response.headers.get("Location"))

    def test_redirect_dir_index_path(self):
        index_file = self.working_dir / "content" / "posts" / "index.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)
        site.generate()

        client = Client(jinjabread.App(config))
        response = client.get("/posts/index.html")

        self.assertEqual(302, response.status_code)
        self.assertEqual("/posts/", response.headers.get("Location"))

    def test_redirect_path_with_suffix(self):
        index_file = self.working_dir / "content" / "about.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)
        site.generate()

        client = Client(jinjabread.App(config))
        response = client.get("/about.html")

        self.assertEqual(302, response.status_code)
        self.assertEqual("/about", response.headers.get("Location"))

    def test_redirect_dir_path_with_missing_slash(self):
        index_file = self.working_dir / "content" / "posts" / "index.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)
        site.generate()

        client = Client(jinjabread.App(config))
        response = client.get("/posts")

        self.assertEqual(302, response.status_code)
        self.assertEqual("/posts/", response.headers.get("Location"))
