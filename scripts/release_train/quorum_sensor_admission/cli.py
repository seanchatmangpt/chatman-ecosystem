from __future__ import annotations

import json
import sys

from .errors import Refused
from .subject import Subject


def main() -> int:
    try:
        request = json.load(sys.stdin)
        subject = Subject.parse(request["subject"])
        response = {"schema": "chatman.quorum-sensor-preflight/1", "subject": subject.canonical(), "actuation_performed": False}
        json.dump(response, sys.stdout, sort_keys=True, separators=(",", ":"))
        sys.stdout.write("\n")
        return 0
    except (KeyError, Refused, json.JSONDecodeError) as exc:
        json.dump({"standing": "REFUSED", "reason": str(exc)}, sys.stdout, sort_keys=True, separators=(",", ":"))
        sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
