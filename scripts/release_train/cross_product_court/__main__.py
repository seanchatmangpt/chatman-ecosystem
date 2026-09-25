from __future__ import annotations

import argparse
import json

from .io import load_case, receipt_dict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a Chatman Ecosystem cross-product evidence case"
    )
    parser.add_argument("case", help="path to cross-product case JSON")
    args = parser.parse_args()
    data = receipt_dict(load_case(args.case))
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0 if data["standing"] == "ALIVE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
