#!/usr/bin/env python3
"""Run one Mix/Igniter command and promote a pending intent to a receipt on success.

The ggen template materializes a pending intent before ``sh_after`` runs. This helper
owns the transition from that non-authoritative intent to a durable receipt. A child
failure can therefore never leave a newly manufactured success receipt behind.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def run_receipted_mix(
    pending: Path,
    receipt: Path,
    log: Path,
    command: Sequence[str],
) -> int:
    """Execute ``command`` once and atomically promote ``pending`` on success.

    Existing receipts are replay/idempotency guards: the child is not executed again.
    Failed children remove the pending intent so a subsequent generation may retry.
    """
    if not command:
        print("REFUSED[EMPTY_MIX_COMMAND]", file=sys.stderr)
        return 64

    if receipt.exists():
        pending.unlink(missing_ok=True)
        print(f"REPLAY[RECEIPT_EXISTS] {receipt}")
        return 0

    if not pending.is_file():
        print(f"REFUSED[PENDING_INTENT_MISSING] {pending}", file=sys.stderr)
        return 65

    receipt.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)

    try:
        with log.open("a", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                list(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            assert process.stdout is not None
            for line in process.stdout:
                sys.stdout.write(line)
                log_file.write(line)
            returncode = process.wait()
    except OSError as exc:
        pending.unlink(missing_ok=True)
        print(f"REFUSED[MIX_EXEC_FAILED] {exc}", file=sys.stderr)
        return 66

    if returncode != 0:
        pending.unlink(missing_ok=True)
        print(f"REFUSED[MIX_NONZERO_EXIT] exit={returncode}", file=sys.stderr)
        return returncode

    os.replace(pending, receipt)
    print(f"ALIVE[RECEIPT_PROMOTED] {receipt}")
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pending", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return run_receipted_mix(args.pending, args.receipt, args.log, args.command)


if __name__ == "__main__":
    raise SystemExit(main())
