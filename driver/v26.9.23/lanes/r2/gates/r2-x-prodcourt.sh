#!/bin/sh
# R2-X-PRODCOURT gate (xaas, static court on .github/workflows/ci_cd.yaml). usage: r2-x-prodcourt.sh [subject-worktree]
#  (1) jobs.production.timeout-minutes >= ceil(1.5 x the longest measured complete hosted production job):
#      runs 35928419752 (18m30s) and 35930975356 (21m31s) -> 1291 s -> 33 min. 12 cancelled every surveyed run.
#  (2) the clean-state semantics stay: a production step still runs `rm -rf deps _build`.
#  (3) publish-image and deploy conditions are byte-identical to the R1-X-FENCE subject 6f59676 and the
#      push-to-main condition is absent (no authority change rides on this lane).
# The diff touches no .ex/.exs file, so the wave's compile prefix has no consumer here; format is still checked.
set -eu
SUBJ=$(cd "${1:-$PWD}" && pwd); cd "$SUBJ"
PIN=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin
FENCE=6f59676
echo "# subject=$SUBJ head=$(git rev-parse HEAD) fence_ref=$FENCE"
git cat-file -e "$FENCE^{commit}"
git show "$FENCE:.github/workflows/ci_cd.yaml" > "${TMPDIR:-/tmp}/r2-x-fence-ci_cd.$$.yaml"
python3 - "${TMPDIR:-/tmp}/r2-x-fence-ci_cd.$$.yaml" <<'PY'
import math, re, sys, yaml
cur = yaml.safe_load(open(".github/workflows/ci_cd.yaml"))["jobs"]
fen = yaml.safe_load(open(sys.argv[1]))["jobs"]
bad = []
need = math.ceil(1.5 * max(18 * 60 + 30, 21 * 60 + 31) / 60)
t = int(cur["production"].get("timeout-minutes", 0))
print(f"production.timeout-minutes={t} required>={need}")
if t < need:
    bad.append("production budget below 1.5x the measured job")
if not any("rm -rf deps _build" in str(s.get("run", "")) for s in cur["production"]["steps"]):
    bad.append("production no longer starts from a clean deps/_build")
for j in ("publish-image", "deploy"):
    if cur[j].get("if") != fen[j].get("if"):
        bad.append(f"{j}.if changed vs R1-X-FENCE: {cur[j].get('if')!r}")
    print(f"{j}.if={cur[j].get('if')!r}")
text = open(".github/workflows/ci_cd.yaml").read()
if re.search(r"^    if: github.event_name == .push. && github.ref == .refs/heads/main.$", text, re.M):
    bad.append("push-to-main publish/deploy condition present")
for b in bad:
    print("PRODCOURT FAIL:", b)
print("PRODCOURT_GATE", "OK" if not bad else "FAIL")
sys.exit(1 if bad else 0)
PY
PATH="$PIN:$PATH" mix format --check-formatted
