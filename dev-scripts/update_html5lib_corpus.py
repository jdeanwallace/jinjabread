#!/usr/bin/env python3
"""Roll the vendored html5lib-tests serializer corpus forward.

Re-downloads the serializer `*.test` files (and the LICENSE) from html5lib-tests
at a given ref, records the resolved commit in SOURCE.md, and reports what
changed. Run it by hand, then review the diff and run the suite before
committing — a bump is a deliberate dependency roll, not something the everyday
test run does over the network.

    python3 dev-scripts/update_html5lib_corpus.py             # latest master
    python3 dev-scripts/update_html5lib_corpus.py --ref v1.1  # a tag or commit SHA
"""

import argparse
import json
import re
import urllib.request
from pathlib import Path

REPO = "html5lib/html5lib-tests"
CORPUS_DIR = Path(__file__).resolve().parent.parent / "tests" / "corpus" / "html5lib"


def _fetch(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "jinjabread-corpus-updater"}
    )
    with urllib.request.urlopen(request) as response:
        return response.read()


def _fetch_json(url):
    return json.loads(_fetch(url))


def resolve_commit(ref):
    return _fetch_json(f"https://api.github.com/repos/{REPO}/commits/{ref}")["sha"]


def list_serializer_tests(sha):
    entries = _fetch_json(
        f"https://api.github.com/repos/{REPO}/contents/serializer?ref={sha}"
    )
    return sorted(e["name"] for e in entries if e["name"].endswith(".test"))


def download(sha, path_in_repo, destination):
    destination.write_bytes(
        _fetch(f"https://raw.githubusercontent.com/{REPO}/{sha}/{path_in_repo}")
    )


def record_commit(sha):
    source = CORPUS_DIR / "SOURCE.md"
    source.write_text(
        re.sub(r"Commit: `[0-9a-f]+`", f"Commit: `{sha}`", source.read_text())
    )


def main():
    parser = argparse.ArgumentParser(
        description="Roll the vendored html5lib-tests serializer corpus forward."
    )
    parser.add_argument("--ref", default="master", help="branch, tag, or commit SHA")
    args = parser.parse_args()

    sha = resolve_commit(args.ref)
    print(f"Resolved {args.ref} -> {sha}")

    upstream = list_serializer_tests(sha)
    local = {path.name for path in CORPUS_DIR.glob("*.test")}

    for name in upstream:
        before = (CORPUS_DIR / name).read_bytes() if name in local else None
        download(sha, f"serializer/{name}", CORPUS_DIR / name)
        after = (CORPUS_DIR / name).read_bytes()
        status = (
            "unchanged" if before == after else "added" if before is None else "updated"
        )
        print(f"  {name}: {status}")

    for name in local - set(upstream):
        (CORPUS_DIR / name).unlink()
        print(f"  {name}: removed (gone upstream)")

    download(sha, "LICENSE", CORPUS_DIR / "LICENSE")
    record_commit(sha)

    print("\nDone. Review the diff, then run the tests before committing:")
    print("  uv run python -m unittest tests.test_html5lib_corpus")


if __name__ == "__main__":
    main()
