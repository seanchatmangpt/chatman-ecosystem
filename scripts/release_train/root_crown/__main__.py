"""CLI: evaluate the root crown and write the receipt (+ tag decision).

Exit codes: 0 ALIVE, 3 typed BLOCKED (lawful, loop continues), 2 REFUSED / usage.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts import release_line  # type: ignore[attr-defined]

from .crown import evaluate
from .tag import tag_decision

EXIT = {"ALIVE": 0, "BLOCKED": 3, "REFUSED": 2}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m scripts.release_train.root_crown")
    parser.add_argument("--release", required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--previous", type=Path, help="previous crown receipt; absent file means genesis")
    parser.add_argument("--crown-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tag-decision", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        release_dir = args.root / release_line.release_dir(args.release)
    except release_line.ReleaseLineError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    observations = json.loads(args.observations.read_text(encoding="utf-8"))
    previous = None
    if args.previous is not None and args.previous.is_file():
        previous = json.loads(args.previous.read_text(encoding="utf-8"))
    verdict = evaluate(release_dir, observations, previous, args.crown_sha, root=args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict.receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tag = observations.get("tag") or {}
    decision = tag_decision(verdict.receipt, args.crown_sha, tag.get("sha"), tag.get("name") or args.release)
    if args.tag_decision is not None:
        args.tag_decision.parent.mkdir(parents=True, exist_ok=True)
        args.tag_decision.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "standing": verdict.standing,
        "terms": verdict.terms,
        "receipt_digest": verdict.receipt["receipt_digest"],
        "previous_receipt_digest": verdict.receipt["previous_receipt_digest"],
        "refusals": list(verdict.refusals),
        "remaining": [
            f"{r['id']}:{r['state']}:{r['code']}({r['failure_class']}/{r['broken_term']})" for r in verdict.remaining
        ],
        "tag_decision": decision["decision"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return EXIT[verdict.standing]


if __name__ == "__main__":
    raise SystemExit(main())
