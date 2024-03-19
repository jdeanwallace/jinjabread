from . import Site, MarkdownPage


def build(project_dir):
    Site(project_dir=project_dir, pages=[MarkdownPage(layout_name="base.html")])()
