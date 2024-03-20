import contextlib
import dataclasses
import importlib
from pathlib import Path
import tomllib
import typing
from .base import PageFactory


def load_page_class(dot_path):
    parts = dot_path.rsplit(".", 2)
    if len(parts) != 2:
        raise TypeError("Invalid page type.")
    module = importlib.import_module(parts[0])
    return getattr(module, parts[1])


@dataclasses.dataclass
class Config:
    project_dir: Path
    content_dir: Path
    layouts_dir: Path
    static_dir: Path
    output_dir: Path
    prettify_html: bool
    context: dict
    page_factories: typing.List[PageFactory]

    @classmethod
    def load(cls, project_dir):
        project_dir = Path(project_dir)
        
        with (Path(__file__).parent / "defaults.toml").open("rb") as file:
            data = tomllib.load(file)

        with contextlib.suppress(FileNotFoundError):
            with (project_dir / "jinjabread.toml").open("rb") as file:
                data |= tomllib.load(file)

        page_factories = []
        for page_kwargs in data.get("pages", []):
            page_class = load_page_class(page_kwargs.pop("type"))
            page_factory = PageFactory(page_class, **page_kwargs)
            page_factories.append(page_factory)

        return Config(
            project_dir=project_dir,
            content_dir=project_dir / data["content_dir"],
            layouts_dir=project_dir / data["layouts_dir"],
            static_dir=project_dir / data["static_dir"],
            output_dir=project_dir / data["output_dir"],
            prettify_html=data["prettify_html"],
            context=data["context"],
            page_factories=page_factories,
        )

    def as_dict(self):
        return dataclasses.asdict(self)
