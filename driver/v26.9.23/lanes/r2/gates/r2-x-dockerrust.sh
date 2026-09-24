#!/bin/sh
# R2-X-DOCKERRUST gate (xaas, static court on Dockerfile + ci_cd.yaml image-check). usage: r2-x-dockerrust.sh [subject-worktree]
#  (1) the builder stage (everything before the second FROM) can compile ggen_igniter's Rustler NIF:
#      a Rust toolchain >= 1.87 (oxigraph / oxrocksdb-sys 0.5.11 rust-version) and clang + libclang-dev (bindgen);
#  (2) that toolchain is an admitted input: either COPY --from a digest-pinned rust image (@sha256:...) or a
#      rustup-init fetched by a fixed URL and checked with sha256sum -c; an unverified `curl ... | sh` is refused;
#  (3) jobs.image-check.timeout-minutes >= ceil(1.5 x the measured hosted image-check job 23m24s) = 36;
#  (4) publish-image / deploy conditions are byte-identical to the R1-X-FENCE subject 6f59676.
# Local probe without Rust: System.cmd("cargo", ["metadata", ...]) :enoent (NO_CARGO_IN_BUILDER).
set -eu
SUBJ=$(cd "${1:-$PWD}" && pwd); cd "$SUBJ"
FENCE=6f59676
echo "# subject=$SUBJ head=$(git rev-parse HEAD) fence_ref=$FENCE"
git cat-file -e "$FENCE^{commit}"
git show "$FENCE:.github/workflows/ci_cd.yaml" > "${TMPDIR:-/tmp}/r2-x-fence-ci_cd.$$.yaml"
python3 - "${TMPDIR:-/tmp}/r2-x-fence-ci_cd.$$.yaml" <<'PY'
import math, re, sys, yaml
bad = []
lines = open("Dockerfile").read().splitlines()
froms = [i for i, l in enumerate(lines) if re.match(r"^\s*FROM\s", l, re.I)]
if len(froms) < 2:
    bad.append("Dockerfile has no separate builder stage")
builder = "\n".join(lines[: froms[1]] if len(froms) > 1 else lines)
logical = re.sub(r"\\\n", " ", builder)
vers = [tuple(map(int, m)) for m in re.findall(r"--default-toolchain\s+(\d+)\.(\d+)", logical)]
vers += [tuple(map(int, m)) for m in re.findall(r"rust:(\d+)\.(\d+)", logical)]
print("builder rust toolchains:", vers)
if not vers or max(vers) < (1, 87):
    bad.append("no Rust toolchain >= 1.87 in the builder stage")
for pkg in ("clang", "libclang-dev"):
    if not re.search(r"apt-get install[^\n]*\b" + re.escape(pkg) + r"\b", logical):
        bad.append(f"builder apt layer lacks {pkg}")
pinned_image = re.search(r"COPY\s+--from=\S*rust:[^\s@]+@sha256:[0-9a-f]{64}", logical) or re.search(r"FROM\s+\S*rust:[^\s@]+@sha256:[0-9a-f]{64}", logical)
checked_init = re.search(r"rustup-init", logical) and re.search(r"sha256sum\s+(-c|--check)", logical)
piped = re.search(r"curl[^\n|]*\|\s*sh\b", logical)
print(f"pinned_image={bool(pinned_image)} checked_rustup_init={bool(checked_init)} curl_pipe_sh={bool(piped)}")
if not (pinned_image or checked_init) or (piped and not pinned_image):
    bad.append("Rust toolchain is not an integrity-pinned input (digest-pinned image or sha256-checked rustup-init)")
cur = __import__("yaml").safe_load(open(".github/workflows/ci_cd.yaml"))["jobs"]
fen = __import__("yaml").safe_load(open(sys.argv[1]))["jobs"]
need = math.ceil(1.5 * (23 * 60 + 24) / 60)
t = int(cur["image-check"].get("timeout-minutes", 0))
print(f"image-check.timeout-minutes={t} required>={need}")
if t < need:
    bad.append("image-check budget below 1.5x the measured job")
for j in ("publish-image", "deploy"):
    if cur[j].get("if") != fen[j].get("if"):
        bad.append(f"{j}.if changed vs R1-X-FENCE")
for b in bad:
    print("DOCKERRUST FAIL:", b)
print("DOCKERRUST_GATE", "OK" if not bad else "FAIL")
sys.exit(1 if bad else 0)
PY
