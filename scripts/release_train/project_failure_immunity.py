#!/usr/bin/env python3
"""Generate consumer standing-failure immunity from the canonical court manifest."""
from __future__ import annotations
import argparse, json
from pathlib import Path

SCHEMA = "https://chatman.dev/standing-court/failure-immunity-consumer/v2"

def project(source, canonical_commit, consumer_subject, consumer_base_sha):
    rows = [r for r in source["failure_classes"] if r.get("inherit")]
    return {
        "GENERATED": "scripts/release_train/project_failure_immunity.py; do not hand-edit",
        "schema": SCHEMA,
        "canonical_owner": source["canonical_owner"],
        "canonical_source": source["inheritance"]["source"],
        "canonical_commit": canonical_commit,
        "consumer_subject": consumer_subject,
        "consumer_base_sha": consumer_base_sha,
        "inherited_failure_classes": [
            {"failure_class": r["id"], "canonical_guard": r["canonical_guard"], "generator": r["generator"]}
            for r in rows
        ],
        "inherited_guards": sorted({g for r in rows for g in r["canonical_guard"]}),
        "first_witness": source["inheritance"]["first_witness"],
        "metric": source["metric"],
        "bespoke_consumer_tests": False,
        "authority": "NONE",
    }

def dump(doc):
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--canonical-commit", required=True)
    p.add_argument("--consumer-subject", required=True)
    p.add_argument("--consumer-base-sha", required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--check", type=Path)
    a = p.parse_args()
    source = json.loads(a.source.read_text(encoding="utf-8"))
    rendered = dump(project(source, a.canonical_commit, a.consumer_subject, a.consumer_base_sha))
    if a.check:
        return 0 if a.check.read_text(encoding="utf-8") == rendered else 2
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
