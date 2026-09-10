#!/usr/bin/env python3
from pathlib import Path
import re, tomllib, sys
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
contract = tomllib.loads((ROOT / "book.contract.toml").read_text(encoding="utf-8"))
summary = (SRC / "SUMMARY.md").read_text(encoding="utf-8")
link_re = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")
targets = link_re.findall(summary)
if len(targets) != len(set(targets)):
    raise SystemExit(contract["refusals"]["duplicate_summary_target"])
missing = [t for t in targets if not (SRC / t).is_file()]
if missing:
    raise SystemExit(f"{contract['refusals']['missing_summary_target']}:{missing}")
chapter_targets = [t for t in targets if t.startswith("chapters/")]
appendix_targets = [t for t in targets if t.startswith("appendices/")]
if len(chapter_targets) != contract["chapter_count"] or len(appendix_targets) != contract["appendix_count"]:
    raise SystemExit(contract["refusals"]["count_drift"])
all_md = {p.relative_to(SRC).as_posix() for p in SRC.rglob("*.md")}
allowed = set(targets) | {"SUMMARY.md"}
orphans = sorted(all_md - allowed)
if orphans:
    raise SystemExit(f"{contract['refusals']['orphan_chapter']}:{orphans}")
corpus = "\n".join((SRC / t).read_text(encoding="utf-8") for t in targets)
if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b", corpus, flags=re.I):
    raise SystemExit(contract["refusals"]["placeholder"])
missing_concepts = [c for c in contract["doctrine"]["required_concepts"] if c not in corpus]
if missing_concepts:
    raise SystemExit(f"REFUSED:MISSING_DOCTRINE:{missing_concepts}")
for t in chapter_targets:
    text=(SRC/t).read_text(encoding='utf-8')
    if not text.startswith('# ') or '**Executive thesis:**' not in text or '## Diagnostic question' not in text:
        raise SystemExit(f"REFUSED:CHAPTER_SHAPE:{t}")
print(f"PASS chapters={len(chapter_targets)} appendices={len(appendix_targets)} targets={len(targets)} markdown={len(all_md)}")
