#!/usr/bin/env python3
"""Run one Chatman tool unmodified and record every path it opens (CE23-7 court probe).

    python3 audit_run.py <open-log> <tool.py> [tool args...]

A PEP 578 audit hook appends the real path of every ``open`` event (file reads and
writes, module imports) to <open-log>, one per line, then the tool runs as
``__main__`` exactly as ``python3 <tool.py> ...`` would: same argv, same sys.path[0],
same exit status. The hook observes; it never changes what the tool reads or does.
The tool's own source path is always logged (runpy opens it), which is the court's
witness that the probe fired.
"""

from __future__ import annotations

import os
import runpy
import sys


def main() -> None:
    if len(sys.argv) < 3:
        sys.stderr.write("usage: audit_run.py <open-log> <tool.py> [args...]\n")
        raise SystemExit(64)
    log = open(sys.argv[1], "a", encoding="utf-8")  # opened before the hook: not logged
    script = os.path.realpath(sys.argv[2])

    def hook(event: str, args: tuple) -> None:
        if event != "open" or not args:
            return
        target = args[0]
        if isinstance(target, int):
            return
        try:
            path = os.path.realpath(os.fsdecode(target))
        except (TypeError, ValueError):
            return
        log.write(path + "\n")
        log.flush()

    sys.addaudithook(hook)
    sys.argv = [sys.argv[2], *sys.argv[3:]]
    sys.path[0] = os.path.dirname(script)
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
