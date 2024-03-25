import itertools
import mimetypes
from pathlib import Path
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from werkzeug.utils import redirect
from .base import Site
from .config import Config


class App:

    def __init__(self, config):
        self.config = config

    def dispatch_request(self, request):
        url_path = Path(request.path)
        file_path = self.config.output_dir / url_path.relative_to("/")

        # Clean up URL path.
        if url_path.name == "index.html":
            return redirect(url_path.parent.as_posix().removesuffix("/") + "/")
        if url_path.suffix == ".html":
            return redirect(url_path.with_suffix("").as_posix())
        if file_path.is_dir() and not request.path.endswith("/"):
            return redirect(url_path.as_posix() + "/")

        # Clean up file path.
        if not file_path.exists() and file_path.with_suffix(".html").exists():
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


def serve(**kwargs):
    config = Config.load(**kwargs)
    site = Site(config)
    site.generate()

    extra_files = [
        path.as_posix()
        for path in itertools.chain(
            config.content_dir.glob("**/*"),
            config.layouts_dir.glob("**/*"),
            config.static_dir.glob("**/*"),
        )
        if path.is_file()
    ]
    run_simple(
        "127.0.0.1",
        8000,
        App(config),
        use_reloader=True,
        extra_files=extra_files,
    )
