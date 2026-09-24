#!/usr/bin/env python3
"""Embed a wave spec into the sm-lane-wave runner so Workflow can run it by scriptPath (scripts cannot read files)."""
import json, sys, pathlib
spec_path = pathlib.Path(sys.argv[1])
runner = pathlib.Path.home() / '.claude/workflows/sm-lane-wave.js'
src = runner.read_text()
spec = json.loads(spec_path.read_text())
needle = 'const A = args || {}'
assert src.count(needle) == 1, 'runner args line changed'
src = src.replace(needle, 'const A = (args && args.wave) ? args : ' + json.dumps(spec, ensure_ascii=False))
out = spec_path.with_suffix('.run.js')
out.write_text(src)
print(out)
