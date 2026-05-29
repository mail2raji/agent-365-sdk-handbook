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
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO_BLOB_BASE = "https://github.com/mail2raji/agent-365-sdk-handbook/blob/main"

ROOT_FILES = ["README.md", "SETUP.md", "GLOSSARY.md"]
PHASE_FILES = ["README.md", "exercises.md"]

LINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)\s]+)(\s+\"[^\"]*\")?\)")


def _looks_external(target: str) -> bool:
    return target.startswith((
        "http://", "https://", "mailto:", "#", "/",
        "data:", "tel:", "ftp:",
    ))


def _normalize(rel: str) -> str:
    """Collapse ../ and ./ segments without touching the anchor / query."""
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
            parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts) + anchor


def rewrite_links(markdown: str, source_rel: Path) -> str:
    source_dir = source_rel.parent

    def repl(match: re.Match[str]) -> str:
        text, target, title = match.group(1), match.group(2), match.group(3) or ""
        if _looks_external(target):
            return match.group(0)

        resolved = _normalize(str(source_dir / target)) if str(source_dir) not in ("", ".") else _normalize(target)
        resolved_no_anchor = resolved.split("#", 1)[0].split("?", 1)[0]

        # If the resolved path is a README/exercises markdown that lives in the
        # docs tree, leave it alone — MkDocs will resolve it.
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
        # gets rewritten to a GitHub blob URL.
        absolute = f"{REPO_BLOB_BASE}/{resolved}"
        return f"[{text}]({absolute}{title})"

    return LINK_RE.sub(repl, markdown)


def copy_with_rewrite(src: Path, dst: Path, source_rel: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8")
    rewritten = rewrite_links(text, source_rel)
    dst.write_text(rewritten, encoding="utf-8")


def is_phase_dir(p: Path) -> bool:
    return p.is_dir() and p.name.startswith("Phase")


def sync() -> int:
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []

    for name in ROOT_FILES:
        src = ROOT / name
        if not src.is_file():
            print(f"  skip (missing): {name}")
            continue
        dst = DOCS / name
        copy_with_rewrite(src, dst, Path(name))
        copied.append(str(dst.relative_to(ROOT)))

    for phase in sorted(p for p in ROOT.iterdir() if is_phase_dir(p)):
        for name in PHASE_FILES:
            src = phase / name
            if not src.is_file():
                continue
            dst = DOCS / phase.name / name
            copy_with_rewrite(src, dst, Path(phase.name) / name)
            copied.append(str(dst.relative_to(ROOT)))

    print(f"Synced {len(copied)} file(s) into {DOCS.relative_to(ROOT)}/")
    for path in copied:
        print(f"  + {path}")
    return 0


if __name__ == "__main__":
    sys.exit(sync())
