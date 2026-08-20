#!/usr/bin/env python3
"""Audit the tracked documentation corpus for vacuous pages.

The audit is intentionally deterministic and conservative. It does not claim
that a long page is meaningful; it identifies mechanically falsifiable forms
of documentation vacuity so reviewers can focus semantic review on a bounded
set of candidates.

Scope:
  * every tracked Markdown file under docs/ and books/;
  * every local Markdown edge in every SUMMARY.md under those roots.

A page is flagged when one or more of these conditions holds:
  * empty or heading-only content;
  * unresolved SUMMARY.md target;
  * explicit placeholder/stub language;
  * fewer than the minimum substantive words;
  * too few explanatory paragraphs/sections for a normal page;
  * exact normalized-body duplication with another page.

SUMMARY.md files are navigation manifests, not prose chapters, so they are
checked for link closure but excluded from prose-density thresholds.

Usage:
    python3 scripts/audit_doc_vacuity.py
    python3 scripts/audit_doc_vacuity.py --report-only
    python3 scripts/audit_doc_vacuity.py --json /tmp/vacuity.json

Exit status is non-zero when findings exist unless --report-only is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("docs/", "books/")
SUMMARY_NAME = "SUMMARY.md"

# Normal prose pages smaller than this are almost always skeletal in this
# corpus. The threshold is deliberately lower than the project's substantial
# chapters so it catches vacuity without prescribing chapter length.
MIN_WORDS = 220
MIN_PARAGRAPHS = 3
MIN_SECTIONS = 2

PLACEHOLDER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("todo", re.compile(r"\bTODO\b", re.IGNORECASE)),
    ("tbd", re.compile(r"\bTBD\b", re.IGNORECASE)),
    ("fixme", re.compile(r"\bFIXME\b", re.IGNORECASE)),
    ("wip", re.compile(r"\bWIP\b", re.IGNORECASE)),
    ("placeholder", re.compile(r"\bplaceholder\b", re.IGNORECASE)),
    ("coming-soon", re.compile(r"\bcoming\s+soon\b", re.IGNORECASE)),
    ("lorem-ipsum", re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE)),
    ("draft-chapter", re.compile(r"\bdraft\s+chapter\b", re.IGNORECASE)),
    ("to-be-written", re.compile(r"\b(to\s+be\s+(written|completed|filled)|write\s+this\s+section)\b", re.IGNORECASE)),
    ("template-instruction", re.compile(r"\b(insert|add)\s+(text|content|description|details|example|gif|link)\b", re.IGNORECASE)),
    ("brief-description-template", re.compile(r"\ba\s+brief\s+description\s+of\b", re.IGNORECASE)),
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+./:'’-]*")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
LINK_TARGET_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
MARKDOWN_MARKUP_RE = re.compile(r"[`*_>#|~]+")

# Short special-purpose pages still need enough explanatory prose, but their
# semantics do not naturally require multiple chapter-style sections.
SPECIAL_SINGLE_SECTION = {"404.md"}


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    detail: str


@dataclass(frozen=True)
class PageMetrics:
    path: str
    bytes: int
    words: int
    paragraphs: int
    sections: int
    placeholder_markers: tuple[str, ...]
    normalized_digest: str


def tracked_markdown() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths: list[Path] = []
    for raw in output.splitlines():
        rel = raw.strip()
        if not rel or not rel.startswith(SCAN_ROOTS):
            continue
        paths.append(Path(rel))
    return sorted(paths)


def strip_non_prose(text: str) -> str:
    text = HTML_COMMENT_RE.sub(" ", text)
    text = FENCE_RE.sub(" ", text)
    text = LINK_TARGET_RE.sub(r"\1", text)
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("#"):
            continue
        # Table separator rows and pure navigation bullets do not count as
        # explanatory prose, though prose inside ordinary bullets still does.
        if re.fullmatch(r"[|:\- ]+", stripped):
            continue
        lines.append(MARKDOWN_MARKUP_RE.sub(" ", line))
    return "\n".join(lines)


def paragraph_count(prose: str) -> int:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", prose) if b.strip()]
    count = 0
    for block in blocks:
        words = WORD_RE.findall(block)
        # A paragraph must contain an explanatory clause, not a label.
        if len(words) >= 12:
            count += 1
    return count


def normalized_body(text: str) -> str:
    prose = strip_non_prose(text).lower()
    words = WORD_RE.findall(prose)
    return " ".join(words)


def metrics(path: Path) -> PageMetrics:
    text = (ROOT / path).read_text(encoding="utf-8")
    prose = strip_non_prose(text)
    words = WORD_RE.findall(prose)
    sections = sum(1 for match in HEADING_RE.finditer(text) if len(match.group(1)) >= 2)
    markers = tuple(name for name, pattern in PLACEHOLDER_PATTERNS if pattern.search(text))
    normalized = normalized_body(text)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return PageMetrics(
        path=path.as_posix(),
        bytes=len(text.encode("utf-8")),
        words=len(words),
        paragraphs=paragraph_count(prose),
        sections=sections,
        placeholder_markers=markers,
        normalized_digest=digest,
    )


def summary_targets(summary: Path) -> Iterable[tuple[str, Path]]:
    text = (ROOT / summary).read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().split("#", 1)[0].strip()
        if not target:
            continue
        if target.startswith(("http://", "https://", "mailto:", "javascript:")):
            continue
        # mdBook accepts angle-bracket destinations; normalize them.
        target = target.strip("<>")
        if not target.lower().endswith(".md"):
            continue
        resolved = (summary.parent / target)
        # lexical normalization without requiring target existence
        parts: list[str] = []
        for part in resolved.parts:
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        yield raw_target, Path(*parts)


def audit() -> tuple[list[PageMetrics], list[Finding], dict[str, int]]:
    pages = tracked_markdown()
    page_set = {p.as_posix() for p in pages}
    summaries = [p for p in pages if p.name == SUMMARY_NAME]
    prose_pages = [p for p in pages if p.name != SUMMARY_NAME]

    page_metrics = [metrics(p) for p in prose_pages]
    findings: list[Finding] = []

    # Navigation closure: every local Markdown edge from every SUMMARY exists.
    linked_pages: set[str] = set()
    link_edges = 0
    for summary in summaries:
        for raw, target in summary_targets(summary):
            link_edges += 1
            target_s = target.as_posix()
            linked_pages.add(target_s)
            if target_s not in page_set or not (ROOT / target).is_file():
                findings.append(
                    Finding(
                        "BROKEN_SUMMARY_LINK",
                        summary.as_posix(),
                        f"{raw!r} resolves to missing {target_s!r}",
                    )
                )

    # Page-level vacuity checks.
    for item in page_metrics:
        path = Path(item.path)
        if item.words == 0:
            findings.append(Finding("EMPTY_OR_HEADING_ONLY", item.path, "0 substantive words"))
            continue
        if item.placeholder_markers:
            findings.append(
                Finding(
                    "PLACEHOLDER_MARKER",
                    item.path,
                    ", ".join(item.placeholder_markers),
                )
            )
        if item.words < MIN_WORDS:
            findings.append(
                Finding(
                    "TOO_SHORT",
                    item.path,
                    f"{item.words} substantive words; minimum {MIN_WORDS}",
                )
            )
        if path.name not in SPECIAL_SINGLE_SECTION:
            if item.paragraphs < MIN_PARAGRAPHS:
                findings.append(
                    Finding(
                        "THIN_EXPLANATION",
                        item.path,
                        f"{item.paragraphs} explanatory paragraphs; minimum {MIN_PARAGRAPHS}",
                    )
                )
            if item.sections < MIN_SECTIONS:
                findings.append(
                    Finding(
                        "THIN_STRUCTURE",
                        item.path,
                        f"{item.sections} level-2+ sections; minimum {MIN_SECTIONS}",
                    )
                )

    # Exact normalized-body duplication catches copy/paste template chapters.
    by_digest: dict[str, list[PageMetrics]] = defaultdict(list)
    for item in page_metrics:
        if item.words >= MIN_WORDS:
            by_digest[item.normalized_digest].append(item)
    for group in by_digest.values():
        if len(group) <= 1:
            continue
        paths = sorted(item.path for item in group)
        joined = ", ".join(paths)
        for path in paths:
            findings.append(Finding("DUPLICATE_BODY", path, joined))

    findings.sort(key=lambda f: (f.path, f.code, f.detail))
    stats = {
        "tracked_markdown": len(pages),
        "summary_files": len(summaries),
        "prose_pages": len(prose_pages),
        "summary_local_markdown_edges": link_edges,
        "summary_unique_targets": len(linked_pages),
        "findings": len(findings),
        "pages_with_findings": len({f.path for f in findings}),
    }
    return page_metrics, findings, stats


def render(metrics_rows: list[PageMetrics], findings: list[Finding], stats: dict[str, int]) -> str:
    lines = [
        "# Documentation Vacuity Audit",
        "",
        "## Corpus",
        "",
    ]
    for key, value in stats.items():
        lines.append(f"- `{key}`: **{value}**")
    lines += ["", "## Findings", ""]
    if not findings:
        lines.append("No mechanically vacuous documentation pages were found.")
    else:
        by_path: dict[str, list[Finding]] = defaultdict(list)
        for finding in findings:
            by_path[finding.path].append(finding)
        metric_lookup = {row.path: row for row in metrics_rows}
        for path in sorted(by_path):
            metric = metric_lookup.get(path)
            if metric:
                lines.append(
                    f"### `{path}` — {metric.words} words, {metric.paragraphs} paragraphs, "
                    f"{metric.sections} sections"
                )
            else:
                lines.append(f"### `{path}`")
            lines.append("")
            for finding in by_path[path]:
                lines.append(f"- **{finding.code}** — {finding.detail}")
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-only", action="store_true", help="report findings without failing")
    parser.add_argument("--json", type=Path, help="write machine-readable audit result")
    args = parser.parse_args()

    metrics_rows, findings, stats = audit()
    report = render(metrics_rows, findings, stats)
    print(report)

    if args.json:
        payload = {
            "stats": stats,
            "findings": [asdict(f) for f in findings],
            "pages": [asdict(m) for m in metrics_rows],
        }
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if findings and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
