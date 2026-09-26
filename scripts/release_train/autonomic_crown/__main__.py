"""CLI: evaluate the autonomic crown (RFC-0005) and write its receipt.

Exit 0 AUTONOMIC with execution ALIVE; 3 typed NOT_AUTONOMIC (lawful, the loop
continues); 2 REFUSED (the court refused its own inputs, an illegal standing, or a
``--check`` drift). Read-only: no network; git objects are read from the root
repository's object database (``--repos-root``, else ``DURABLE_LOCATOR_REPOS_ROOT``,
else the checkout at ``--root`` when it is a git work tree).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from dataclasses import replace

from .court import INPUT_NAMES, _json, _read, evaluate, load_inputs
from .faults import attempt_input_digest
from .model import digest, pretty
from .receipt import build, exit_code, seal


def _repos_root(arg: str | None, root: Path) -> tuple[Path | None, str | None]:
    if arg:
        return Path(arg), None
    env = os.environ.get("DURABLE_LOCATOR_REPOS_ROOT")
    if env:
        return Path(env), None
    if (root / ".git").exists():
        tmp = tempfile.mkdtemp(prefix="autonomic-crown-repos-")
        os.symlink(root.resolve(), Path(tmp) / "chatman-ecosystem")
        return Path(tmp), tmp
    return None, None


def observed_time(inputs: object) -> str | None:
    """``evaluated_at`` is the consumed observation time (deterministic), never the wall clock."""
    data, _, _ = _read(inputs, "observations", None)  # type: ignore[arg-type]
    doc = _json(data)
    return doc.get("observed_at") if isinstance(doc, dict) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="autonomic_crown")
    parser.add_argument("--release", default="v26.9.25")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--repos-root")
    for name in INPUT_NAMES:
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, help=f"{name} from a file instead of its locator")
    parser.add_argument("--governance", type=Path)
    parser.add_argument(
        "--rebind-subject",
        action="store_true",
        help="RFC-0005 §8 SUBJECT_FAILURE (R): re-bind the inventory to this receipt's crown subject and re-evaluate",
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", type=Path, help="recompute and refuse any byte difference with this receipt")
    args = parser.parse_args(argv)
    repos_root, tmp = _repos_root(args.repos_root, args.root)
    try:
        overrides = {n: getattr(args, n).read_bytes() for n in INPUT_NAMES if getattr(args, n) is not None}
        governance = None
        if args.governance is not None and args.governance.is_file():
            governance = json.loads(args.governance.read_text(encoding="utf-8"))
        inputs = load_inputs(args.root, args.release, repos_root, overrides, governance)
        ev = evaluate(inputs)
        repairs = []
        if args.rebind_subject and "SUBJECT_SPLIT" in ev.codes and ev.crown_receipt:
            before = attempt_input_digest(inputs)
            inputs = replace(
                inputs,
                edges_doc={**inputs.edges_doc, "crown_subject": ev.crown_receipt["crown_sha"]},
                hypothesis="crown-sha split; re-bind to the current crown subject",
            )
            after = attempt_input_digest(inputs)
            if after == before:
                print("REFUSED:UNCHANGED_RETRY:rebind-subject", file=sys.stderr)
                return 2
            repairs.append({"code": "SUBJECT_SPLIT", "hypothesis": inputs.hypothesis, "attempt_input_digest": after})
            ev = evaluate(inputs)
        observed_at = observed_time(inputs)
        body = build(
            ev,
            args.release,
            digest(inputs.edges_doc),
            digest(inputs.gates_doc),
            digest(governance) if governance else None,
        )
        if repairs:
            body["repairs"] = repairs
        receipt = seal(body, observed_at)
        data = pretty(receipt)
        code = exit_code(ev)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_bytes(data)
        summary = {
            "standings": receipt["standings"],
            "blocked_gates": receipt["blocked_gates"],
            "passed_gates": receipt["passed_gates"],
            "refusals": [
                f"{f['severity']}:{f['code']}:{f['subject']}" for f in receipt["findings"] if f["severity"] == "REFUSED"
            ],
            "receipt_digest": receipt["receipt_digest"],
            "exit": code,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        if args.check is not None:
            if not args.check.is_file() or args.check.read_bytes() != data:
                print(f"REFUSED:AUTONOMIC_RECEIPT_DRIFT:{args.check}", file=sys.stderr)
                return 2
            print(f"AUTONOMIC_RECEIPT_CURRENT:{args.check}")
        return code
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
