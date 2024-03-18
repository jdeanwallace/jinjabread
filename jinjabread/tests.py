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


class SiteTest(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path(tempfile.mkdtemp())
        os.chdir(self.project_dir)
        self.addCleanup(shutil.rmtree, self.project_dir)

    def test_html_content(self):
        content_path = self.project_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("<h1>Hello, World{# This is a comment #}</h1>")

        site = jinjabread.Site(
            pages=[
                jinjabread.Page(),
            ]
        )
        site()

        self.assertEqual(
            "<h1>Hello, World</h1>", Path("public/home.html").read_text()
        )
    
    def test_html_content_extends_layout(self):
        content_path = self.project_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("{% extends 'base.html' %}{% block body %}<p>Blah blah blah</p>{% endblock body %}")
        layout_path = self.project_dir / "layouts" / "base.html"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        with layout_path.open("w") as file:
            file.write("<h1>Hello, World</h1>{% block body %}{% endblock body %}")

        site = jinjabread.Site(
            pages=[
                jinjabread.Page(),
            ]
        )
        site()

        self.assertEqual(
            "<h1>Hello, World</h1><p>Blah blah blah</p>", Path("public/home.html").read_text()
        )
    
    def test_html_content_includes_layout(self):
        content_path = self.project_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("<h1>Hello, World</h1>{% include 'message.txt' %}")
        layout_path = self.project_dir / "layouts" / "message.txt"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        with layout_path.open("w") as file:
            file.write("<p>Blah blah blah</p>")

        site = jinjabread.Site(
            pages=[
                jinjabread.Page(),
            ]
        )
        site()

        self.assertEqual(
            "<h1>Hello, World</h1><p>Blah blah blah</p>", Path("public/home.html").read_text()
        )
        self.assertFalse(Path("public/message.txt").exists())
    
    def test_html_content_includes_content(self):
        content_path = self.project_dir / "content" / "home.html"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("<h1>Hello, World</h1>{% include 'message.txt' %}")
        content_path2 = self.project_dir / "content" / "message.txt"
        content_path2.parent.mkdir(parents=True, exist_ok=True)
        with content_path2.open("w") as file:
            file.write("<p>Blah blah blah</p>")

        site = jinjabread.Site(
            pages=[
                jinjabread.Page(),
            ]
        )
        site()

        self.assertEqual(
            "<h1>Hello, World</h1><p>Blah blah blah</p>", Path("public/home.html").read_text()
        )
        self.assertTrue(Path("public/message.txt").exists())

    def test_text_content(self):
        content_path = self.project_dir / "content" / "home.txt"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("Hello, World{# This is a comment #}")

        site = jinjabread.Site(
            pages=[
                jinjabread.Page(),
            ]
        )
        site()

        self.assertEqual("Hello, World", Path("public/home.txt").read_text())

    def test_markdown_content(self):
        content_path = self.project_dir / "content" / "home.md"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("w") as file:
            file.write("# Hello, World{# This is a comment #}")
        layout_path = self.project_dir / "layouts" / "base.html"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        with layout_path.open("w") as file:
            file.write("{{ content }}{# This is another comment #}")

        site = jinjabread.Site(
            pages=[
                jinjabread.MarkdownPage("base.html"),
            ]
        )
        site()

        self.assertEqual(
            "<h1>Hello, World</h1>", Path("public/home.html").read_text()
        )
    
    def test_copy_static_content(self):
        content_path = self.project_dir / "content" / "dummy.jpg"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.touch()

        site = jinjabread.Site(
            pages=[
                jinjabread.Page(),
            ]
        )
        site()
    
    def test_copy_static_directory(self):
        static_path = self.project_dir / "static" / "dummy.jpg"
        static_path.parent.mkdir(parents=True, exist_ok=True)
        static_path.touch()

        site = jinjabread.Site(
            pages=[
                jinjabread.Page(),
            ]
        )
        site()

        self.assertTrue(Path("public/static/dummy.jpg").exists())
