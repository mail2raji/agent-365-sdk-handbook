"""
sync_docs.py — mirror Phase content into the MkDocs `docs/` directory.

Why this exists: MkDocs requires `docs_dir` to be a *child* of the project root,
so we can't point it at the curriculum root directly. This script copies every
`*/README.md`, `*/exercises.md`, and the curriculum root markdown files into
`docs/` while preserving folder structure.

It also rewrites relative links that point to files NOT in `docs/` (e.g. code/
samples, requirements.txt) into absolute GitHub blob URLs so `mkdocs build
--strict` passes.

The script is idempotent — running it on top of an existing `docs/` is safe.

Usage:
    python tools/sync_docs.py

KID-FRIENDLY VERSION:
    Think of this script as a PHOTOCOPIER + SPELL-CHECK for markdown.
    1. It empties the `docs/` folder.
    2. It photocopies the top-level README/SETUP/GLOSSARY + every Phase's
       README.md and exercises.md into `docs/`.
    3. While copying, it RE-WRITES any link that points to a file the
       photocopier didn't bring along (like `code/app.py`) so it points
       to the file on GitHub instead. That way `mkdocs build --strict`
       (a very fussy proofreader) doesn't yell about broken links.
"""
from __future__ import annotations

import re                # regular expressions \u2014 a search-pattern language
import shutil            # high-level file/folder copy + delete
import sys
from pathlib import Path

# `Path(__file__)` = THIS file (sync_docs.py). `.parent.parent` = repo root.
ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
# Base URL for the GitHub blob view \u2014 used when we rewrite \"code/app.py\"-style links.
REPO_BLOB_BASE = "https://github.com/mail2raji/agent-365-sdk-handbook/blob/main"

# Files at the very top of the repo we always copy.
ROOT_FILES = ["README.md", "SETUP.md", "GLOSSARY.md"]
# Inside each Phase folder, we only copy these two markdowns.
PHASE_FILES = ["README.md", "exercises.md"]

# Match `[label](target "optional title")` BUT NOT image links `![alt](...)`.
# `(?<!\\!)` = negative look-behind \u2014 \"the char before [ must NOT be !\".
LINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)\s]+)(\s+\"[^\"]*\")?\)")


def _looks_external(target: str) -> bool:
    # Anything that starts with one of these prefixes is NOT a local file
    # \u2014 leave it alone (no rewrite needed).
    return target.startswith((
        "http://", "https://", "mailto:", "#", "/",
        "data:", "tel:", "ftp:",
    ))


def _normalize(rel: str) -> str:
    """Collapse ../ and ./ segments without touching the anchor / query.

    KID-FRIENDLY: turns \"a/b/../c#section\" into \"a/c#section\". We split off
    the anchor first so we don't mangle it.
    """
    anchor = ""
    for ch in ("#", "?"):
        if ch in rel:
            idx = rel.index(ch)
            anchor = rel[idx:]
            rel = rel[:idx]
            break
    parts: list[str] = []
    for seg in rel.replace("\\", "/").split("/"):
        if seg in ("", "."):
            continue
        if seg == ".." and parts and parts[-1] != "..":
            parts.pop()    # \"..\" means \"go up one\" \u2192 drop the last part
        else:
            parts.append(seg)
    return "/".join(parts) + anchor


def rewrite_links(markdown: str, source_rel: Path) -> str:
    # `source_rel` = where this markdown lives (relative to repo root).
    # `source_dir` = its folder \u2014 needed to resolve relative links.
    source_dir = source_rel.parent

    def repl(match: re.Match[str]) -> str:
        # For each `[text](target)` we find, decide: keep, or rewrite.
        text, target, title = match.group(1), match.group(2), match.group(3) or ""
        if _looks_external(target):
            return match.group(0)        # external \u2192 untouched

        # Turn the relative link into a path from the repo root.
        resolved = _normalize(str(source_dir / target)) if str(source_dir) not in ("", ".") else _normalize(target)
        resolved_no_anchor = resolved.split("#", 1)[0].split("?", 1)[0]

        # If the resolved path is a README/exercises markdown that lives in the
        # docs tree, leave it alone \u2014 MkDocs will resolve it.
        is_in_docs_tree = (
            resolved_no_anchor in ROOT_FILES
            or (
                resolved_no_anchor.endswith(("README.md", "exercises.md"))
                and resolved_no_anchor.startswith("Phase")
            )
        )
        if is_in_docs_tree:
            return match.group(0)

        # Anything else (code/, requirements.txt, sample scripts, manifest files)
        # gets rewritten to a GitHub blob URL so clicking still works on the site.
        absolute = f"{REPO_BLOB_BASE}/{resolved}"
        return f"[{text}]({absolute}{title})"

    return LINK_RE.sub(repl, markdown)


def copy_with_rewrite(src: Path, dst: Path, source_rel: Path) -> None:
    # Make sure the destination folder exists, then write a rewritten copy.
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8")
    rewritten = rewrite_links(text, source_rel)
    dst.write_text(rewritten, encoding="utf-8")


def is_phase_dir(p: Path) -> bool:
    # Our convention: folders that start with \"Phase\" are curriculum chapters.
    return p.is_dir() and p.name.startswith("Phase")


def sync() -> int:
    # STEP 1 \u2014 wipe and recreate `docs/` so old files don't linger.
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []

    # STEP 2 \u2014 copy the three top-level markdowns (README/SETUP/GLOSSARY).
    for name in ROOT_FILES:
        src = ROOT / name
        if not src.is_file():
            print(f"  skip (missing): {name}")
            continue
        dst = DOCS / name
        copy_with_rewrite(src, dst, Path(name))
        copied.append(str(dst.relative_to(ROOT)))

    # STEP 3 \u2014 for every Phase folder, copy its README.md + exercises.md.
    for phase in sorted(p for p in ROOT.iterdir() if is_phase_dir(p)):
        for name in PHASE_FILES:
            src = phase / name
            if not src.is_file():
                continue
            dst = DOCS / phase.name / name
            copy_with_rewrite(src, dst, Path(phase.name) / name)
            copied.append(str(dst.relative_to(ROOT)))

    # STEP 4 \u2014 friendly summary so we know it ran.
    print(f"Synced {len(copied)} file(s) into {DOCS.relative_to(ROOT)}/")
    for path in copied:
        print(f"  + {path}")
    return 0


if __name__ == "__main__":
    # `sys.exit(...)` returns the exit code to the shell.
    # 0 = success \u2192 useful in CI pipelines.
    sys.exit(sync())
