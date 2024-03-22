import argparse
from . import new, build, serve


def main(action, **options):
    match action:
        case "new":
            new(**options)

        case "build":
            build(**options)

        case "serve":
            serve(**options)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="jinjabread",
        description="A Python-based static site generator using Jinja templates.",
    )
    subparsers = parser.add_subparsers(required=True, dest="action")

    new_site_parser = subparsers.add_parser("new", help="Create new site.")
    new_site_parser.add_argument("project_dir", help="The site directory.")

    serve_parser = subparsers.add_parser("serve", help="Run development web server.")
    serve_parser.add_argument("project_dir", help="The site directory.")
    serve_parser.add_argument(
        "--config",
        dest="config_file",
        default=argparse.SUPPRESS,
        help="Optional. The config file",
    )

    build_parser = subparsers.add_parser("build", help="Build site.")
    build_parser.add_argument("project_dir", help="The site directory.")
    build_parser.add_argument(
        "--config",
        dest="config_file",
        default=argparse.SUPPRESS,
        help="Optional. The config file",
    )

    args = parser.parse_args()
    main(**vars(args))
