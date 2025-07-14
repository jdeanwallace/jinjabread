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
        index_file = self.working_dir / "content" / "index.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        index_page = site.match_page(Path("content/index.html"))
        self.assertDictEqual(
            {
                "file_path": "index.html",
                "url_path": "/",
                "pages": [],
            },
            index_page.get_context(),
        )

    def test_context_variables_on_dir_index_page(self):
        index_file = self.working_dir / "content" / "posts" / "index.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        index_page = site.match_page(Path("content/posts/index.html"))
        self.assertDictEqual(
            {
                "file_path": "posts/index.html",
                "url_path": "/posts/",
                "pages": [],
            },
            index_page.get_context(),
        )

    def test_context_variables_on_root_page(self):
        index_file = self.working_dir / "content" / "about.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        index_page = site.match_page(Path("content/about.html"))
        self.assertDictEqual(
            {
                "file_path": "about.html",
                "url_path": "/about",
            },
            index_page.get_context(),
        )

    def test_context_variables_on_dir_page(self):
        index_file = self.working_dir / "content" / "posts" / "post1.html"
        index_file.parent.mkdir(parents=True)
        index_file.touch()

        config = jinjabread.Config.load()
        site = jinjabread.Site(config)

        index_page = site.match_page(Path("content/posts/post1.html"))
        self.assertDictEqual(
            {
                "file_path": "posts/post1.html",
                "url_path": "/posts/post1",
            },
            index_page.get_context(),
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
