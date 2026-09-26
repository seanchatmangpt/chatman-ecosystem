#!/usr/bin/env python3
"""Replay ~/.claude/dfcm/topology_guard_cases.json through the real hook script (subprocess, real stdin JSON)."""

import json, os, subprocess, sys

G = os.path.expanduser("~/.claude/dfcm/topology_guard.py")
cases = json.load(open(os.path.expanduser("~/.claude/dfcm/topology_guard_cases.json")))
fail = []
for want, ev in cases:
    p = subprocess.run(["python3", G], input=json.dumps(ev), capture_output=True, text=True)
    got = "DENY" if '"deny"' in p.stdout else "allow"
    if got != want or p.returncode != 0:
        fail.append({"want": want, "got": got, "rc": p.returncode, "ev": ev, "err": p.stderr[-300:]})
out = {"cases": len(cases), "failures": len(fail), "failed": fail}
home = os.environ.get("TOPO_HOME", os.path.dirname(os.path.abspath(__file__)))
json.dump(out, open(os.path.join(home, "verify", "guard.json"), "w"), indent=1)
print(json.dumps(out, indent=1)[:4000])
sys.exit(1 if fail else 0)
