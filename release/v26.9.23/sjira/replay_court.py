#!/usr/bin/env python3
"""Replay court for gate logs and fleet R receipts (lane CE-INTAKE, repair round 2).

A receipt's replay field is only admissible if every recorded command, re-executed
literally, exits with the recorded code (fleet R schema: replay.commands[].{cmd, cwd,
exit}; ~/.claude/dfcm/receipt.schema.json). Repair round 1 recorded a command line in
receipts/v26.9.23/CE-INTAKE.gate/r1-12-invariants.log that exits 2 when run literally
(a 4-argument cmp whose 3rd and 4th arguments are skip offsets), next to exit=0: a
hand-transcribed log (broken term R_missing_replay). This court closes that class:
`record` executes exactly the string it writes, and `log` / `receipt` re-execute every
recorded command and refuse any exit that differs.

  replay_court.py record --log LOG [--cwd DIR] [--timeout S] -- 'CMD'
  replay_court.py log --log LOG [--cwd DIR] [--timeout S]
  replay_court.py receipt --receipt RECEIPT.json [--timeout S]

Log format (the gate-log format of receipts/v26.9.23/CE-INTAKE.gate/):

  $ <command, one line, run as /bin/sh -c '<command>' in --cwd>
  <combined stdout+stderr>
  exit=<code>

A block opens at a line starting with "$ " and closes at the next line matching
^exit=<integer>; a second "$ " line before that exit line leaves the first block
unterminated (refused: a command with no recorded exit replays nothing). Lines
outside blocks are notes. `record` writes output lines that would read as a block
boundary ("$ ..." or "exit=...") indented by two spaces, then re-parses the log and
refuses unless its last block is exactly the command and exit it executed.

Commands run with the caller's environment and cwd (--cwd, default: the current
directory for `log`/`record`; each command's own cwd for `receipt`). Exit codes are
compared, not output bytes: outputs carry scratch paths and timings.

Exit: 0 every block replays to its recorded exit (record: the block was written);
1 a mismatch, an unterminated block, a missing cwd or a timeout; 2 usage.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EXIT_LINE = re.compile(r"^exit=(-?\d+)")
DEFAULT_TIMEOUT = 1200  # seconds; one command stays under the lane's 20-minute bound


def parse_log(text: str) -> tuple[list[tuple[int, str, int]], list[str]]:
    """Return ([(line_no, cmd, exit)], [problems]) for a gate log."""
    blocks: list[tuple[int, str, int]] = []
    problems: list[str] = []
    open_block: tuple[int, str] | None = None
    for no, line in enumerate(text.splitlines(), start=1):
        if line.startswith("$ "):
            if open_block is not None:
                problems.append(f"line {open_block[0]}: unterminated block (no exit= before line {no})")
            open_block = (no, line[2:])
            continue
        m = EXIT_LINE.match(line)
        if m and open_block is not None:
            blocks.append((open_block[0], open_block[1], int(m.group(1))))
            open_block = None
    if open_block is not None:
        problems.append(f"line {open_block[0]}: unterminated block (no exit= before end of log)")
    return blocks, problems


def execute(cmd: str, cwd: Path, timeout: int) -> tuple[int | None, str]:
    """Run cmd as /bin/sh -c cmd in cwd; return (exit or None on timeout, combined output)."""
    try:
        done = subprocess.run(
            ["/bin/sh", "-c", cmd],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or b""
        return None, out.decode("utf-8", "replace")
    return done.returncode, done.stdout.decode("utf-8", "replace")


def replay(entries: list[tuple[str, str, Path, int]], timeout: int) -> int:
    """entries: (label, cmd, cwd, recorded exit). Print one verdict line per entry."""
    bad = 0
    for label, cmd, cwd, want in entries:
        if not cwd.is_dir():
            print(f"REFUSED {label}: cwd {cwd} does not exist")
            bad += 1
            continue
        got, out = execute(cmd, cwd, timeout)
        if got is None:
            print(f"REFUSED {label}: timeout after {timeout}s (recorded exit={want})")
            bad += 1
        elif got != want:
            tail = out.strip().splitlines()[-1:] or [""]
            print(f"REFUSED {label}: recorded exit={want}, replayed exit={got} ({tail[0][:160]!r})")
            bad += 1
        else:
            print(f"OK {label}: exit={got}")
    return bad


def cmd_record(args: argparse.Namespace) -> int:
    command = " ".join(args.command).strip()
    if not command or "\n" in command:
        print("usage: record needs one single-line command after --", file=sys.stderr)
        return 2
    cwd = Path(args.cwd).resolve()
    got, out = execute(command, cwd, args.timeout)
    if got is None:
        print(f"REFUSED record: timeout after {args.timeout}s: {command}")
        return 1
    lines = []
    for line in out.splitlines():
        if line.startswith("$ ") or EXIT_LINE.match(line):
            line = "  " + line
        lines.append(line)
    block = "$ " + command + "\n" + "".join(x + "\n" for x in lines) + f"exit={got}\n"
    log = Path(args.log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(block)
    sys.stdout.write(block)
    blocks, problems = parse_log(log.read_text(encoding="utf-8"))
    if problems or not blocks or blocks[-1][1:] != (command, got):
        print(f"REFUSED record: {log} does not re-parse to the executed block ({problems})")
        return 1
    print(f"RECORDED {log}: exit={got}")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    log = Path(args.log)
    blocks, problems = parse_log(log.read_text(encoding="utf-8"))
    for p in problems:
        print(f"REFUSED {log}: {p}")
    if not blocks and not problems:
        print(f"REFUSED {log}: no recorded command")
        return 1
    cwd = Path(args.cwd).resolve()
    bad = replay([(f"{log}:{no}", cmd, cwd, want) for no, cmd, want in blocks], args.timeout)
    bad += len(problems)
    total = len(blocks) + len(problems)
    verdict = "REPLAY OK" if bad == 0 else "REPLAY REFUSED"
    print(f"{verdict}: {total - bad}/{total} blocks of {log} replay to their recorded exit")
    return 0 if bad == 0 else 1


def cmd_receipt(args: argparse.Namespace) -> int:
    path = Path(args.receipt)
    try:
        commands = json.loads(path.read_text(encoding="utf-8"))["replay"]["commands"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"REFUSED {path}: no replay.commands ({type(exc).__name__}: {exc})")
        return 1
    entries = []
    problems = 0
    for i, c in enumerate(commands, start=1):
        if not isinstance(c, dict) or not isinstance(c.get("cmd"), str) or not isinstance(c.get("exit"), int):
            print(f"REFUSED {path}#{i}: command entry lacks cmd/exit")
            problems += 1
            continue
        entries.append((f"{path}#{i}", c["cmd"], Path(str(c.get("cwd", "."))), c["exit"]))
    if not entries and not problems:
        print(f"REFUSED {path}: replay.commands is empty")
        return 1
    bad = replay(entries, args.timeout) + problems
    total = len(entries) + problems
    verdict = "REPLAY OK" if bad == 0 else "REPLAY REFUSED"
    print(f"{verdict}: {total - bad}/{total} replay.commands of {path} replay to their recorded exit")
    return 0 if bad == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="replay_court.py", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    rec = sub.add_parser("record", help="execute one command and append its block to a gate log")
    rec.add_argument("--log", required=True)
    rec.add_argument("--cwd", default=".")
    rec.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    rec.add_argument("command", nargs=argparse.REMAINDER)
    lg = sub.add_parser("log", help="re-execute every block of a gate log")
    lg.add_argument("--log", required=True)
    lg.add_argument("--cwd", default=".")
    lg.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    rc = sub.add_parser("receipt", help="re-execute every replay.commands entry of a fleet R receipt")
    rc.add_argument("--receipt", required=True)
    rc.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    args = parser.parse_args(argv)
    if args.mode == "record":
        if args.command and args.command[0] == "--":
            args.command = args.command[1:]
        return cmd_record(args)
    if args.mode == "log":
        return cmd_log(args)
    return cmd_receipt(args)


if __name__ == "__main__":
    sys.exit(main())
