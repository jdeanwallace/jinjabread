import importlib
import bs4


def prettify_html(text):
    soup = bs4.BeautifulSoup(text, "html.parser")
    return soup.prettify(formatter=bs4.formatter.HTMLFormatter(indent=2))


def load_page_class(dot_path):
    parts = dot_path.rsplit(".", 2)
    if len(parts) != 2:
        raise TypeError("Invalid page type.")
    module = importlib.import_module(parts[0])
    return getattr(module, parts[1])
