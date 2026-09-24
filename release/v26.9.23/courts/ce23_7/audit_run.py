#!/usr/bin/env python3
r"""Run one Chatman tool unmodified and record what it reads (CE23-7 court probe).

    python3 audit_run.py <audit-log> <tool.py> [tool args...]

A PEP 578 audit hook appends one line per observed event to <audit-log>, then the
tool runs as ``__main__`` exactly as ``python3 <tool.py> ...`` would: same argv, same
sys.path[0], same exit status. The hook observes; it never changes what the tool
reads or does. Line kinds (a realpath always starts with "/", a tag with "@"):

  <realpath>             ``open`` (file reads and writes, os.open, module imports)
  @dir\t<realpath>       os.listdir / os.scandir / os.chdir / glob.glob (a directory read)
  @db\t<realpath>        sqlite3.connect (a file opened by native code)
  @exec\t<json>          subprocess.Popen / os.exec / os.posix_spawn / os.spawn / os.system:
                         a child process, whose own reads this hook cannot see
  @native\t<json>        ctypes.dlopen / ctypes.dlsym / ctypes.call_function: native code
                         that can open files without an ``open`` event
  @net\t<json>           socket.connect to a non-loopback address (an off-host read)
  @url\t<url>            urllib.Request (the URL a tool asked for, loopback or not)
  @blind\t<json>         the hook itself failed on an event (the court cannot see that read)

The court (court.py) judges these lines; the tool's own source path is always logged
(runpy opens it), which is the court's witness that the probe fired.
"""

from __future__ import annotations

import json
import os
import runpy
import sys

PATH_EVENTS = {"os.listdir": "@dir", "os.scandir": "@dir", "os.chdir": "@dir", "glob.glob": "@dir",
               "glob.glob/2": "@dir", "sqlite3.connect": "@db", "sqlite3.connect/handle": None}
EXEC_EVENTS = ("subprocess.Popen", "os.exec", "os.posix_spawn", "os.spawn", "os.system", "os.startfile")
NATIVE_EVENTS = ("ctypes.dlopen", "ctypes.dlsym", "ctypes.dlsym/handle", "ctypes.call_function")
LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def _text(value: object) -> str:
    if isinstance(value, (bytes, bytearray)):
        return os.fsdecode(bytes(value))
    if isinstance(value, (list, tuple)):
        return json.dumps([_text(item) for item in value])
    return str(value)


def _realpath(value: object) -> str | None:
    if value is None or isinstance(value, int):
        return None
    try:
        return os.path.realpath(os.fsdecode(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def main() -> None:
    if len(sys.argv) < 3:
        sys.stderr.write("usage: audit_run.py <audit-log> <tool.py> [args...]\n")
        raise SystemExit(64)
    log = open(sys.argv[1], "a", encoding="utf-8")  # opened before the hook: not logged
    script = os.path.realpath(sys.argv[2])

    def emit(line: str) -> None:
        log.write(line.replace("\n", "\\n") + "\n")
        log.flush()

    def hook(event: str, args: tuple) -> None:
        try:
            observe(event, args)
        except Exception as exc:  # noqa: BLE001 - a probe fault is a blind spot, never a silent pass
            emit("@blind\t" + json.dumps({"event": event, "probe_error": repr(exc)}))

    def observe(event: str, args: tuple) -> None:
        if event == "open":
            path = _realpath(args[0]) if args else None
            if path is not None:
                emit(path)
        elif event in PATH_EVENTS:
            tag = PATH_EVENTS[event]
            path = _realpath(args[0] if args else None) if tag else None
            if tag and path is not None:
                emit(f"{tag}\t{path}")
            elif tag and args and args[0] is None and event != "glob.glob":
                emit(f"{tag}\t{os.path.realpath('.')}")
        elif event in EXEC_EVENTS:
            emit("@exec\t" + json.dumps({"event": event, "args": [_text(a) for a in args if not isinstance(a, dict)],
                                         "cwd": os.getcwd()}))
        elif event in NATIVE_EVENTS:
            emit("@native\t" + json.dumps({"event": event, "args": [_text(a) for a in args[:2]]}))
        elif event == "socket.connect" and len(args) >= 2:
            address = args[1]
            host = address[0] if isinstance(address, tuple) and address else address
            if _text(host) not in LOOPBACK:
                emit("@net\t" + json.dumps({"event": event, "address": _text(address)}))
        elif event == "urllib.Request" and args:
            emit(f"@url\t{_text(args[0])}")

    sys.addaudithook(hook)
    sys.argv = [sys.argv[2], *sys.argv[3:]]
    sys.path[0] = os.path.dirname(script)
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
