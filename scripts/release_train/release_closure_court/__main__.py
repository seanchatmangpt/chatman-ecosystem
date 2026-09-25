from __future__ import annotations

import json
import sys

from .court import evaluate_path

USAGE = "usage: python3 -m scripts.release_train.release_closure_court <closure.json> [--evidence-root <dir>]"


def main(argv: list[str]) -> int:
    args = argv[1:]
    evidence_root = None
    if "--evidence-root" in args:
        i = args.index("--evidence-root")
        if i + 1 >= len(args):
            print(USAGE, file=sys.stderr)
            return 64
        evidence_root = args[i + 1]
        del args[i : i + 2]
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        return 64
    verdict = evaluate_path(args[0], evidence_root)
    print(json.dumps(verdict.receipt, indent=2, sort_keys=True))
    return 0 if verdict.standing in {"ALIVE", "PARTIAL_ALIVE"} else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
