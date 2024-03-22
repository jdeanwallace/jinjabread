from pathlib import Path
from .config import CONFIG_FILENAME


def new(*, project_dir=None):
    suppress_existing_project_dir_error = project_dir is None

    project_dir = Path(project_dir or ".")
    project_dir.mkdir(exist_ok=suppress_existing_project_dir_error)

    config_file = project_dir / CONFIG_FILENAME
    with config_file.open("w") as file:
        file.write(
            f"""
[context]
  site_name = "{project_dir.name}"
  url_origin = "http://127.0.0.1:8000"
""".lstrip()
        )
    content_path = project_dir / "content" / "index.md"
    content_path.parent.mkdir(parents=True)
    with content_path.open("w") as file:
        file.write(
            """
---
author: me
---
# Hello, World!
This is my new website.
""".lstrip()
        )
    layout_file = project_dir / "layouts" / "base.html"
    layout_file.parent.mkdir(parents=True)
    with layout_file.open("w") as file:
        file.write(
            """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site_name }}</title>
  </head>
  <body>
    {{ content }}
    <p>Created by {{ author }}.</p>
  </body>
</html>
""".lstrip()
        )
