import itertools
import mimetypes
from pathlib import Path
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from werkzeug.utils import redirect
from . import build


class App:

    def __init__(self, project_dir):
        self.public_dir = Path(project_dir) / "public"

    def dispatch_request(self, request):
        path = Path(request.path)
        if path.suffix == ".html":
            return redirect(path.with_suffix(""))

        file_path = self.public_dir / path.relative_to("/")
        if (not file_path.exists() or file_path.is_dir()) and file_path.with_suffix(
            ".html"
        ).exists():
            file_path = file_path.with_suffix(".html")
        elif file_path.is_dir():
            file_path /= "index.html"

        try:
            with file_path.open("rb") as file:
                mimetype, _ = mimetypes.guess_type(file_path.name)
                return Response(
                    file.read(),
                    status=200,
                    mimetype=mimetype,
                )
        except FileNotFoundError:
            return Response(f"File Not Found: {file_path}", status=404)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def serve(project_dir):
    build(project_dir)
    extra_files = [
        path.as_posix()
        for path in itertools.chain(
            Path(f"{project_dir}/content").rglob("*"),
            Path(f"{project_dir}/layouts").rglob("*"),
            Path(f"{project_dir}/static").rglob("*"),
        )
        if path.is_file()
    ]
    run_simple(
        "127.0.0.1",
        8000,
        App(project_dir),
        use_reloader=True,
        extra_files=extra_files,
    )
