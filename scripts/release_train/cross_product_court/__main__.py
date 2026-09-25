from __future__ import annotations

import argparse
import json
from typing import Any

from .io import load_case, receipt_dict

_INADMISSIBLE_SCHEMA = (
    "https://chatman.dev/cross-product-court/inadmissible-case/v1"
)


def run(path: str) -> tuple[dict[str, Any], int]:
    """Evaluate a case file; an inadmissible case is a typed refusal.

    Model constructors raise ValueError (authority smuggling, malformed
    identity, bad digest shape); a missing field raises KeyError. Both are
    refusals of the case itself, never a crash and never a standing.
    """
    try:
        case = load_case(path)
    except (ValueError, KeyError, TypeError) as exc:
        message = str(exc).replace("\n", " ").strip() or type(exc).__name__
        if isinstance(exc, KeyError):
            message = f"missing field {message}"
        return (
            {
                "schema": _INADMISSIBLE_SCHEMA,
                "standing": "REFUSED",
                "authority": "NONE",
                "refusals": [f"REFUSED:INADMISSIBLE_CASE:{message}"],
            },
            2,
        )
    data = receipt_dict(case)
    return data, 0 if data["standing"] == "ALIVE" else 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a Chatman Ecosystem cross-product evidence case"
    )
    parser.add_argument("case", help="path to cross-product case JSON")
    args = parser.parse_args()
    data, code = run(args.case)
    print(json.dumps(data, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
