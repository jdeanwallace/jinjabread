# HTML prettifier improvements + tooling

**Date:** 2026-07-13
**Status:** Implemented across the `prettifier/*` branch stack; held for the 0.6.4 release
**Base:** the `0.6.4` inline-element bugfix (custom lxml serializer in `jinjabread/utils.py`)

## Background

`0.6.4` fixed the inline-element pretty-printing bug by giving `utils.py` a custom lxml serializer (`traverse` + `serialize`) that classifies elements as inline / block / preformatted and reflows only insignificant whitespace.

Research into how authoritative formatters solve this (Prettier's `htmlWhitespaceSensitivity: "css"`, `XML::LibXML::PrettyPrint`) confirms the approach is **canonical and correct**: parse → classify (inline/block/preformatted) → recurse, indenting only in block contexts → preserve whitespace adjacent to and inside inline elements and inside `pre`/`script`/`style` → collapse insignificant whitespace runs to a single space. No maintained Python library does this *and* normalizes messy Jinja/Markdown input (`bs4.prettify` breaks inline tags; lxml `pretty_print`/`etree.indent` inject rendering-affecting whitespace and don't normalize; `prettierfier` is conservative and unmaintained). **Custom stays the right call.**

This document plans incremental improvements. None change correctness; they improve test rigour, code clarity, output tightness, and dev tooling.

## Goals

- Strengthen confidence in the serializer with property/metamorphic tests over an adopted real-world corpus.
- Refactor the serializer into a clearer recursive form without changing output.
- Tighten output for short block elements ("compact" elements).
- Modernize the dev workflow with uv.
- Bring touched code into line with the global style guide.

## Non-goals

- Line-width/print-width wrapping of inline runs (real complexity, little value for a static-site generator — YAGNI).
- Handling runtime CSS `display` overrides (magic comments) — inherent limitation of all inference-based formatters; out of scope.
- Changing the established "reflow" output style beyond the compact-element tweak.

## Decisions

- **Attribute order:** preserve the author's **source order** (currently sorted alphabetically). Matches Prettier and convention; least surprising.
- **uv:** **full migration** — dev deps into `pyproject.toml` `[dependency-groups]`, add `uv.lock`, use `uv sync`; CI uses uv.
- **Testing:** **corpus + Hypothesis** — a curated corpus for deterministic real-world coverage, plus Hypothesis-generated inputs for automated edge-case discovery, both asserting the same invariants.

## The work as a reviewable branch stack

The `0.6.4` inline-element bugfix lands first as its own PR and release — it is an urgent user-facing fix, separate from this improvement work. The improvements then follow the repo's stacked-PR convention (see the git style guide): branches are named `<topic>/<N>-<description>`, each based on the previous one, landed bottom-up one PR at a time. Branch `0` holds only the design — this spec plus the implementation plans — so every implementation PR is reviewed against an already-merged spec.

```
master (with 0.6.4 merged)
 └─ prettifier/0-design               # this spec + the implementation plans; lands first
     └─ prettifier/1-uv-tooling           # dev workflow → uv; the toolchain every later branch runs on
         └─ prettifier/2-test-hardening       # property/metamorphic suite; adds the hypothesis dev dep
             └─ prettifier/3-serializer-refactor  # recursive reflow; behavior-preserving; style-compliant
                 └─ prettifier/4-compact-elements # short block elements on one line (style change)
```

Ordering rationale:

- uv first so every later branch runs on the faster, locked toolchain, and so the `hypothesis` dev dependency added in `test-hardening` drops straight into the new `pyproject.toml` `[dependency-groups]` — no `requirements.ini` entry to add and then undo.
- test-hardening before the refactor so "behavior-preserving" is actually enforced (idempotence + render-invariance over a large corpus, not just the ~72 hand-written examples).
- compact-elements after the refactor: cleaner to implement in the recursive form, and the metamorphic tests survive it because it only alters *insignificant* whitespace.

Style-guide conformance is folded into each branch that touches a file.

## Branch: `test-hardening`

The oracle problem: a formatter's exact output is style-specific, so we cannot adopt another tool's golden files. We test **metamorphic relations** that hold regardless of output style. No production code changes on this branch.

### Invariants

- **Idempotence:** `prettify(prettify(x)) == prettify(x)`.
- **Render-invariance:** prettifying must not change what the page renders, asserted with an oracle that is **independent of the serializer's own logic** (does not reuse `INLINE_TAGS`/`OPAQUE_TAGS` or `serialize`):
  - `visible_text(html)`: concatenate all text nodes (excluding `script`/`style`) in document order, collapse whitespace runs to single spaces. Catches lost / added / reordered words and the "linkthen" class of spacing bug.
  - `structure(html)`: the tag tree with attributes compared order-independently, plus verbatim content of `pre`/`textarea`/`script`/`style`. Catches structural changes and whitespace-sensitive corruption.
  - Assert `visible_text(x) == visible_text(prettify(x))` and `structure(x) == structure(prettify(x))`.
  - The oracle can only yield false negatives (too coarse), never false positives, so it is a safe net; `structure` + `visible_text` together make it strong.

### Corpus (license-checked)

- **html5lib-tests** `serializer/*.test` (esp. `whitespace.test`) — the de-facto standard HTML5 corpus. **MIT-licensed** (verified), compatible with jinjabread's MIT license. Vendor the relevant test *inputs* under `tests/corpus/html5lib/`, including upstream `LICENSE` + a `SOURCE.md` note recording the commit vendored.
- **Our own authored inputs** covering known-hard whitespace cases (inline runs, punctuation adjacency, mixed inline/block, nested inline, `pre`/`script`). Inspired by — not copied from — Prettier's documented issues; test *scenarios* aren't copyrightable, and authoring our own avoids Prettier's fixture-license ambiguity (Prettier is MIT, but some fixtures are synced from other-licensed projects and the HTML fixtures' provenance isn't clearly stated). We do **not** vendor Prettier fixtures.
- A few real full HTML documents we control (e.g. sampled from the consuming site's own generated output).

### Hypothesis

- A `hypothesis` strategy builds random HTML trees from a fixed tag vocabulary (block, inline, void, one preformatted) with text and **randomly injected insignificant whitespace** (spaces / newlines / tabs) between and around elements, serializes to a string, and asserts the invariants above.
- Pin determinism for CI (seeded / `derandomize`) so a run failing surfaces a real minimal counterexample (via shrinking) rather than intermittent noise.
- `hypothesis` is a **dev-only** dependency (not shipped to PyPI consumers), added to the dev `[dependency-groups]` established by the `uv-tooling` branch.

## Branch: `serializer-refactor`

Replace the token-stream (`traverse` emitting open/text/close/tail, consumed by `serialize` with index-based prev/next look-ahead) with a **recursive tree reflow**: `render(node, depth) -> str` that partitions each element's children into inline runs (text + inline elements, emitted atomically with collapsed-but-boundary-preserving whitespace) and block children (each recursed on its own indented line), with `pre`/`script`/`style`/comments emitted verbatim. This localizes every whitespace decision to a single inline run — no cross-token look-ahead — matching the reference implementations. **Behavior-preserving:** all existing snapshot tests and the `test-hardening` invariants must stay green. Also applies the **preserve-source-order** attribute decision (removes the `sorted(...)` call; updates `test_prettify_html5`).

## Branch: `compact-elements`

Keep a block element on one line when its entire content is a single inline run, producing `<li>One</li>` and `<title>Document</title>` instead of the current three-line form. The compact set is the `XML::LibXML::PrettyPrint` "compact" category — `title`, `caption`, `li`, `dd`, `dt`, `th`, `td` — plus `option` and `figcaption`. `p` and headings (`h1`–`h6`) are **excluded**: they hold prose that can be long, and the existing reflow form is fine for them. (The set is a constant; revisiting it later is a one-line change.) Updates affected snapshot tests; the `test-hardening` invariants stay green (only insignificant whitespace changes). This changes the consuming site's HTML formatting (cosmetic).

## Branch: `uv-tooling` (base of the stack)

- Move dev dependencies (`black`, `coverage`, `twine`, `hypothesis`, plus runtime deps as needed) into `pyproject.toml` (`[dependency-groups]` for dev).
- Add `uv.lock`; replace the `requirements.ini` → `requirements.txt` (pip-tools) flow. Keep `requirements.txt` only if a consumer needs it, otherwise remove.
- Update `.circleci/config.yml` to install uv and use `uv sync` / `uv run`.
- Update `README`/contributor notes for the uv workflow.

## Testing and CI

- All branches keep the full `unittest` suite green (`python -m unittest discover .`, or `uv run` equivalent).
- `test-hardening` adds the property/metamorphic suite; runs in CI.
- `black --check .` stays green on every branch.

## Risks and mitigations

- **Refactor changes output subtly** → guarded by existing snapshots + the `test-hardening` invariants; land `test-hardening` first.
- **Hypothesis nondeterminism in CI** → seed / derandomize; commit failing cases as regression examples.
- **Compact set too aggressive** (e.g. compacting `p` surprises) → keep the set conservative; the set is a documented constant; the invariants still protect correctness.
- **Vendored corpus licensing** → include upstream license/attribution for the vendored html5lib-tests corpus. We do not vendor Prettier fixtures.

## Success criteria

- Property/metamorphic suite (corpus + Hypothesis) passes and enforces idempotence + render-invariance.
- Serializer refactor merges with identical output (all snapshots + invariants green).
- Compact-element output ships with updated snapshots; invariants unchanged.
- uv is the documented dev workflow; CI green.
- Touched files conform to the global style guide.
