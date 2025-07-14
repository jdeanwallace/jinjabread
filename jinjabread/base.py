import mimetypes
from pathlib import Path
import shutil
from jinja2 import Environment, FileSystemLoader
import markdown

from . import errors
from .utils import prettify_html, find_index_file


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

    def match_page(self, path):
        for page_factory in self.config.page_factories:
            page = page_factory.make_page(self, path)
            if path.match(page.glob_pattern):
                return page
        raise errors.PageNotMatchedError(f"No page matched: {path.as_posix()}")

    def generate(self):
        for content_path in self.config.content_dir.glob("**/*"):
            if content_path.is_dir():
                continue
            # Ignore hidden files and directories.
            if any(part.startswith(".") for part in content_path.parts):
                continue
            mime_type, _ = mimetypes.guess_type(content_path.name)
            if mime_type and not mime_type.startswith("text/"):
                output_path = self.config.output_dir / content_path.relative_to(
                    self.config.content_dir
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(content_path, output_path)
                continue
            try:
                page = self.match_page(content_path)
            except errors.PageNotMatchedError:
                continue
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

    def make_page(self, site, content_path):
        page = self.page_class(**self.page_initkwargs)
        page.setup(site, content_path)
        return page


class Page:
    def __init__(self, *, glob_pattern=None, context=None):
        self.glob_pattern = glob_pattern or "**/*"
        self.context = context or {}

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

    def _get_sibling_context_list(self):
        context_list = []
        for path in self.content_path.parent.iterdir():
            if path == self.content_path:
                continue
            if path.is_dir():
                try:
                    index_path = find_index_file(path)
                    page = self.site.match_page(index_path)
                except (FileNotFoundError, errors.PageNotMatchedError):
                    continue
                context_list.append(page.get_context())
                continue
            try:
                page = self.site.match_page(path)
            except errors.PageNotMatchedError:
                continue
            context_list.append(page.get_context())
        return context_list

    def get_context(self):
        relative_path = self.output_path.relative_to(self.site.config.output_dir)
        if not relative_path.stem == "index":
            url_path = "/" + relative_path.with_suffix("").as_posix()
        elif not relative_path.parent.name:
            url_path = "/"
        else:
            url_path = "/" + relative_path.parent.as_posix() + "/"
        context = (
            self.site.config.context
            | self.context
            | {
                "file_path": relative_path.as_posix(),
                "url_path": url_path,
            }
        )
        if self.content_path.stem == "index":
            context["pages"] = self._get_sibling_context_list()
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

    def __init__(self, *, layout_name, glob_pattern=None, **kwargs):
        self.layout_name = layout_name
        self.markdown = markdown.Markdown(extensions=["full_yaml_metadata"])
        super().__init__(glob_pattern=glob_pattern or "**/*.md", **kwargs)

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
