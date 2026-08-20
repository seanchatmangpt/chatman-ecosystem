#!/usr/bin/env python3
"""Fail-closed non-vacuity court for the Dyson-sphere mdBook.

This court does not pretend to prove literary excellence. It does make structural
vacuity observable and merge-blocking: every book page must be linked, substantive,
subject-specific, domain-grounded, falsifiable, and free of the generator's legacy
label-only boilerplate.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import statistics
from pathlib import Path

import enrich_dyson_sphere_book as enrich

REQUIRED = (
    "## Why this page exists",
    "## Engineering model",
    "## Operational contract",
    "## Worked reasoning",
    "## Questions the design must answer",
    "## Executable representation",
    "## Failure modes and counterexamples",
    "## DfCM decision rule",
    "## Admission and authority boundary",
    "## Admission test",
    "## Downstream consequence",
    "## Epistemic boundary",
)
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|TKTK|lorem ipsum|insert (?:text|content)|replace me|coming soon)\b", re.I)
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+*'-]*")
CODE_FENCE = re.compile(r"```.*?```", re.S)
LINK = re.compile(r"\[[^\]]+\]\(([^)#]+\.md)(?:#[^)]+)?\)")


def words(text: str) -> list[str]:
    return WORD.findall(CODE_FENCE.sub(" ", text))


def paragraphs(text: str) -> list[str]:
    clean = CODE_FENCE.sub("", text)
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", clean) if len(re.sub(r"\s+", " ", p).strip()) >= 120]


def title_tokens(title: str) -> set[str]:
    return {w.lower() for w in WORD.findall(title) if len(w) > 2 and w.lower() not in enrich.STOP}


def normalize_body(text: str) -> str:
    # Titles/subject IDs remain intentionally significant: two pages with identical bodies
    # after those are removed would indicate a generated clone.
    return re.sub(r"\s+", " ", text).strip()


def audit(root: Path) -> dict[str, object]:
    pages, summary = enrich.parse_summary(root)
    linked = [p.rel for p in pages]
    unique_linked = list(dict.fromkeys(linked))
    all_md = sorted(str(p.relative_to(root)).replace("\\", "/") for p in root.rglob("*.md") if p.name != "SUMMARY.md")
    findings: list[dict[str, object]] = []

    if len(linked) != len(unique_linked):
        dup = [x for x, n in collections.Counter(linked).items() if n > 1]
        findings.append({"code": "SUMMARY_DUPLICATE_LINK", "subjects": dup})

    repeated_parts = [h for h, n in collections.Counter(line for line in summary.splitlines() if line.startswith("# Part ") or line == "# Appendices").items() if n > 1]
    if repeated_parts:
        findings.append({"code": "SUMMARY_REPEATED_SECTION_HEADING", "subjects": repeated_parts})

    missing = [rel for rel in unique_linked if not (root / rel).exists()]
    if missing:
        findings.append({"code": "SUMMARY_TARGET_MISSING", "subjects": missing})

    orphan = sorted(set(all_md) - set(unique_linked))
    if orphan:
        findings.append({"code": "BOOK_MARKDOWN_ORPHAN", "subjects": orphan})

    counts: dict[str, int] = {}
    domains: collections.Counter[str] = collections.Counter()
    hashes: dict[str, list[str]] = collections.defaultdict(list)
    para_owners: dict[str, list[str]] = collections.defaultdict(list)
    internal_broken: list[tuple[str, str]] = []

    for page in pages:
        if not page.path.exists():
            continue
        text = page.path.read_text(encoding="utf-8")
        wc = len(words(text))
        counts[page.rel] = wc
        body_hash = hashlib.sha256(normalize_body(text).encode()).hexdigest()
        hashes[body_hash].append(page.rel)

        if page.rel == "README.md":
            if wc < 700:
                findings.append({"code": "README_TOO_THIN", "subject": page.rel, "words": wc, "minimum": 700})
            if "HYPER_MEANINGFUL_PAGE_CONTRACT_V1" not in text:
                findings.append({"code": "README_MEANING_CONTRACT_MISSING", "subject": page.rel})
        else:
            domain = enrich.classify(page.title, page.parent_title or "", page.part)
            domains[domain] += 1
            minimum = 560 if page.depth >= 2 else 650
            if wc < minimum:
                findings.append({"code": "PAGE_TOO_THIN", "subject": page.rel, "words": wc, "minimum": minimum})
            for heading in REQUIRED:
                if heading not in text:
                    findings.append({"code": "MEANING_SECTION_MISSING", "subject": page.rel, "section": heading})
            # The exact title must materially participate in the page; this catches a
            # renderer that emits a generic domain essay under many filenames.
            title_occurrences = text.lower().count(page.title.lower())
            if title_occurrences < 6:
                findings.append({"code": "SUBJECT_SPECIFICITY_WEAK", "subject": page.rel, "title_occurrences": title_occurrences})
            vocab = enrich.VOCAB[domain]
            vocab_hits = sum(1 for term in vocab if term.lower() in text.lower())
            if vocab_hits < 4:
                findings.append({"code": "DOMAIN_GROUNDING_WEAK", "subject": page.rel, "domain": domain, "vocab_hits": vocab_hits})
            if f"**Domain:** `{domain}`" not in text:
                findings.append({"code": "DOMAIN_IDENTITY_MISSING", "subject": page.rel, "domain": domain})
            if "**Subject identity:** `dyson:" not in text:
                findings.append({"code": "EXACT_SUBJECT_ID_MISSING", "subject": page.rel})
            if "**not evidence that a physical Dyson system exists.**" not in text:
                findings.append({"code": "EPISTEMIC_SCOPE_MISSING", "subject": page.rel})

        for phrase in enrich.LEGACY_VACUITY:
            if phrase.lower() in text.lower():
                findings.append({"code": "LEGACY_VACUITY_PRESENT", "subject": page.rel, "phrase": phrase})
        if PLACEHOLDER.search(text):
            findings.append({"code": "PLACEHOLDER_LANGUAGE", "subject": page.rel, "match": PLACEHOLDER.search(text).group(0)})

        for para in paragraphs(text):
            # Deliberate constitutional equations/checklists can repeat; prose should not.
            if "OBSERVED -> ADMITTED" in para or "SELECT" in para and "CONSTRUCT" in para and "DO" in para:
                continue
            para_owners[hashlib.sha256(para.encode()).hexdigest()].append(page.rel)

        for target in LINK.findall(text):
            # Ignore paths outside the book root; rendered pages are expected to link only
            # to book peers, but this remains safe for future references.
            resolved = (page.path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                continue
            if not resolved.exists():
                internal_broken.append((page.rel, target))

    clone_groups = [owners for owners in hashes.values() if len(owners) > 1]
    if clone_groups:
        findings.append({"code": "DUPLICATE_PAGE_BODY", "groups": clone_groups[:20], "group_count": len(clone_groups)})

    repeated_paras = sorted((owners for owners in para_owners.values() if len(owners) >= 12), key=len, reverse=True)
    if repeated_paras:
        findings.append({"code": "BOILERPLATE_PARAGRAPH_FANOUT", "groups": repeated_paras[:20], "group_count": len(repeated_paras), "threshold": 12})

    if internal_broken:
        findings.append({"code": "BROKEN_INTERNAL_MD_LINK", "subjects": internal_broken[:100], "count": len(internal_broken)})

    ordered_counts = sorted(counts.values())
    result: dict[str, object] = {
        "schema": "urn:chatman:dyson:vacuity-audit:v1",
        "standing": "ALIVE" if not findings else "BUILD_BROKEN",
        "summary_linked_pages": len(linked),
        "unique_linked_pages": len(unique_linked),
        "book_markdown_pages_excluding_summary": len(all_md),
        "minimum_words": min(ordered_counts) if ordered_counts else 0,
        "median_words": statistics.median(ordered_counts) if ordered_counts else 0,
        "maximum_words": max(ordered_counts) if ordered_counts else 0,
        "domains": dict(sorted(domains.items())),
        "unique_page_bodies": len(hashes),
        "finding_count": len(findings),
        "findings": findings,
        "definition_of_non_vacuous": {
            "all_summary_targets_exist": not missing,
            "no_orphan_markdown_pages": not orphan,
            "summary_sections_not_repeated": not repeated_parts,
            "legacy_label_only_boilerplate_absent": not any(f["code"] == "LEGACY_VACUITY_PRESENT" for f in findings),
            "every_non_root_page_has_required_sections": not any(f["code"] == "MEANING_SECTION_MISSING" for f in findings),
            "every_non_root_page_is_subject_specific": not any(f["code"] == "SUBJECT_SPECIFICITY_WEAK" for f in findings),
            "every_non_root_page_is_domain_grounded": not any(f["code"] == "DOMAIN_GROUNDING_WEAK" for f in findings),
            "all_page_bodies_unique": not clone_groups,
            "no_high_fanout_boilerplate_paragraphs": not repeated_paras,
            "internal_markdown_links_resolve": not internal_broken,
        },
    }
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("docs/how-to-build-a-dyson-sphere"))
    p.add_argument("--report", type=Path, default=Path("artifacts/dyson-vacuity-audit.json"))
    p.add_argument("--write-report", action="store_true")
    a = p.parse_args(argv)
    result = audit(a.root.resolve())
    if a.write_report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["standing"] == "ALIVE" else 2

if __name__ == "__main__":
    raise SystemExit(main())
