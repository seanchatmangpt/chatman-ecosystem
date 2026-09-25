"""CLI: evaluate the root crown and write the receipt (+ tag decision).

Exit codes: 0 ALIVE, 3 typed BLOCKED (lawful, loop continues), 2 REFUSED / usage.

``--mode auto`` (default) is PRE_TAG until ``release/<v>/hardening/TAG-SUBJECT.json``
records the tag, then POST_TAG. ``--head-sha`` is the checked-out HEAD the runner
actually has (``git rev-parse HEAD``); the tag decision compares it to the receipt's
crown SHA, so it must never default to the crown SHA itself. Absent files for
``--observations`` / ``--previous`` mean "not observed" / genesis.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts import release_line  # type: ignore[attr-defined]

from .crown import attest
from .tag import post_tag_decision, tag_decision

EXIT = {"ALIVE": 0, "BLOCKED": 3, "REFUSED": 2}


def _json(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m scripts.release_train.root_crown")
    parser.add_argument("--release", required=True)
    parser.add_argument("--observations", type=Path, required=True, help="absent file means not observed")
    parser.add_argument("--previous", type=Path, help="previous crown receipt (PRE_TAG); absent file means genesis")
    parser.add_argument("--crown-sha", required=True, help="the commit being evaluated")
    parser.add_argument("--head-sha", help="checked-out HEAD (git rev-parse HEAD); the tag decision binds to it")
    parser.add_argument("--mode", choices=("auto", "PRE_TAG", "POST_TAG"), default="auto")
    parser.add_argument("--subject-tree", type=Path, help="git archive of the tag commit (POST_TAG replay)")
    parser.add_argument("--hardening-dir", type=Path, help="default: <root>/release/<v>/hardening")
    parser.add_argument(
        "--tag-observation", type=Path, help="local tag observation JSON {name,sha,object_sha,object_type}"
    )
    parser.add_argument("--ancestry", type=Path, help="commits reachable from HEAD (git rev-list HEAD), one per line")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tag-decision", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        release_dir = args.root / release_line.release_dir(args.release)
    except release_line.ReleaseLineError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    observations = _json(args.observations)
    previous = _json(args.previous)
    ancestry = None
    if args.ancestry is not None and args.ancestry.is_file():
        ancestry = {line.strip() for line in args.ancestry.read_text(encoding="utf-8").splitlines() if line.strip()}
    verdict = attest(
        release_dir,
        observations,
        previous,
        args.crown_sha,
        root=args.root,
        requested_mode=args.mode,
        head_sha=args.head_sha,
        subject_dir=args.subject_tree,
        hardening_dir=args.hardening_dir,
        tag_observation=_json(args.tag_observation),
        ancestry=ancestry,
    )
    receipt = verdict.receipt
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tag = (observations or {}).get("tag") or {}
    if receipt["mode"] == "POST_TAG":
        decision = post_tag_decision(receipt, args.head_sha, tag.get("name") or args.release)
    else:
        decision = tag_decision(receipt, args.head_sha, tag.get("sha"), tag.get("name") or args.release)
    if args.tag_decision is not None:
        args.tag_decision.parent.mkdir(parents=True, exist_ok=True)
        args.tag_decision.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    historical = receipt.get("historical") or {}
    summary = {
        "mode": receipt["mode"],
        "standing": verdict.standing,
        "terms": verdict.terms,
        "receipt_digest": receipt["receipt_digest"],
        "previous_receipt_digest": receipt["previous_receipt_digest"],
        "refusals": list(verdict.refusals),
        "remaining": [
            f"{r['id']}:{r['state']}:{r['code']}({r['failure_class']}/{r['broken_term']})" for r in verdict.remaining
        ],
        "historical": {
            "standing": historical.get("standing"),
            "replay": historical.get("replay_standing"),
            "replayed_digest": (historical.get("replay") or {}).get("replayed_digest"),
            "standing_ceiling": historical.get("standing_ceiling"),
        }
        if historical
        else None,
        "current": receipt["current"]["standing"],
        "tag_decision": decision["decision"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return EXIT[verdict.standing]


if __name__ == "__main__":
    raise SystemExit(main())
