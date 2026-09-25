"""Deterministic projector for ``release/<v>/hardening/`` (stdlib only, no network).

Inputs (committed bytes, E1): raw git objects ``inputs/objects/<sha>.<type>.raw`` and
crown run receipts ``receipts/run-*/{crown-receipt,observations}.json``; the hardened
ceiling also reads ``inputs/delta-observations.json`` (observed subject->container deltas,
``observe_release_heads.py --post-tag-bindings``), never the exact replay.

Outputs (GENERATED, never hand-edited):
  TAG-SUBJECT.json     the tag object, its commit/tree, the subject path trees and the
                       tag-named crown receipt, all recomputed from the raw objects
  receipts/chain.json  committed receipts ordered by their hash links
  replay-receipt.json  exact replay of the tag-time crown from the materialized subject
                       (``--subject-tree``), plus the hardened re-evaluation ceiling

``--check`` re-projects and prints ``REFUSED:PROJECTION_DRIFT:<path>`` on any byte
difference (exit 2); ``--write`` rewrites the outputs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from . import chain, gitobj
from .model import digest

SCHEMA_TAG_SUBJECT = "https://chatman.dev/root-crown/hardening/tag-subject/v1"
SCHEMA_REPLAY = "https://chatman.dev/root-crown/hardening/replay/v1"
GENERATED = "scripts/release_train/root_crown/hardening.py -- do not edit; run --write"
TAG_SUBJECT = "TAG-SUBJECT.json"
REPLAY_RECEIPT = "replay-receipt.json"
OBJECTS = "inputs/objects"
# Top-level entries of the frozen payload that are post-tag additions (never tagged bytes).
POST_TAG_EXCLUDES = ("autonomy", "hardening")
_RECEIPT_IN_MESSAGE = re.compile(r"crown receipt (sha256:[0-9a-f]{64})")
_RUN_IN_MESSAGE = re.compile(r"approval run (\d+)")


class HardeningError(ValueError):
    pass


def subject_paths(release: str) -> tuple[str, ...]:
    """Paths of the tag commit materialized for replay (``git archive <commit> <paths>``)."""
    return ("release", "scripts", f"docs/jira/{release}")


def _dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def project_tag_subject(hardening_dir: Path, release: str, repository: str) -> dict[str, Any]:
    objects = gitobj.RawObjects(hardening_dir / OBJECTS)
    if objects.mismatches:
        raise HardeningError("TAG_OBJECT_DIGEST_MISMATCH:" + ",".join(objects.mismatches))
    tags = []
    for sha, (kind, body) in sorted(objects.bodies.items()):
        if kind == "tag":
            parsed = gitobj.parse_tag(body)
            if parsed["tag"] == release:
                tags.append((sha, parsed))
    if len(tags) != 1:
        raise HardeningError(f"TAG_UNRECORDED:{len(tags)} raw tag objects named {release}")
    tag_sha, tag = tags[0]
    if tag["type"] != "commit":
        raise HardeningError(f"TAG_SUBJECT_SPLIT:tag targets a {tag['type']}")
    commit_sha = tag["object"]
    commit = gitobj.parse_commit(objects.get(commit_sha, "commit"))
    paths = {}
    for path in subject_paths(release) + (f"release/{release}",):
        paths[path] = gitobj.tree_chain(objects, commit_sha, path)[-1][1]
    receipt_match = _RECEIPT_IN_MESSAGE.search(tag["message"])
    run_match = _RUN_IN_MESSAGE.search(tag["message"])
    receipt_digest = receipt_match.group(1) if receipt_match else None
    receipts = chain.committed_receipts(hardening_dir)
    if receipt_digest not in receipts:
        raise HardeningError(f"TAG_RECEIPT_SPLIT:tag names receipt {receipt_digest}, not committed")
    receipt_path, receipt = receipts[receipt_digest]
    run_dir = receipt_path.rsplit("/", 1)[0]
    observations_path = f"{run_dir}/observations.json"
    observations = json.loads((hardening_dir / observations_path).read_text(encoding="utf-8"))
    previous_digest = receipt.get("previous_receipt_digest")
    previous_path = receipts[previous_digest][0] if previous_digest in receipts else None
    return {
        "GENERATED": GENERATED,
        "schema": SCHEMA_TAG_SUBJECT,
        "release": release,
        "repository": repository,
        "tag": {
            "name": tag["tag"],
            "object_sha": tag_sha,
            "object_type": "tag",
            "target_sha": commit_sha,
            "target_type": tag["type"],
            "tagger": tag["tagger"],
            "message_receipt_digest": receipt_digest,
            "approval_run": run_match.group(1) if run_match else None,
        },
        "subject": {
            "commit_sha": commit_sha,
            "tree_sha": commit["tree"],
            "parents": commit["parents"],
            "paths": paths,
        },
        "payload": {
            "path": f"release/{release}",
            "tree_sha": paths[f"release/{release}"],
            "post_tag_excludes": list(POST_TAG_EXCLUDES),
        },
        "tag_receipt": {
            "path": receipt_path,
            "receipt_digest": receipt_digest,
            "standing": receipt.get("standing"),
            "crown_sha": receipt.get("crown_sha"),
            "observations_path": observations_path,
            "observations_digest": receipt.get("observations_digest"),
            "observations_recomputed_digest": digest(observations),
            "previous_path": previous_path,
            "previous_receipt_digest": previous_digest,
        },
        "raw_objects": {sha: f"{OBJECTS}/{sha}.{kind}.raw" for sha, (kind, _) in sorted(objects.bodies.items())},
    }


def project_replay(hardening_dir: Path, record: dict[str, Any], subject_dir: Path, root: Path) -> dict[str, Any]:
    from . import posttag

    historical = posttag.historical_standing(record, hardening_dir, subject_dir, root)
    return {
        "GENERATED": GENERATED,
        "schema": SCHEMA_REPLAY,
        "release": record["release"],
        "subject": posttag.subject_of(record),
        "historical": historical,
        "authority": "NONE",
    }


def outputs(hardening_dir: Path, release: str, repository: str, subject_dir: Path, root: Path) -> dict[str, bytes]:
    record = project_tag_subject(hardening_dir, release, repository)
    return {
        TAG_SUBJECT: _dump(record),
        chain.CHAIN_FILE: _dump(chain.project(hardening_dir, release)),
        REPLAY_RECEIPT: _dump(project_replay(hardening_dir, record, subject_dir, root)),
    }


def check(hardening_dir: Path, rendered: dict[str, bytes]) -> list[str]:
    drift = []
    for name, data in sorted(rendered.items()):
        path = hardening_dir / name
        if not path.is_file() or path.read_bytes() != data:
            drift.append(f"REFUSED:PROJECTION_DRIFT:{(hardening_dir / name).as_posix()}")
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m scripts.release_train.root_crown.hardening")
    parser.add_argument("--release", required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--subject-tree", type=Path, required=True, help="git archive of the tag commit")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    release_dir = args.root / "release" / args.release
    hardening_dir = release_dir / "hardening"
    pins = json.loads((release_dir / "pins.json").read_text(encoding="utf-8"))
    try:
        rendered = outputs(hardening_dir, args.release, pins["root_repository"], args.subject_tree, args.root)
    except (HardeningError, gitobj.GitObjectError, FileNotFoundError, KeyError) as exc:
        print(f"REFUSED:{exc}", file=sys.stderr)
        return 2
    if args.write:
        for name, data in rendered.items():
            (hardening_dir / name).parent.mkdir(parents=True, exist_ok=True)
            (hardening_dir / name).write_bytes(data)
        print(f"WROTE:{','.join(sorted(rendered))}")
        return 0
    drift = check(hardening_dir, rendered)
    for line in drift:
        print(line)
    if drift:
        return 2
    print(f"HARDENING_PROJECTION_CURRENT:{hardening_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
