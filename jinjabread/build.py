from .base import Site
from .parsers import Config


def build(project_dir):
    config = Config.load(project_dir)
    Site(config).generate()
