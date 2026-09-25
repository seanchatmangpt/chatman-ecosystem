from __future__ import annotations

import json
import sys

from .court import evaluate_path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 -m scripts.release_train.release_closure_court <closure.json>", file=sys.stderr)
        return 64
    verdict = evaluate_path(argv[1])
    print(json.dumps(verdict.receipt, indent=2, sort_keys=True))
    return 0 if verdict.standing in {"ALIVE", "PARTIAL_ALIVE"} else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
