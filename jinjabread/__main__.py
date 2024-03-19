import argparse
from . import create_new_project, build, serve

def main(action, **options):
    match action:
        case "new":
            create_new_project(options["site_name"])

        case "build":
            build(options["project_dir"])

        case "serve":
            serve(options["project_dir"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="jinjabread",
        description="A Python-based static site generator using Jinja templates.",
    )
    subparsers = parser.add_subparsers(required=True, dest="action")
    new_site_parser = subparsers.add_parser("new", help="Create new site.")
    new_site_parser.add_argument("site_name", help="Your site name.")
    serve_parser = subparsers.add_parser("serve", help="Run development web server.")
    serve_parser.add_argument("project_dir", help="The site directory.")
    build_parser = subparsers.add_parser("build", help="Build site.")
    build_parser.add_argument("project_dir", help="The site directory.")
    args = parser.parse_args()

    main(**vars(args))
