import mimetypes
from pathlib import Path
import shutil
from jinja2 import Environment, FileSystemLoader
import markdown

from .utils import prettify_html


class Site:
    def __init__(self, config):
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(
                searchpath=[
                    self.config.layouts_dir,
                    self.config.content_dir,
                ],
            ),
        )

    def render_template(self, template_name, **context):
        template = self.env.get_template(template_name)
        return template.render(context)

    def match_page_factory(self, path):
        for page_factory in self.config.page_factories:
            if path.match(page_factory.page_class.glob_pattern):
                return page_factory

    def generate(self):
        for content_path in self.config.content_dir.glob("**/*"):
            if content_path.is_dir():
                continue
            mime_type, _ = mimetypes.guess_type(content_path.name)
            if mime_type and not mime_type.startswith("text/"):
                output_path = self.config.output_dir / content_path.relative_to(
                    self.config.content_dir
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(content_path, output_path)
                continue
            page_factory = self.match_page_factory(content_path)
            if not page_factory:
                continue
            page = page_factory.new_page(self, content_path)
            page.generate()

        if self.config.static_dir.exists():
            shutil.copytree(
                self.config.static_dir,
                self.config.output_dir / self.config.static_dir.name,
                dirs_exist_ok=True,
            )


class PageFactory:
    def __init__(self, page_class, **initkwargs):
        self.page_class = page_class
        self.page_initkwargs = initkwargs

    def new_page(self, site, content_path):
        page = self.page_class(**self.page_initkwargs)
        page.setup(site, content_path)
        return page


class Page:
    glob_pattern = "**/*"

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def setup(self, site, content_path):
        self.site = site
        self.content_path = content_path
        self.output_path = self.get_output_path()

    def get_output_path(self):
        return self.site.config.output_dir / self.content_path.relative_to(
            self.site.config.content_dir
        )

    def get_template_name(self):
        return self.content_path.relative_to(self.site.config.content_dir).as_posix()

    def get_context(self):
        file_path = self.output_path.relative_to(self.site.config.output_dir)
        url_path = file_path.with_suffix("")
        if url_path.name == "index":
            url_path = url_path.parent
        context = self.site.config.context | {
            "file_path": file_path,
            "url_path": f"/{url_path.as_posix()}",
        }
        if self.content_path.stem == "index":
            items = []
            for path in self.content_path.parent.glob("*"):
                if path == self.content_path or path.is_dir() or path.stem == "index":
                    continue
                page_factory = self.site.match_page_factory(path)
                if not page_factory:
                    continue
                page = page_factory.new_page(self.site, path)
                items.append(page.get_context())
            context |= {"pages": items}
        return context

    def render(self):
        template_name = self.get_template_name()
        text = self.site.render_template(template_name, **self.get_context())
        if self.site.config.prettify_html and self.output_path.suffix == ".html":
            return prettify_html(text)
        return text

    def generate(self):
        text = self.render()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w") as file:
            file.write(text)


class MarkdownPage(Page):
    glob_pattern = "**/*.md"

    def __init__(self, *, layout_name):
        self.layout_name = layout_name
        self.markdown = markdown.Markdown(extensions=["full_yaml_metadata"])

    def get_output_path(self):
        return super().get_output_path().with_suffix(Path(self.layout_name).suffix)

    def get_template_name(self):
        return self.layout_name

    def get_context(self):
        context = super().get_context()
        text = self.site.render_template(
            self.content_path.relative_to(self.site.config.content_dir).as_posix(),
            **context,
        )
        context["content"] = self.markdown.convert(text)
        if self.markdown.Meta:
            context.update(self.markdown.Meta)
        self.markdown.reset()
        return context
