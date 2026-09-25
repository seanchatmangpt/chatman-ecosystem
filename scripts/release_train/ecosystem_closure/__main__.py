"""Compile an ecosystem closure manifest.

Exit codes:
  0  manifest is well-formed and its declared standing does not overclaim
     (with --require-alive: additionally, the closure computes ALIVE)
  1  malformed manifest, overclaim, or replay mismatch
  2  --require-alive and the closure is not ALIVE
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

from .compiler import ClosureMalformed, compile_closure, verify_receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile a Chatman ecosystem closure manifest")
    parser.add_argument("manifest", help="path to release/vYY.M.D/closure.toml")
    parser.add_argument("--require-alive", action="store_true", help="refuse unless the closure computes ALIVE")
    parser.add_argument("--emit", help="write the closure receipt JSON to this path")
    parser.add_argument("--replay", help="recompile and require byte-identical agreement with this receipt")
    parser.add_argument("--summary", action="store_true", help="print a per-subject summary instead of the receipt")
    args = parser.parse_args(argv)

    raw = Path(args.manifest).read_bytes()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    try:
        receipt = compile_closure(tomllib.loads(raw.decode("utf-8")), digest)
    except (ClosureMalformed, tomllib.TOMLDecodeError) as exc:
        print(f"REFUSED:{exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.emit:
        Path(args.emit).write_text(rendered, encoding="utf-8")

    if args.summary:
        print(f"closure {receipt['version']} computed={receipt['computed_standing']} declared={receipt['declared_standing']}")
        for verdict in receipt["subjects"]:
            mark = "required" if verdict["required"] else "advisory"
            codes = sorted({item["code"] for item in verdict["findings"]})
            print(f"  {verdict['computed_standing']:<7} {mark:<8} {verdict['id']:<22} {verdict['sha'][:12]:<12} {','.join(codes)}")
        print("repair_order: " + " -> ".join(receipt["repair_order"]))
        for item in receipt["closure_findings"] + receipt["overclaims"]:
            print(f"  {item['code']} {item['subject']} {item['detail']}")
        print(f"receipt_digest: {receipt['receipt_digest']}")
    elif not args.emit:
        sys.stdout.write(rendered)

    if args.replay:
        prior = json.loads(Path(args.replay).read_text(encoding="utf-8"))
        if not verify_receipt(prior):
            print("REFUSED:CLOSURE_REPLAY_RECEIPT_TAMPERED", file=sys.stderr)
            return 1
        if prior != receipt:
            print("REFUSED:CLOSURE_REPLAY_DIVERGED", file=sys.stderr)
            return 1

    if receipt["overclaims"]:
        print("REFUSED:CLOSURE_STANDING_OVERCLAIM", file=sys.stderr)
        return 1
    if args.require_alive and receipt["computed_standing"] != "ALIVE":
        print(f"REFUSED:CLOSURE_NOT_ALIVE:{','.join(receipt['blocked_required']) or 'closure'}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
