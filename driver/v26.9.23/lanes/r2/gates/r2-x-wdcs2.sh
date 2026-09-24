#!/bin/sh
# R2-X-WDCS2 gate (xaas). usage: r2-x-wdcs2.sh [subject-worktree]
# Static court on the three measured causes of the WD CS2 exact-head failure, then the real asset build:
#  (1) assets/ is not an ES module package (root package.json has "type": "module", so esbuild would read the
#      UMD assets/vendor/topbar.js as ESM: 'No matching export in vendor/topbar.js for import default');
#  (2) the workflow builds priv/static/assets (untracked) before it starts the Phoenix server;
#  (3) the LiveView socket is admitted from the origin the workflow uses: EITHER the workflow addresses the
#      server as localhost (the test endpoint's url host; swarm candidate, hosted-witnessed run 35928423483)
#      OR config/test.exs sets check_origin: false on XaasWeb.Endpoint (scan-plan R2-X-WDCS2 variant, precedent
#      config/dev.exs:65). 127.0.0.1 with the default check_origin is refused (403), so LiveView never connects;
#  (4) real: `mix assets.setup && mix assets.build` exits 0 under the xaas pin.
# Witnessed failing on main-equivalent b9bf336 (run 35826687758) and release head 246460c (run 35923001574);
# passing with the candidate on 0e2ec64 (run 35928423483).
set -eu
SUBJ=$(cd "${1:-$PWD}" && pwd); cd "$SUBJ"
PIN=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin
PATH="$PIN:$PATH"; export PATH
echo "# subject=$SUBJ head=$(git rev-parse HEAD)"
elixir --version | tail -1
python3 - <<'PY'
import json, os, sys, yaml
bad = []
p = "assets/package.json"
if not os.path.isfile(p):
    bad.append("assets/package.json absent: esbuild inherits the root package.json 'type': 'module'")
elif json.load(open(p)).get("type") == "module":
    bad.append("assets/package.json declares type=module")
wf = yaml.safe_load(open(".github/workflows/wd-cs2-exact-head.yml"))
steps = wf["jobs"]["wd-cs2"]["steps"]
run = lambda s: str(s.get("run", ""))
build = [i for i, s in enumerate(steps) if "mix assets.build" in run(s)]
server = [i for i, s in enumerate(steps) if "phx.server" in run(s)]
if not build or not server or min(build) > min(server):
    bad.append(f"assets not built before the server starts (assets.build steps {build}, phx.server steps {server})")
import re
text = open(".github/workflows/wd-cs2-exact-head.yml").read()
cfg = open("config/test.exs").read()
origin_off = re.search(r"config :xaas, XaasWeb\.Endpoint,(?:(?!\nconfig ).)*?check_origin:\s*false", cfg, re.S)
base = [s.get("env", {}).get("PLAYWRIGHT_BASE_URL") for s in steps if "PLAYWRIGHT_BASE_URL" in s.get("env", {})]
localhost = "127.0.0.1:4002" not in text and base and all(str(b).startswith("http://localhost:4002") for b in base)
print(f"origin fix: workflow_localhost={bool(localhost)} test_check_origin_false={bool(origin_off)}")
if not (localhost or origin_off):
    bad.append(f"LiveView origin still refused: workflow uses {base} and config/test.exs keeps check_origin")
for b in bad:
    print("WDCS2_STATIC FAIL:", b)
print("WDCS2_STATIC", "OK" if not bad else "FAIL")
sys.exit(1 if bad else 0)
PY
mix format --check-formatted
MIX_ENV=test mix assets.setup
MIX_ENV=test mix assets.build
echo "WDCS2_GATE OK"
