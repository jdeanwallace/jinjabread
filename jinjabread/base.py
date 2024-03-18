from pathlib import Path
import re
import shutil

from jinja2 import Environment, FileSystemLoader
import markdown


class Site:

    def __init__(self, *, pages):
        self.content_dir = Path("content")
        self.layouts_dir = Path("layouts")
        self.static_dir = Path("static")
        self.output_dir = Path("public")
        self.env = Environment(
            loader=FileSystemLoader(searchpath=[self.layouts_dir, self.content_dir])
        )
        self.pages = pages
    
    def __call__(self):
        self.generate()

    def render_template(self, template_name, **context):
        template = self.env.get_template(template_name)
        return template.render(context)

    def match_page(self, path):
        for page in self.pages:
            if re.match(page.path_pattern, path.name):
                return page

    def generate(self):
        for content_path in self.content_dir.rglob("*"):
            if content_path.is_dir():
                continue
            if content_path.suffix not in [".html", ".md", ".txt"]:
                output_path = self.output_dir / content_path.relative_to(
                    self.content_dir
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(content_path, output_path)
                continue
            page = self.match_page(content_path)
            if not page:
                continue
            page(self, content_path)
        
        if self.static_dir.exists():
            shutil.copytree(self.static_dir, self.output_dir / self.static_dir.name, dirs_exist_ok=True)
        


class Page:
    path_pattern = r".*"

    def __call__(self, site, content_path):
        self.site = site
        self.content_path = content_path
        self.output_path = self.get_output_path()
        self.generate()

    def get_output_path(self):
        return self.site.output_dir / self.content_path.relative_to(
            self.site.content_dir
        )
    
    def get_template_name(self):
        return self.content_path.relative_to(self.site.content_dir).as_posix()

    def get_context(self):
        path = "/" + self.output_path.relative_to(self.site.output_dir).as_posix()
        return {
            "path": path,
        }

    def render(self):
        template_name = self.get_template_name()
        return self.site.render_template(template_name, **self.get_context())

    def generate(self):
        text = self.render()
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w") as file:
            file.write(text)


class MarkdownPage(Page):
    path_pattern = r".*\.md"

    def __init__(self, layout_name):
        self.layout_name = layout_name
    
    def get_output_path(self):
        return super().get_output_path().with_suffix(Path(self.layout_name).suffix)
    
    def get_template_name(self):
        return self.layout_name

    def get_context(self):
        context = super().get_context()
        text = self.site.render_template(
            self.content_path.relative_to(self.site.content_dir).as_posix(), **context
        )
        context["content"] = markdown.markdown(text)
        return context
