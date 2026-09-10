#!/usr/bin/env python3
"""Audit every published Markdown page for mechanically demonstrable vacuity.

The goal is not to equate length with meaning. A concise schema, equation sheet,
SHACL shape, table, or worked command can carry more semantic density than a
long paragraph. This verifier therefore audits the publication graph first and
then measures both prose and structured knowledge.

Strict page corpus:
  * every existing local Markdown target from every tracked SUMMARY.md under
    docs/ and books/;
  * mdBook's special docs/404.md page when present.

All tracked Markdown remains counted so hidden support/audit/manufacturing files
cannot be confused with user-facing pages. SUMMARY.md itself is navigation and
is checked for edge closure rather than prose density.

A published page is mechanically vacuous when one or more of these hold:
  * the SUMMARY edge points at a missing file;
  * the page is empty/heading-only;
  * it contains an explicit unfinished marker such as a standalone TODO/TBD;
  * combined prose + code + tables + lists + sections falls below a conservative
    semantic-density floor;
  * its normalized semantic body is an exact duplicate of another published
    page, indicating copy/paste template material.

The verifier deliberately does *not* flag a page merely because it discusses
"WIP", "TODO", or "placeholder" as a concept. Historical audits and chapters
about work-in-process are therefore not rewritten to make the checker green.

Usage:
    python3 scripts/audit_doc_vacuity.py
    python3 scripts/audit_doc_vacuity.py --report-only
    python3 scripts/audit_doc_vacuity.py --json /tmp/vacuity.json
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
MIN_SEMANTIC_SCORE = 220
MIN_PROSE_WORDS_WITHOUT_STRUCTURE = 120

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+./:'’-]*")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
LINK_TARGET_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
MARKDOWN_MARKUP_RE = re.compile(r"[`*_>#|~]+")
LIST_RE = re.compile(r"^\s*(?:[-*+] |\d+[.)] )\S", re.MULTILINE)
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}")

# These patterns represent unfinished *states*, not ordinary occurrences of
# the same words in explanatory prose.
UNFINISHED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "standalone-work-marker",
        re.compile(
            r"(?im)^\s*(?:[-*+]\s+)?(?:status\s*:\s*)?"
            r"(?:TODO|TBD|FIXME|COMING\s+SOON|PLACEHOLDER(?:\s+TEXT)?)"
            r"(?:\s*[:.!-].*)?$"
        ),
    ),
    (
        "template-instruction",
        re.compile(
            r"(?im)^\s*(?:insert|add)\s+"
            r"(?:text|content|description|details|example|gif|link)\b.*$"
        ),
    ),
    (
        "lorem-ipsum",
        re.compile(r"\blorem\s+ipsum\b", re.IGNORECASE),
    ),
    (
        "to-be-written",
        re.compile(
            r"\b(?:to\s+be\s+(?:written|completed|filled)|write\s+this\s+section)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "brief-description-template",
        re.compile(r"\ba\s+brief\s+description\s+of\s+what\s+this\b", re.IGNORECASE),
    ),
)


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    detail: str


@dataclass(frozen=True)
class PageMetrics:
    path: str
    bytes: int
    prose_words: int
    paragraphs: int
    sections: int
    code_lines: int
    table_rows: int
    list_items: int
    semantic_score: int
    unfinished_markers: tuple[str, ...]
    normalized_digest: str


def tracked_markdown() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return sorted(
        Path(rel)
        for raw in output.splitlines()
        if (rel := raw.strip()) and rel.startswith(SCAN_ROOTS)
    )


def split_fenced_code(text: str) -> tuple[str, int]:
    """Return text with fenced code removed and count non-empty code lines."""
    prose_lines: list[str] = []
    code_lines = 0
    in_fence = False
    fence_char = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_char = marker
            elif marker == fence_char:
                in_fence = False
                fence_char = ""
            continue
        if in_fence:
            if stripped:
                code_lines += 1
        else:
            prose_lines.append(line)
    return "\n".join(prose_lines), code_lines


def strip_non_prose(text: str) -> str:
    text = HTML_COMMENT_RE.sub(" ", text)
    text, _ = split_fenced_code(text)
    text = LINK_TARGET_RE.sub(r"\1", text)
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("#"):
            continue
        if TABLE_SEPARATOR_RE.match(stripped):
            continue
        lines.append(MARKDOWN_MARKUP_RE.sub(" ", line))
    return "\n".join(lines)


def paragraph_count(prose: str) -> int:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", prose) if b.strip()]
    return sum(1 for block in blocks if len(WORD_RE.findall(block)) >= 12)


def table_row_count(text_without_code: str) -> int:
    count = 0
    for line in text_without_code.splitlines():
        stripped = line.strip()
        if stripped.count("|") < 2 or TABLE_SEPARATOR_RE.match(stripped):
            continue
        count += 1
    return count


def normalized_semantic_body(text: str) -> str:
    """Normalize full semantic body while ignoring headings/titles/markup."""
    text = HTML_COMMENT_RE.sub(" ", text).lower()
    kept: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        kept.append(line)
    return " ".join(WORD_RE.findall("\n".join(kept)))


def metrics(path: Path) -> PageMetrics:
    text = (ROOT / path).read_text(encoding="utf-8")
    without_code, code_lines = split_fenced_code(HTML_COMMENT_RE.sub(" ", text))
    prose = strip_non_prose(text)
    words = WORD_RE.findall(prose)
    sections = sum(1 for match in HEADING_RE.finditer(text) if len(match.group(1)) >= 2)
    table_rows = table_row_count(without_code)
    list_items = len(LIST_RE.findall(without_code))
    markers = tuple(name for name, pattern in UNFINISHED_PATTERNS if pattern.search(text))
    normalized = normalized_semantic_body(text)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    # Structured reference material counts as semantic content. Weights are
    # intentionally modest: a one-line list cannot cheaply inflate a stub,
    # while a real schema/table/equation-heavy appendix can clear the floor.
    semantic_score = (
        len(words)
        + 5 * code_lines
        + 5 * table_rows
        + 3 * list_items
        + 6 * sections
    )
    return PageMetrics(
        path=path.as_posix(),
        bytes=len(text.encode("utf-8")),
        prose_words=len(words),
        paragraphs=paragraph_count(prose),
        sections=sections,
        code_lines=code_lines,
        table_rows=table_rows,
        list_items=list_items,
        semantic_score=semantic_score,
        unfinished_markers=markers,
        normalized_digest=digest,
    )


def lexical_normalize(path: Path) -> Path:
    parts: list[str] = []
    for part in path.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return Path(*parts)


def summary_targets(summary: Path) -> Iterable[tuple[str, Path]]:
    text = (ROOT / summary).read_text(encoding="utf-8")
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().split("#", 1)[0].strip().strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:", "javascript:")):
            continue
        if not target.lower().endswith(".md"):
            continue
        yield raw_target, lexical_normalize(summary.parent / target)


def published_page_set(
    pages: list[Path], summaries: list[Path], findings: list[Finding]
) -> tuple[set[Path], int, int]:
    page_set = {p.as_posix() for p in pages}
    published: set[Path] = set()
    link_edges = 0
    unique_targets: set[str] = set()
    for summary in summaries:
        for raw, target in summary_targets(summary):
            link_edges += 1
            target_s = target.as_posix()
            unique_targets.add(target_s)
            if target_s not in page_set or not (ROOT / target).is_file():
                findings.append(
                    Finding(
                        "BROKEN_SUMMARY_LINK",
                        summary.as_posix(),
                        f"{raw!r} resolves to missing {target_s!r}",
                    )
                )
            else:
                published.add(target)

    special_404 = Path("docs/404.md")
    if (ROOT / special_404).is_file():
        published.add(special_404)
    return published, link_edges, len(unique_targets)


def audit() -> tuple[list[PageMetrics], list[Finding], dict[str, int]]:
    pages = tracked_markdown()
    summaries = [p for p in pages if p.name == SUMMARY_NAME]
    findings: list[Finding] = []
    published, link_edges, unique_targets = published_page_set(pages, summaries, findings)

    page_metrics = [metrics(p) for p in sorted(published) if p.name != SUMMARY_NAME]

    for item in page_metrics:
        if item.semantic_score == 0:
            findings.append(Finding("EMPTY_OR_HEADING_ONLY", item.path, "0 semantic score"))
            continue

        if item.unfinished_markers:
            findings.append(
                Finding(
                    "UNFINISHED_MARKER",
                    item.path,
                    ", ".join(item.unfinished_markers),
                )
            )

        if item.semantic_score < MIN_SEMANTIC_SCORE:
            findings.append(
                Finding(
                    "LOW_SEMANTIC_DENSITY",
                    item.path,
                    (
                        f"score={item.semantic_score} < {MIN_SEMANTIC_SCORE}; "
                        f"prose={item.prose_words}, code_lines={item.code_lines}, "
                        f"table_rows={item.table_rows}, list_items={item.list_items}, "
                        f"sections={item.sections}"
                    ),
                )
            )

        structured_units = item.code_lines + item.table_rows + item.list_items
        if structured_units < 8 and item.prose_words < MIN_PROSE_WORDS_WITHOUT_STRUCTURE:
            findings.append(
                Finding(
                    "THIN_UNSTRUCTURED_EXPLANATION",
                    item.path,
                    (
                        f"only {item.prose_words} prose words and {structured_units} "
                        "structured units"
                    ),
                )
            )

    # Exact semantic duplication is a strong signal and does not depend on
    # arbitrary length thresholds. Ignore truly tiny content already caught
    # by density so the report remains actionable.
    by_digest: dict[str, list[PageMetrics]] = defaultdict(list)
    for item in page_metrics:
        if item.semantic_score >= MIN_SEMANTIC_SCORE:
            by_digest[item.normalized_digest].append(item)
    for group in by_digest.values():
        if len(group) <= 1:
            continue
        paths = sorted(item.path for item in group)
        joined = ", ".join(paths)
        for path in paths:
            findings.append(Finding("DUPLICATE_SEMANTIC_BODY", path, joined))

    findings.sort(key=lambda f: (f.path, f.code, f.detail))
    stats = {
        "tracked_markdown": len(pages),
        "summary_files": len(summaries),
        "summary_local_markdown_edges": link_edges,
        "summary_unique_targets": unique_targets,
        "published_pages_audited": len(page_metrics),
        "unpublished_support_markdown": len(pages) - len(summaries) - len(page_metrics),
        "findings": len(findings),
        "pages_with_findings": len({f.path for f in findings}),
    }
    return page_metrics, findings, stats


def render(metrics_rows: list[PageMetrics], findings: list[Finding], stats: dict[str, int]) -> str:
    lines = ["# Documentation Vacuity Audit", "", "## Corpus", ""]
    for key, value in stats.items():
        lines.append(f"- `{key}`: **{value}**")
    lines += ["", "## Findings", ""]
    if not findings:
        lines.append("No mechanically vacuous published documentation pages were found.")
    else:
        by_path: dict[str, list[Finding]] = defaultdict(list)
        for finding in findings:
            by_path[finding.path].append(finding)
        metric_lookup = {row.path: row for row in metrics_rows}
        for path in sorted(by_path):
            metric = metric_lookup.get(path)
            if metric:
                lines.append(
                    f"### `{path}` — score {metric.semantic_score}; "
                    f"{metric.prose_words} prose words, {metric.code_lines} code lines, "
                    f"{metric.table_rows} table rows, {metric.list_items} list items"
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
    print(render(metrics_rows, findings, stats))

    if args.json:
        payload = {
            "stats": stats,
            "findings": [asdict(f) for f in findings],
            "pages": [asdict(m) for m in metrics_rows],
        }
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return 0 if args.report_only or not findings else 1


if __name__ == "__main__":
    sys.exit(main())
