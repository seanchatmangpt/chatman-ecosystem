#!/usr/bin/env python3
"""Fail-closed structural verifier for The Chatman Ecosystem mdBook."""
from __future__ import annotations
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SUMMARY = DOCS / "SUMMARY.md"

CANONICAL_50 = [f"{i:02d}-" for i in range(1, 51)]
FORMAL_50 = [f"{i:02d}_" for i in range(0, 50)]
READER_SPINE = {
    "README.md",
    "51-ecosystem-map.md",
    "52-repository-atlas.md",
    "53-month-in-review.md",
    "54-current-standing.md",
    "55-pull-system.md",
    "56-receipts-replay-evidence.md",
    "57-operating-control-plane.md",
    "58-falsifiers-open-work.md",
    "59-roadmap-autonomous-factory.md",
    "60-ecosystem-synthesis.md",
}
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")

class BookRefusal(RuntimeError):
    pass

def refuse(msg: str) -> None:
    raise BookRefusal(msg)

def load_config() -> dict:
    with (ROOT / "book.toml").open("rb") as fh:
        cfg = tomllib.load(fh)
    if cfg.get("book", {}).get("src") != "docs":
        refuse("REFUSED:BOOK_SOURCE_NOT_DOCS")
    if cfg.get("output", {}).get("html", {}).get("site-url") != "/chatman-ecosystem/":
        refuse("REFUSED:PAGES_SITE_URL_DRIFT")
    if cfg.get("build", {}).get("create-missing") is not False:
        refuse("REFUSED:BOOK_MISSING_CHAPTERS_NOT_FAIL_CLOSED")
    return cfg

def summary_links() -> list[str]:
    text = SUMMARY.read_text(encoding="utf-8")
    links = LINK_RE.findall(text)
    if len(links) != len(set(links)):
        refuse("REFUSED:DUPLICATE_SUMMARY_CHAPTER")
    return links

def verify_links(links: list[str]) -> None:
    for rel in links:
        p = (DOCS / rel).resolve()
        try:
            p.relative_to(DOCS.resolve())
        except ValueError:
            refuse(f"REFUSED:SUMMARY_ESCAPES_BOOK_SOURCE:{rel}")
        if not p.is_file():
            refuse(f"REFUSED:MISSING_SUMMARY_TARGET:{rel}")

def verify_required_membership(links: list[str]) -> None:
    direct = [p for p in links if "/" not in p]
    for prefix in CANONICAL_50:
        matches = [p for p in direct if p.startswith(prefix)]
        if len(matches) != 1:
            refuse(f"REFUSED:CANONICAL_CHAPTER_CLOSURE:{prefix}:{len(matches)}")
    formal = [p.split("/", 1)[1] for p in links if p.startswith("v26.9.1/")]
    for prefix in FORMAL_50:
        matches = [p for p in formal if p.startswith(prefix)]
        if len(matches) != 1:
            refuse(f"REFUSED:FORMAL_CHAPTER_CLOSURE:{prefix}:{len(matches)}")
    missing_spine = sorted(READER_SPINE - set(links))
    if missing_spine:
        refuse("REFUSED:READER_SPINE_INCOMPLETE:" + ",".join(missing_spine))

def verify_intro_fence() -> None:
    intro = (DOCS / "README.md").read_text(encoding="utf-8")
    required = [
        "Not constitutional authority",
        "Generated is not authorized",
        "SELECT is not CONSTRUCT",
        "Where is the receipt",
    ]
    for marker in required:
        if marker not in intro:
            refuse(f"REFUSED:BOOK_AUTHORITY_FENCE_MISSING:{marker}")

def verify_local_markdown_links() -> None:
    for name in sorted(READER_SPINE):
        text = (DOCS / name).read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            target_path = ((DOCS / name).parent / target).resolve()
            try:
                target_path.relative_to(DOCS.resolve())
            except ValueError:
                continue
            if not target_path.exists():
                refuse(f"REFUSED:SPINE_LINK_TARGET_MISSING:{name}:{target}")

def main() -> int:
    try:
        load_config()
        links = summary_links()
        verify_links(links)
        verify_required_membership(links)
        verify_intro_fence()
        verify_local_markdown_links()
    except (BookRefusal, OSError, tomllib.TOMLDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"BOOK_STRUCTURAL_ALIVE chapters={len(links)} canonical=50 formal=50 reader_spine={len(READER_SPINE)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
