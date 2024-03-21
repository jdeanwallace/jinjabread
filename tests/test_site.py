import os
import shutil
import unittest
import tempfile
from pathlib import Path

import jinjabread


def print_tree(dir):
    for path in Path(dir).rglob("*"):
        print(path.relative_to(dir).as_posix())


def list_files(dir):
    return [
        path.relative_to(dir).as_posix()
        for path in Path(dir).rglob("*")
        if path.is_file()
    ]


class TestHtmlMixin:

    def assertHtmlEqual(self, first, second):
        return self.assertEqual(
            jinjabread.prettify_html(first), jinjabread.prettify_html(second)
        )


class SiteTest(TestHtmlMixin, unittest.TestCase):

    def setUp(self):
        self.project_dir = Path(tempfile.mkdtemp())
        os.chdir(self.project_dir)
        self.addCleanup(shutil.rmtree, self.project_dir)

        self.test_data_dir = Path(__file__).parent / "test_data"

    def test_site_config_defaults(self):
        config = jinjabread.Config.load("mysite")

        self.assertEqual("mysite", config.project_dir.name)
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

    def test_html_content(self):
        content_path = self.project_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                <h1>Hello, World{# This is a comment #}</h1>
                """
            )
        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

        self.assertHtmlEqual(
            """
            <h1>Hello, World</h1>
            """,
            Path("public/home.html").read_text(),
        )

    def test_html_content_extends_layout(self):
        content_path = self.project_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                {% extends 'base.html' %}
                {% block body %}
                <p>Blah blah blah</p>
                {% endblock body %}
                """
            )
        layout_path = self.project_dir / "layouts" / "base.html"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        with layout_path.open("w") as file:
            file.write(
                """
                <h1>Hello, World</h1>
                {% block body %}
                {% endblock body %}
                """
            )

        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

        self.assertHtmlEqual(
            """
            <h1>Hello, World</h1>
            <p>Blah blah blah</p>
            """,
            Path("public/home.html").read_text(),
        )

    def test_html_content_includes_layout(self):
        content_path = self.project_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                <h1>Hello, World</h1>
                {% include 'message.txt' %}
                """
            )
        layout_path = self.project_dir / "layouts" / "message.txt"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        with layout_path.open("w") as file:
            file.write(
                """
                <p>Blah blah blah</p>
                """
            )

        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

        self.assertHtmlEqual(
            """
            <h1>Hello, World</h1>
            <p>Blah blah blah</p>
            """,
            Path("public/home.html").read_text(),
        )
        self.assertFalse(Path("public/message.txt").exists())

    def test_html_content_includes_content(self):
        content_path = self.project_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write(
                """
                <h1>Hello, World</h1>
                {% include 'message.txt' %}
                """
            )
        content_path2 = self.project_dir / "content" / "message.txt"
        content_path2.parent.mkdir(parents=True, exist_ok=True)
        with content_path2.open("w") as file:
            file.write(
                """
                <p>Blah blah blah</p>
                """
            )

        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

        self.assertHtmlEqual(
            """
            <h1>Hello, World</h1>
            <p>Blah blah blah</p>
            """,
            Path("public/home.html").read_text(),
        )
        self.assertTrue(Path("public/message.txt").exists())

    def test_text_content(self):
        content_path = self.project_dir / "content" / "home.txt"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("""Hello, World{# This is a comment #}""")

        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

        self.assertEqual("""Hello, World""", Path("public/home.txt").read_text())

    def test_markdown_content(self):
        shutil.copytree(
            self.test_data_dir / "test_markdown_content",
            self.project_dir,
            dirs_exist_ok=True,
        )

        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

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
        content_path = self.project_dir / "content" / "posts" / "index.html"
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
        content_path = self.project_dir / "content" / "posts" / "post1.html"
        with content_path.open("w") as file:
            file.write(
                """
                <p>I am post 1.</p>
                """
            )
        content_path = self.project_dir / "content" / "posts" / "post2.html"
        with content_path.open("w") as file:
            file.write(
                """
                <p>I am post 2.</p>
                """
            )
        content_path = self.project_dir / "content" / "posts" / "post3.html"
        with content_path.open("w") as file:
            file.write(
                """
                <p>I am post 3.</p>
                """
            )

        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

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
            self.project_dir,
            dirs_exist_ok=True,
        )

        config = jinjabread.Config.load(".")
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

    def test_copy_static_content(self):
        content_path = self.project_dir / "content" / "dummy.jpg"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.touch()

        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

        self.assertTrue(Path("public/dummy.jpg").exists())

    def test_copy_static_directory(self):
        static_path = self.project_dir / "static" / "dummy.jpg"
        static_path.parent.mkdir(parents=True, exist_ok=True)
        static_path.touch()

        config = jinjabread.Config.load(".")
        site = jinjabread.Site(config)
        site.generate()

        self.assertTrue(Path("public/static/dummy.jpg").exists())
