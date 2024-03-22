from .base import Site
from .config import Config


def build(**kwargs):
    config = Config.load(**kwargs)
    site = Site(config)
    site.generate()
