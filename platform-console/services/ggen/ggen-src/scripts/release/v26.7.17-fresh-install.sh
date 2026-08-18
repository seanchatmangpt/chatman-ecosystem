#!/usr/bin/env bash
# v26.7.17-fresh-install.sh -- DoD gate G6 (Clean Install) harness.
#
# G6 asks one question: if a user with no prior state installs ggen from this
# release and runs the canonical workflow, does it work? The textbook way to
# answer that is a SECOND independent machine (different OS/VM, never touched
# by this checkout). That machine is not available in this environment.
#
# Correction 3 (this release): rather than silently downgrading G6 to "ran it
# again on the same box" and calling that equivalent, this harness maximizes
# the number of INDEPENDENT COORDINATES achievable on a single machine, and
# reports the result as two distinct standings that are never merged into one
# boolean (see the bottom of this file / the final log section):
#
#   G6_LOCAL_CLEAN_ENVIRONMENT_ALIVE   -- did every local-clean-room step below
#                                          actually pass, with captured evidence
#   G6_SECOND_ENVIRONMENT_UNVERIFIED    -- always true this session: no second
#                                          independent OS/VM was available. A
#                                          disclosed limitation, not a hidden one.
#
# Independent coordinates this harness actually establishes (all separate
# mktemp locations / process boundaries, none reused across each other):
#   1. HOME               -- fresh mktemp dir; never the operator's real $HOME
#   2. CARGO_HOME          -- separate fresh mktemp dir; never ~/.cargo (no
#                              reuse of the developer's registry cache or
#                              credentials.toml)
#   3. package extract dir -- separate fresh mktemp dir, OUTSIDE the checkout
#   4. build target-dir(s) -- separate fresh mktemp dir(s); never touches this
#                              checkout's own target/
#   5. install --root      -- separate fresh mktemp dir for the installed tree
#   6. project dir         -- separate fresh mktemp dir for the init/sync/
#                              receipt canonical-workflow run
#   7. process environment -- reconstructed with `env -i` and an explicit
#                              allowlist; scrubs every GGEN_* var plus all
#                              unrelated developer shell/session state
#   8. PATH                -- rewritten to the installed binary's bin dir plus
#                              only the OS's own minimal system paths, so a
#                              stray `ggen` earlier on the operator's real PATH
#                              (e.g. an old `cargo install` or this checkout's
#                              own target/debug/ggen) can never shadow the
#                              binary under test
#
# What this harness cannot give you, and does not pretend to: a second
# physical machine, a second kernel, independent hardware, or a true
# network-namespace sandbox (no root/unshare available here). Every place
# below where a real gap exists is reported as such, not smoothed over.
#
# Usage: scripts/release/v26.7.17-fresh-install.sh [--skip-package-verify-build]
#
# Exit code: 0 if G6_LOCAL_CLEAN_ENVIRONMENT_ALIVE is true, 1 otherwise. Either
# way, full evidence is written under target/ggen-release/v26.7.17/ before this
# script returns.
set -u
set -o pipefail

# --------------------------------------------------------------------------
# Setup: paths, logging, step bookkeeping
# --------------------------------------------------------------------------

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RELEASE_VERSION="v26.7.17"
RELEASE_DIR="$REPO_ROOT/target/ggen-release/$RELEASE_VERSION"
LOG_DIR="$RELEASE_DIR/logs"
PKG_DIR="$RELEASE_DIR/packages"
INSTALL_ROOTS_DIR="$RELEASE_DIR/install-roots"
mkdir -p "$LOG_DIR" "$PKG_DIR" "$INSTALL_ROOTS_DIR"

LOG_FILE="$LOG_DIR/fresh-install.log"
SUMMARY_FILE="$LOG_DIR/fresh-install-summary.json"
: > "$LOG_FILE"

# Real wall-clock timestamps only -- never fabricated (CLAUDE.md evidence-first
# rule). Every log line is stamped with the actual `date` output at the time
# the line is written.
log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG_FILE"
}

section() {
  log ""
  log "=== $* ==="
}

declare -A STEP_STATUS
declare -A STEP_NOTE
ORDERED_STEPS=()

record() {
  local name="$1" status="$2" note="$3"
  STEP_STATUS["$name"]="$status"
  STEP_NOTE["$name"]="$note"
  ORDERED_STEPS+=("$name")
  log "STEP[$name] = $status :: $note"
}

# Optional external wall-clock cap for long-running cargo invocations. Prefer
# GNU coreutils `timeout` (Homebrew installs it un-prefixed on this host;
# also check `gtimeout` for hosts where it's g-prefixed). If neither exists,
# fall back to no external cap -- this harness's own disk guard (see
# run_with_disk_guard below) is the real backstop in that case, and that
# degradation is logged, not hidden.
TIMEOUT_BIN=""
if command -v timeout >/dev/null 2>&1; then
  TIMEOUT_BIN="timeout"
elif command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT_BIN="gtimeout"
fi

DISK_GUARD_MIN_GB=5

# df -g gives 1GB-block counts on macOS (BSD df); this host is confirmed
# Darwin. If df -g isn't supported (e.g. a future Linux run of this same
# script), fall back to `df -Pk` and convert from KB, so the guard degrades
# gracefully instead of crashing the harness.
free_gb_for() {
  local path="$1"
  if df -g "$path" >/dev/null 2>&1; then
    df -g "$path" | awk 'NR==2{print $4}'
  else
    df -Pk "$path" | awk 'NR==2{print int($4/1024/1024)}'
  fi
}

# Recursively signals a process and every descendant (post-order: children
# before parent). Plain `kill $pid` on a `bash -c 'cd x && cargo install'`
# background job is NOT sufficient: bash does not forward signals to
# unrelated child processes by default, so killing only the wrapper PID
# would orphan cargo/rustc, which then keep running (and keep consuming
# disk) uninterrupted -- exactly the failure this guard exists to prevent.
kill_tree() {
  local pid="$1" sig="$2"
  local children
  children="$(pgrep -P "$pid" 2>/dev/null || true)"
  local c
  for c in $children; do
    kill_tree "$c" "$sig"
  done
  kill -s "$sig" "$pid" 2>/dev/null || true
}

# Runs "$@" in the background, tailing to $1's sibling log file, while a
# disk-space guard polls free space on $REPO_ROOT's filesystem every 15s. If
# free space drops under DISK_GUARD_MIN_GB, the whole process tree is killed
# and a ".disk-guard-tripped" sentinel is written next to the log -- this is
# a genuine safety rail (this host had only ~39GB free at harness-authoring
# time against a workspace target/ already at 137GB) so a runaway clean-room
# build cannot fill the operator's disk. A guard trip is reported as BLOCKED,
# never silently reinterpreted as PASS or FAIL.
run_with_disk_guard() {
  local out_log="$1"; shift
  : > "$out_log"
  ( "$@" >"$out_log" 2>&1 ) &
  local pid=$!
  local tripped=0
  while kill -0 "$pid" 2>/dev/null; do
    local free_gb
    free_gb="$(free_gb_for "$REPO_ROOT" 2>/dev/null || echo 999)"
    if [ "${free_gb:-999}" -lt "$DISK_GUARD_MIN_GB" ]; then
      log "DISK GUARD TRIPPED: only ${free_gb}GB free on $REPO_ROOT's filesystem (< ${DISK_GUARD_MIN_GB}GB threshold) -- terminating pid $pid and its full process tree"
      kill_tree "$pid" TERM
      sleep 3
      kill_tree "$pid" KILL
      echo "DISK_GUARD_TRIPPED at $(date -u +%Y-%m-%dT%H:%M:%SZ), free_gb=${free_gb}" > "$out_log.disk-guard-tripped"
      tripped=1
      break
    fi
    sleep 15
  done
  wait "$pid" 2>/dev/null
  local rc=$?
  if [ "$tripped" -eq 1 ]; then
    return 97
  fi
  return $rc
}

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

# --------------------------------------------------------------------------
# Step 0: capture the real repo state this run is evidence FOR
# --------------------------------------------------------------------------

section "Step 0: repo state"
cd "$REPO_ROOT"
GIT_SHA="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
GIT_PORCELAIN="$(git status --porcelain 2>/dev/null || true)"
if [ -n "$GIT_PORCELAIN" ]; then
  GIT_DIRTY=true
else
  GIT_DIRTY=false
fi
log "repo_root=$REPO_ROOT"
log "git_sha=$GIT_SHA"
log "git_branch=$GIT_BRANCH"
log "git_dirty=$GIT_DIRTY"
log "free_disk_gb_at_start=$(free_gb_for "$REPO_ROOT" 2>/dev/null || echo unknown)"
if [ "$GIT_DIRTY" = true ]; then
  log "dirty files (git status --porcelain):"
  printf '%s\n' "$GIT_PORCELAIN" | tee -a "$LOG_FILE"
  log "note: uncommitted changes are expected if other tasks are running in parallel in this workspace; --allow-dirty will be used for cargo package below because of this."
fi
record "repo_state_captured" "PASS" "sha=$GIT_SHA branch=$GIT_BRANCH dirty=$GIT_DIRTY"

# --------------------------------------------------------------------------
# Steps 1-2: independent clean HOME and CARGO_HOME coordinates
# --------------------------------------------------------------------------

section "Steps 1-2: clean HOME + clean CARGO_HOME"

CLEAN_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ggen-g6-home.XXXXXX")"
CLEAN_CARGO_HOME="$(mktemp -d "${TMPDIR:-/tmp}/ggen-g6-cargo-home.XXXXXX")"
CLEAN_PKG_EXTRACT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ggen-g6-pkg-extract.XXXXXX")"
CLEAN_INSTALL_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ggen-g6-install-root.XXXXXX")"
CLEAN_PROJECT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ggen-g6-project.XXXXXX")"
CLEAN_BUILD_TARGET_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ggen-g6-target.XXXXXX")"

COORDINATE_VIOLATION=""
for d in "$CLEAN_HOME" "$CLEAN_CARGO_HOME" "$CLEAN_PKG_EXTRACT_DIR" "$CLEAN_INSTALL_ROOT" "$CLEAN_PROJECT_DIR" "$CLEAN_BUILD_TARGET_ROOT"; do
  log "coordinate dir: $d"
  case "$d" in
    "$REPO_ROOT"/*)
      COORDINATE_VIOLATION="$d is INSIDE $REPO_ROOT"
      ;;
  esac
done
if [ -n "$COORDINATE_VIOLATION" ]; then
  record "coordinate_outside_checkout" "FAIL" "$COORDINATE_VIOLATION -- isolation coordinate violated"
else
  record "coordinate_outside_checkout" "PASS" "all 6 mktemp coordinate dirs are outside $REPO_ROOT"
fi
record "clean_home_created" "$([ -d "$CLEAN_HOME" ] && echo PASS || echo FAIL)" "HOME=$CLEAN_HOME"
record "clean_cargo_home_created" "$([ -d "$CLEAN_CARGO_HOME" ] && echo PASS || echo FAIL)" "CARGO_HOME=$CLEAN_CARGO_HOME"

# --------------------------------------------------------------------------
# Steps 3-4: verify no pre-existing ~/.ggen or pack cache is visible under
# the clean HOME (this is inherently true of a fresh mktemp dir -- the point
# of this step is to assert it explicitly with a real test -d check rather
# than assume it, per the task's own instruction).
# --------------------------------------------------------------------------

section "Steps 3-4: verify no ~/.ggen / pack cache visible under clean HOME"

# ~/.ggen itself (project-level installs write here as a fallback destination
# -- see crates/ggen-marketplace/src/marketplace/install.rs's home_dir()-based
# default pack destination, ".ggen/packs/<pack_id>" under home_dir()).
GGEN_HOME_DIR="$CLEAN_HOME/.ggen"
if [ -d "$GGEN_HOME_DIR" ]; then
  record "no_ggen_home_dir_visible" "FAIL" "$GGEN_HOME_DIR unexpectedly exists"
else
  record "no_ggen_home_dir_visible" "PASS" "test -d $GGEN_HOME_DIR is false, as required"
fi

# Pack cache candidate 1: ~/.ggen/packs (marketplace/install.rs:1571-1573,
# dirs::home_dir().join(".ggen").join("packs").join(<pack_id>))
PACK_CACHE_HOME="$CLEAN_HOME/.ggen/packs"
if [ -d "$PACK_CACHE_HOME" ]; then
  record "no_pack_cache_home_visible" "FAIL" "$PACK_CACHE_HOME unexpectedly exists"
else
  record "no_pack_cache_home_visible" "PASS" "test -d $PACK_CACHE_HOME is false, as required"
fi

# Pack cache candidate 2: dirs::cache_dir()/ggen/packs -- on macOS `dirs`
# resolves cache_dir() to $HOME/Library/Caches (crates/ggen-marketplace/src/
# marketplace/metadata.rs's pack_cache_dir). Since HOME is now the clean temp
# dir, this path is also necessarily fresh; verified explicitly rather than
# assumed.
PACK_CACHE_XDG="$CLEAN_HOME/Library/Caches/ggen/packs"
if [ -d "$PACK_CACHE_XDG" ]; then
  record "no_pack_cache_xdg_visible" "FAIL" "$PACK_CACHE_XDG unexpectedly exists"
else
  record "no_pack_cache_xdg_visible" "PASS" "test -d $PACK_CACHE_XDG is false, as required"
fi

# --------------------------------------------------------------------------
# Step 5: package the current workspace's `ggen` (root) package
# --------------------------------------------------------------------------

section "Step 5: cargo package -p ggen"

export HOME="$CLEAN_HOME"
export CARGO_HOME="$CLEAN_CARGO_HOME"

PACKAGE_ARGS=(-p ggen --locked)
if [ "$GIT_DIRTY" = true ]; then
  PACKAGE_ARGS+=(--allow-dirty)
  log "tree is dirty at run time -> using --allow-dirty"
else
  log "tree is clean at run time -> omitting --allow-dirty"
fi

PKG_BUILD_TARGET_DIR="$CLEAN_BUILD_TARGET_ROOT/pkg"
# --no-verify: disclosed, deliberate deviation from the literal `cargo package
# -p ggen --locked --allow-dirty` command line. Rationale (real, measured,
# not a guess): this host had ~39GB free against a workspace target/ already
# at 137GB at harness-authoring time. `cargo package`'s default verify step
# performs a full build of the packaged crate's entire dependency graph
# (tokio-full, oxigraph, opentelemetry, genai, ...) inside a fresh, empty
# CARGO_HOME -- i.e. a second full from-scratch compile with no cache reuse,
# on top of whatever the later, AUTHORITATIVE build step (step 6) will
# already do. Running it twice is not extra evidence, it is a real risk of
# exhausting this machine's disk before step 6 (the step that actually
# produces the binary under test) gets to run. The genuine "does this build"
# question is answered by step 6, not duplicated here.
PACKAGE_ARGS+=(--no-verify --target-dir "$PKG_BUILD_TARGET_DIR")

log "+ cargo package ${PACKAGE_ARGS[*]}"
PACKAGE_LOG="$LOG_DIR/step5-cargo-package.log"
( cd "$REPO_ROOT" && cargo package "${PACKAGE_ARGS[@]}" ) >"$PACKAGE_LOG" 2>&1
PACKAGE_RC=$?
cat "$PACKAGE_LOG" | tee -a "$LOG_FILE" >/dev/null
log "cargo package exit_code=$PACKAGE_RC"

CRATE_FILE=""
if [ "$PACKAGE_RC" -eq 0 ]; then
  CRATE_FILE="$(find "$PKG_BUILD_TARGET_DIR/package" -maxdepth 1 -name 'ggen-*.crate' 2>/dev/null | head -n1)"
fi

if [ -n "$CRATE_FILE" ] && [ -f "$CRATE_FILE" ]; then
  cp "$CRATE_FILE" "$PKG_DIR/"
  CRATE_DIGEST="$(sha256_of "$CRATE_FILE")"
  echo "$CRATE_DIGEST  $(basename "$CRATE_FILE")" > "$PKG_DIR/$(basename "$CRATE_FILE").sha256"
  log "packaged crate: $CRATE_FILE"
  log "packaged crate sha256: $CRATE_DIGEST"
  record "cargo_package_ggen" "PASS" "produced $(basename "$CRATE_FILE"), sha256=$CRATE_DIGEST"
else
  record "cargo_package_ggen" "FAIL" "cargo package exit_code=$PACKAGE_RC, no .crate file found under $PKG_BUILD_TARGET_DIR/package -- see $PACKAGE_LOG"
fi

# --------------------------------------------------------------------------
# Step 5b / 6a: extract the .crate OUTSIDE the checkout and attempt a
# standalone build FROM THAT EXTRACTED PACKAGE ONLY.
# --------------------------------------------------------------------------

section "Step 6a: extract package outside checkout + attempt standalone build"

STANDALONE_BUILD_ATTEMPTED=false
STANDALONE_BUILD_FEASIBLE=false
CRATE_SRC_DIR=""

if [ -n "$CRATE_FILE" ] && [ -f "$CRATE_FILE" ]; then
  tar -xzf "$CRATE_FILE" -C "$CLEAN_PKG_EXTRACT_DIR"
  CRATE_SRC_DIR="$(find "$CLEAN_PKG_EXTRACT_DIR" -maxdepth 1 -type d -name 'ggen-*' | head -n1)"
  if [ -n "$CRATE_SRC_DIR" ] && [ -d "$CRATE_SRC_DIR" ]; then
    IS_OUTSIDE_CHECKOUT="yes"
    case "$CRATE_SRC_DIR" in
      "$REPO_ROOT"*) IS_OUTSIDE_CHECKOUT="no" ;;
    esac
    log "extracted package to: $CRATE_SRC_DIR (outside $REPO_ROOT: $IS_OUTSIDE_CHECKOUT)"
    record "package_extracted_outside_checkout" "PASS" "$CRATE_SRC_DIR"

    # Structural check, independent of any build attempt: does the packaged
    # manifest carry a [[bin]] target at all? Root `ggen`'s own Cargo.toml
    # has `autobins = false` and no [[bin]] section (removed 2026-07-16 --
    # see Cargo.toml's own comment on this). A packaged Cargo.toml never
    # gains a bin target that wasn't in the source manifest, so this is
    # decidable by inspection alone, with certainty, before any build runs.
    if grep -q '^\[\[bin\]\]' "$CRATE_SRC_DIR/Cargo.toml" 2>/dev/null; then
      log "unexpected: extracted Cargo.toml DOES declare a [[bin]] target"
    else
      log "confirmed: extracted Cargo.toml has no [[bin]] target (root \`ggen\` package is publish-safe library-only since the 2026-07-16 CLI-routing flip)"
      record "standalone_package_has_bin_target" "FAIL (expected)" "no [[bin]] in packaged Cargo.toml -- this package can never produce a \`ggen\` executable, independent of whether it builds"
    fi

    STANDALONE_BUILD_ATTEMPTED=true
    FETCH_LOG="$LOG_DIR/step6a-cargo-fetch.log"
    log "+ (cd $CRATE_SRC_DIR && cargo fetch --locked)  # cheap dependency-resolution probe before a full build attempt"
    ( cd "$CRATE_SRC_DIR" && ${TIMEOUT_BIN:+$TIMEOUT_BIN 300} cargo fetch --locked ) >"$FETCH_LOG" 2>&1
    FETCH_RC=$?
    cat "$FETCH_LOG" | tee -a "$LOG_FILE" >/dev/null
    log "cargo fetch (standalone extracted package) exit_code=$FETCH_RC"

    if [ "$FETCH_RC" -eq 0 ]; then
      BUILD_LOG="$LOG_DIR/step6a-cargo-build.log"
      log "+ (cd $CRATE_SRC_DIR && cargo build --locked --target-dir $CLEAN_BUILD_TARGET_ROOT/standalone)"
      ( cd "$CRATE_SRC_DIR" && ${TIMEOUT_BIN:+$TIMEOUT_BIN 600} cargo build --locked --target-dir "$CLEAN_BUILD_TARGET_ROOT/standalone" ) >"$BUILD_LOG" 2>&1
      BUILD_RC=$?
      cat "$BUILD_LOG" | tee -a "$LOG_FILE" >/dev/null
      log "cargo build (standalone extracted package) exit_code=$BUILD_RC"
      if [ "$BUILD_RC" -eq 0 ]; then
        STANDALONE_BUILD_FEASIBLE=true
        record "standalone_package_build" "PASS (library only, no bin produced)" "dependency resolution + library compile succeeded from the extracted package alone; still cannot produce a ggen executable (see standalone_package_has_bin_target above)"
      else
        record "standalone_package_build" "FAIL" "exit_code=$BUILD_RC -- see $BUILD_LOG (real, not fabricated: workspace-internal path deps were rewritten to registry version pins by \`cargo package\`, and those pinned versions/content may not resolve or match outside the workspace)"
      fi
    else
      # Note (corrected after the first real run of this harness, 2026-07-17):
      # the failure observed here was NOT the version-pin mismatch this
      # comment originally speculated about -- it was rustup refusing to
      # pick a toolchain at all ("rustup could not choose a version of cargo
      # to run ... no default is configured"), because the extracted
      # tarball carries no rust-toolchain.toml (that file lives at the
      # workspace root, outside this package's `include` list, so it is
      # never packaged). See $FETCH_LOG for the exact captured error on any
      # given run. Whether the version-pin concern below is ALSO a real
      # blocker remains unproven either way -- resolution never got that
      # far. Both are logged, neither is asserted past what was observed.
      record "standalone_package_build" "FAIL" "cargo fetch (dependency resolution alone) failed with exit_code=$FETCH_RC before any compile was attempted -- see $FETCH_LOG for the exact captured error. First real run (2026-07-17) observed: rustup could not select a toolchain outside the workspace (no rust-toolchain.toml in the packaged tarball -- that file lives at the workspace root and is not part of this package's \`include\` list). A separate, still-untested concern: this package's path dependencies (ggen-config, ggen-marketplace) were rewritten by \`cargo package\` into registry version pins (e.g. \"26.7.2\"/\"26.7.1\") that may not match what is actually published on crates.io for those crates -- unproven either way since resolution never got past the toolchain error."
    fi
  else
    record "package_extracted_outside_checkout" "FAIL" "tar extraction produced no ggen-* directory under $CLEAN_PKG_EXTRACT_DIR"
  fi
else
  record "package_extracted_outside_checkout" "SKIP" "no .crate file from step 5 to extract"
fi

log "conclusion for the IDEAL path (point 6, first sentence): infeasible, for a structural reason independent of network/build results -- crates/../Cargo.toml for the ROOT \`ggen\` package has autobins=false and no [[bin]] section (removed 2026-07-16 CLI-routing flip, see that file's own comment). \`cargo package -p ggen\` can only ever produce a library crate's tarball. The actual \`ggen\` binary is built by a DIFFERENT package, ggen-cli-lib (crates/ggen-cli, \`[[bin]] name = \"ggen\"\`), which is \`publish = false\` and therefore cannot itself be the target of a \`cargo package\`/crates.io-style standalone install. Falling back to method B per the task's own documented fallback."

# --------------------------------------------------------------------------
# Step 6b: fallback authoritative install -- `cargo install --path
# crates/ggen-cli --root <clean install root>`, still under the clean
# HOME/CARGO_HOME/no-cache coordinates established above.
# --------------------------------------------------------------------------

section "Step 6b: cargo install --path crates/ggen-cli (fallback; labeled explicitly)"

log "INSTALL METHOD USED: fallback (method B) -- cargo install --path crates/ggen-cli --root <clean root>."
log "WHY: method A (build the extracted, standalone .crate package) cannot produce a ggen executable under any circumstance, because the packaged crate (root package \`ggen\`) carries no [[bin]] target -- a structural fact of this workspace's 2026-07-16 CLI-routing flip, not a build failure. The real \`ggen\` binary is defined by crates/ggen-cli's own [[bin]] (package name ggen-cli-lib). This IS still source from the original checkout (crates/ggen-cli is a workspace member, resolved via this checkout's own Cargo.lock) -- unlike method A, method B does NOT achieve 'installed binary genuinely cannot see the development checkout'. That gap is disclosed here, not hidden: everything downstream (HOME, CARGO_HOME, install root, project dir, PATH, process environment) is still the clean/independent coordinates set up above."

log "free_disk_gb_before_install=$(free_gb_for "$REPO_ROOT" 2>/dev/null || echo unknown)"
INSTALL_TARGET_DIR="$CLEAN_BUILD_TARGET_ROOT/install"
INSTALL_LOG="$LOG_DIR/step6b-cargo-install.log"

# --debug (dev profile, not release): disclosed, deliberate. A release build
# of this crate's full dependency graph from a genuinely empty CARGO_HOME
# (fresh network fetch of every dependency, no registry cache reuse) is a
# large, slow compile; --debug trades runtime binary performance (irrelevant
# to this correctness/idempotency probe) for a much shorter compile, which
# matters given this host's disk headroom (see disk guard above).
log "+ cargo install --path crates/ggen-cli --root $CLEAN_INSTALL_ROOT --locked --debug --target-dir $INSTALL_TARGET_DIR"
run_with_disk_guard "$INSTALL_LOG" bash -c "cd '$REPO_ROOT' && cargo install --path crates/ggen-cli --root '$CLEAN_INSTALL_ROOT' --locked --debug --target-dir '$INSTALL_TARGET_DIR'"
INSTALL_RC=$?
cat "$INSTALL_LOG" | tee -a "$LOG_FILE" >/dev/null
log "cargo install exit_code=$INSTALL_RC"
log "free_disk_gb_after_install=$(free_gb_for "$REPO_ROOT" 2>/dev/null || echo unknown)"

INSTALLED_GGEN="$CLEAN_INSTALL_ROOT/bin/ggen"
if [ "$INSTALL_RC" -eq 97 ]; then
  record "cargo_install_ggen_cli" "BLOCKED" "disk guard tripped during install -- see $INSTALL_LOG.disk-guard-tripped; this machine's free disk was insufficient to complete a from-scratch clean-CARGO_HOME build safely"
elif [ "$INSTALL_RC" -eq 0 ] && [ -x "$INSTALLED_GGEN" ]; then
  BIN_DIGEST="$(sha256_of "$INSTALLED_GGEN")"
  echo "$BIN_DIGEST  ggen" > "$INSTALL_ROOTS_DIR/installed-ggen.sha256"
  cp "$INSTALLED_GGEN" "$INSTALL_ROOTS_DIR/ggen.installed-binary" 2>/dev/null || true
  log "installed binary: $INSTALLED_GGEN"
  log "installed binary sha256: $BIN_DIGEST"
  record "cargo_install_ggen_cli" "PASS" "installed to $INSTALLED_GGEN, sha256=$BIN_DIGEST"
else
  record "cargo_install_ggen_cli" "FAIL" "exit_code=$INSTALL_RC or binary missing/not executable at $INSTALLED_GGEN -- see $INSTALL_LOG"
fi

# --------------------------------------------------------------------------
# Step 7: scrub GGEN_* env vars from the subprocess environment used for
# every remaining step. Reconstructed via `env -i` + an explicit allowlist
# rather than a bare `unset`, so unrelated developer shell state (aliases,
# functions, stray exported vars) cannot leak into the binary under test
# either -- this is itself one of the extra independent coordinates.
# --------------------------------------------------------------------------

section "Step 7: scrub GGEN_* env vars + rebuild a minimal subprocess environment"

mapfile -t LEAKED_GGEN_VARS < <(env | awk -F= '/^GGEN_/{print $1}')
if [ "${#LEAKED_GGEN_VARS[@]}" -gt 0 ]; then
  log "GGEN_* vars present in the harness's own shell (will NOT be forwarded): ${LEAKED_GGEN_VARS[*]}"
else
  log "no GGEN_* vars present in the harness's own shell"
fi

CLEAN_BIN_DIR="$CLEAN_INSTALL_ROOT/bin"
CLEAN_PATH="$CLEAN_BIN_DIR:/usr/bin:/bin:/usr/sbin:/sbin"
record "ggen_env_scrubbed" "PASS" "subprocess environment for every step below is env -i HOME=$CLEAN_HOME CARGO_HOME=$CLEAN_CARGO_HOME PATH=$CLEAN_PATH (no GGEN_* vars, no inherited developer shell state)"

run_clean() {
  env -i \
    HOME="$CLEAN_HOME" \
    CARGO_HOME="$CLEAN_CARGO_HOME" \
    PATH="$CLEAN_PATH" \
    TMPDIR="${TMPDIR:-/tmp}" \
    LANG="${LANG:-C}" \
    "$@"
}

# --------------------------------------------------------------------------
# Step 8: canonical workflow, installed binary ONLY, fresh project dir
# --------------------------------------------------------------------------

section "Step 8: canonical workflow (init / sync --dry-run / sync / receipt verify)"

if [ "$INSTALL_RC" -eq 0 ] && [ -x "$INSTALLED_GGEN" ]; then
  RESOLVED_GGEN="$(run_clean command -v ggen)"
  log "PATH-resolved ggen (inside the clean subprocess env): $RESOLVED_GGEN"
  if [ "$RESOLVED_GGEN" = "$INSTALLED_GGEN" ]; then
    record "resolved_binary_is_installed_binary" "PASS" "command -v ggen == $INSTALLED_GGEN (never /Users/sac/ggen/target/debug/ggen)"
  else
    record "resolved_binary_is_installed_binary" "FAIL" "command -v ggen resolved to $RESOLVED_GGEN, expected $INSTALLED_GGEN"
  fi

  WORKFLOW_LOG="$LOG_DIR/step8-canonical-workflow.log"
  : > "$WORKFLOW_LOG"

  cd "$CLEAN_PROJECT_DIR"
  log "project dir: $CLEAN_PROJECT_DIR"

  log "+ ggen init --skip-hooks true"
  INIT_OUT="$(run_clean "$INSTALLED_GGEN" init --skip-hooks true 2>&1)"
  INIT_RC=$?
  printf '%s\n' "$INIT_OUT" >> "$WORKFLOW_LOG"
  printf '%s\n' "$INIT_OUT" | tee -a "$LOG_FILE" >/dev/null
  if [ "$INIT_RC" -eq 0 ] && printf '%s' "$INIT_OUT" | grep -q '"status": "success"'; then
    record "ggen_init" "PASS" "exit_code=$INIT_RC, status=success"
  else
    record "ggen_init" "FAIL" "exit_code=$INIT_RC -- see $WORKFLOW_LOG"
  fi

  log "+ ggen sync run --dry-run"
  SYNC_DRY_OUT="$(run_clean "$INSTALLED_GGEN" sync run --dry-run 2>&1)"
  SYNC_DRY_RC=$?
  printf '%s\n' "$SYNC_DRY_OUT" >> "$WORKFLOW_LOG"
  printf '%s\n' "$SYNC_DRY_OUT" | tee -a "$LOG_FILE" >/dev/null
  if [ "$SYNC_DRY_RC" -eq 0 ] && printf '%s' "$SYNC_DRY_OUT" | grep -q '"graph_hash_hex"'; then
    record "ggen_sync_dry_run" "PASS" "exit_code=$SYNC_DRY_RC"
  else
    record "ggen_sync_dry_run" "FAIL" "exit_code=$SYNC_DRY_RC -- see $WORKFLOW_LOG"
  fi

  log "+ ggen sync run"
  SYNC_OUT_1="$(run_clean "$INSTALLED_GGEN" sync run 2>&1)"
  SYNC_RC_1=$?
  printf '%s\n' "$SYNC_OUT_1" >> "$WORKFLOW_LOG"
  printf '%s\n' "$SYNC_OUT_1" | tee -a "$LOG_FILE" >/dev/null
  if [ "$SYNC_RC_1" -eq 0 ] && printf '%s' "$SYNC_OUT_1" | grep -q '"written"'; then
    record "ggen_sync_run" "PASS" "exit_code=$SYNC_RC_1"
  else
    record "ggen_sync_run" "FAIL" "exit_code=$SYNC_RC_1 -- see $WORKFLOW_LOG"
  fi

  log "+ ggen receipt verify"
  RECEIPT_OUT_1="$(run_clean "$INSTALLED_GGEN" receipt verify 2>&1)"
  RECEIPT_RC_1=$?
  printf '%s\n' "$RECEIPT_OUT_1" >> "$WORKFLOW_LOG"
  printf '%s\n' "$RECEIPT_OUT_1" | tee -a "$LOG_FILE" >/dev/null
  if [ "$RECEIPT_RC_1" -eq 0 ] && printf '%s' "$RECEIPT_OUT_1" | grep -q '"valid": true' && printf '%s' "$RECEIPT_OUT_1" | grep -q '"signature_valid": true'; then
    record "ggen_receipt_verify" "PASS" "exit_code=$RECEIPT_RC_1, valid=true, signature_valid=true"
  else
    record "ggen_receipt_verify" "FAIL" "exit_code=$RECEIPT_RC_1 -- see $WORKFLOW_LOG"
  fi

  # ------------------------------------------------------------------------
  # Step 9: idempotency -- run `ggen sync run` a second time, confirm no
  # unexpected delta (must report "skipped: unchanged", not a fresh write).
  # ------------------------------------------------------------------------

  section "Step 9: idempotency (second sync run)"

  log "+ ggen sync run (second run, idempotency check)"
  SYNC_OUT_2="$(run_clean "$INSTALLED_GGEN" sync run 2>&1)"
  SYNC_RC_2=$?
  printf '%s\n' "$SYNC_OUT_2" >> "$WORKFLOW_LOG"
  printf '%s\n' "$SYNC_OUT_2" | tee -a "$LOG_FILE" >/dev/null

  GRAPH_HASH_1="$(printf '%s' "$SYNC_OUT_1" | grep -o '"graph_hash_hex": *"[^"]*"' | head -n1)"
  GRAPH_HASH_2="$(printf '%s' "$SYNC_OUT_2" | grep -o '"graph_hash_hex": *"[^"]*"' | head -n1)"
  WRITTEN_2_EMPTY="$(printf '%s' "$SYNC_OUT_2" | grep -o '"written": *\[\]')"
  SKIPPED_UNCHANGED="$(printf '%s' "$SYNC_OUT_2" | grep -o 'skipped: unchanged[^"]*')"

  if [ "$SYNC_RC_2" -eq 0 ] && [ -n "$WRITTEN_2_EMPTY" ] && [ -n "$SKIPPED_UNCHANGED" ] && [ "$GRAPH_HASH_1" = "$GRAPH_HASH_2" ]; then
    record "ggen_sync_idempotent" "PASS" "second run: written=[], decision='$SKIPPED_UNCHANGED', graph_hash unchanged ($GRAPH_HASH_1)"
  else
    record "ggen_sync_idempotent" "FAIL" "second run exit_code=$SYNC_RC_2, written_empty=$([ -n "$WRITTEN_2_EMPTY" ] && echo yes || echo no), skipped_unchanged=$([ -n "$SKIPPED_UNCHANGED" ] && echo yes || echo no), graph_hash_1=$GRAPH_HASH_1 graph_hash_2=$GRAPH_HASH_2 -- see $WORKFLOW_LOG"
  fi

  log "+ ggen receipt verify (post-idempotency)"
  RECEIPT_OUT_2="$(run_clean "$INSTALLED_GGEN" receipt verify 2>&1)"
  RECEIPT_RC_2=$?
  printf '%s\n' "$RECEIPT_OUT_2" >> "$WORKFLOW_LOG"
  printf '%s\n' "$RECEIPT_OUT_2" | tee -a "$LOG_FILE" >/dev/null
  if [ "$RECEIPT_RC_2" -eq 0 ] && printf '%s' "$RECEIPT_OUT_2" | grep -q '"valid": true'; then
    record "ggen_receipt_verify_post_idempotency" "PASS" "exit_code=$RECEIPT_RC_2"
  else
    record "ggen_receipt_verify_post_idempotency" "FAIL" "exit_code=$RECEIPT_RC_2 -- see $WORKFLOW_LOG"
  fi

  # ------------------------------------------------------------------------
  # Step 10: offline rerun attempt. There is no true kernel-level network
  # namespace available here (no root/unshare on this macOS host, and the
  # ggen CLI itself exposes no --offline/--no-network flag on the sync/init/
  # receipt nouns -- confirmed by grepping ggen-cli's and ggen-engine's verb
  # sources; the RDF-derived `offline` flag that DOES exist is scoped only to
  # `pack add`/`pack install`, which this canonical workflow never invokes).
  # Best effort taken here: point every proxy env var at an unroutable
  # address, so IF anything in this workflow attempted an outbound HTTP call
  # it would fail fast (connection refused / timeout) instead of silently
  # succeeding over a real network path. This is disclosed as a best-effort
  # proxy trick, not claimed as real network isolation.
  # ------------------------------------------------------------------------

  section "Step 10: best-effort offline rerun (disclosed limitation, not faked)"

  log "LIMITATION (disclosed, not hidden): no OS-level network namespace is available in this environment (no root/unshare on this macOS host). ggen's sync/init/receipt nouns also expose no --offline flag to invoke instead (the CLI's only 'offline' argument belongs to the pack add/install verb, unused by this canonical workflow). Best effort only: HTTP_PROXY/HTTPS_PROXY/ALL_PROXY point at an unroutable address (127.0.0.1:9) for this rerun, so any attempted outbound call would fail fast rather than silently succeed."

  OFFLINE_LOG="$LOG_DIR/step10-offline-rerun.log"
  OFFLINE_OUT="$(env -i \
    HOME="$CLEAN_HOME" \
    CARGO_HOME="$CLEAN_CARGO_HOME" \
    PATH="$CLEAN_PATH" \
    TMPDIR="${TMPDIR:-/tmp}" \
    LANG="${LANG:-C}" \
    HTTP_PROXY="http://127.0.0.1:9" \
    HTTPS_PROXY="http://127.0.0.1:9" \
    ALL_PROXY="http://127.0.0.1:9" \
    "$INSTALLED_GGEN" sync run 2>&1)"
  OFFLINE_RC=$?
  printf '%s\n' "$OFFLINE_OUT" > "$OFFLINE_LOG"
  printf '%s\n' "$OFFLINE_OUT" | tee -a "$LOG_FILE" >/dev/null
  if [ "$OFFLINE_RC" -eq 0 ]; then
    record "offline_rerun_best_effort" "PASS (best-effort proxy-block only)" "exit_code=$OFFLINE_RC under an unroutable HTTP(S)_PROXY -- consistent with this canonical workflow performing no real network I/O, but NOT independently proven at the OS/kernel level (see disclosed limitation above)"
  else
    record "offline_rerun_best_effort" "FAIL" "exit_code=$OFFLINE_RC -- see $OFFLINE_LOG"
  fi

  cd "$REPO_ROOT"
else
  record "resolved_binary_is_installed_binary" "SKIP" "no installed binary from step 6b"
  record "ggen_init" "SKIP" "no installed binary from step 6b"
  record "ggen_sync_dry_run" "SKIP" "no installed binary from step 6b"
  record "ggen_sync_run" "SKIP" "no installed binary from step 6b"
  record "ggen_receipt_verify" "SKIP" "no installed binary from step 6b"
  record "ggen_sync_idempotent" "SKIP" "no installed binary from step 6b"
  record "ggen_receipt_verify_post_idempotency" "SKIP" "no installed binary from step 6b"
  record "offline_rerun_best_effort" "SKIP" "no installed binary from step 6b"
fi

# --------------------------------------------------------------------------
# Step 11: logs + digests are ALREADY under target/ggen-release/v26.7.17/
# (written there directly throughout this run, not staged in a temp dir) --
# this section just confirms and records their final locations before the
# temp coordinates are destroyed in step 12.
# --------------------------------------------------------------------------

section "Step 11: evidence locations (already persisted outside the temp coordinates)"

log "logs:          $LOG_DIR"
log "packages:      $PKG_DIR"
log "install-roots: $INSTALL_ROOTS_DIR"
record "evidence_persisted" "PASS" "logs=$LOG_DIR packages=$PKG_DIR install-roots=$INSTALL_ROOTS_DIR"

# --------------------------------------------------------------------------
# Step 12: destroy the temporary environment, now that evidence is captured
# --------------------------------------------------------------------------

section "Step 12: destroy temporary coordinates"

for d in "$CLEAN_HOME" "$CLEAN_CARGO_HOME" "$CLEAN_PKG_EXTRACT_DIR" "$CLEAN_INSTALL_ROOT" "$CLEAN_PROJECT_DIR" "$CLEAN_BUILD_TARGET_ROOT"; do
  log "rm -rf $d"
  rm -rf "$d"
done
record "temp_coordinates_destroyed" "PASS" "all 6 mktemp coordinate dirs removed"

# --------------------------------------------------------------------------
# Step 13: two DISTINCT standings -- never merged into one boolean
# --------------------------------------------------------------------------

section "Step 13: G6 standings"

REQUIRED_FOR_ALIVE=(
  repo_state_captured
  clean_home_created
  clean_cargo_home_created
  no_ggen_home_dir_visible
  no_pack_cache_home_visible
  no_pack_cache_xdg_visible
  cargo_package_ggen
  package_extracted_outside_checkout
  cargo_install_ggen_cli
  ggen_env_scrubbed
  resolved_binary_is_installed_binary
  ggen_init
  ggen_sync_dry_run
  ggen_sync_run
  ggen_receipt_verify
  ggen_sync_idempotent
  ggen_receipt_verify_post_idempotency
  evidence_persisted
  temp_coordinates_destroyed
)

ALIVE=true
FAILED_STEPS=()
for s in "${REQUIRED_FOR_ALIVE[@]}"; do
  status="${STEP_STATUS[$s]:-MISSING}"
  case "$status" in
    PASS*) ;;
    *)
      ALIVE=false
      FAILED_STEPS+=("$s=$status")
      ;;
  esac
done

log ""
log "--------------------------------------------------------------"
if [ "$ALIVE" = true ]; then
  log "G6_LOCAL_CLEAN_ENVIRONMENT_ALIVE = true"
  log "  Every local-clean-room step succeeded on this one machine, under 6"
  log "  independent mktemp coordinates (HOME, CARGO_HOME, package-extract dir,"
  log "  build target-dir(s), install root, project dir), a scrubbed GGEN_*-free"
  log "  subprocess environment, and a PATH containing only the installed"
  log "  binary's bin dir + minimal system paths. See per-step evidence above."
else
  log "G6_LOCAL_CLEAN_ENVIRONMENT_ALIVE = false"
  log "  Failed/blocked/skipped steps: ${FAILED_STEPS[*]}"
fi
log ""
log "G6_SECOND_ENVIRONMENT_UNVERIFIED = true (always true this session)"
log "  No second independent OS/VM was available in this environment. This is"
log "  a real, disclosed limitation of THIS run's evidence, not a failure being"
log "  hidden inside the standing above: G6_LOCAL_CLEAN_ENVIRONMENT_ALIVE, even"
log "  if true, certifies only that this ONE machine's clean-room coordinates"
log "  behave correctly -- it does NOT certify cross-OS/cross-hardware behavior."
log "--------------------------------------------------------------"

# Machine-readable summary alongside the human log.
{
  printf '{\n'
  printf '  "release_version": "%s",\n' "$RELEASE_VERSION"
  printf '  "generated_at_utc": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '  "git_sha": "%s",\n' "$GIT_SHA"
  printf '  "git_branch": "%s",\n' "$GIT_BRANCH"
  printf '  "git_dirty": %s,\n' "$GIT_DIRTY"
  printf '  "install_method_used": "fallback_cargo_install_path",\n'
  printf '  "standings": {\n'
  printf '    "G6_LOCAL_CLEAN_ENVIRONMENT_ALIVE": %s,\n' "$ALIVE"
  printf '    "G6_SECOND_ENVIRONMENT_UNVERIFIED": true\n'
  printf '  },\n'
  printf '  "steps": {\n'
  first=true
  for s in "${ORDERED_STEPS[@]}"; do
    if [ "$first" = true ]; then first=false; else printf ',\n'; fi
    esc_note="$(printf '%s' "${STEP_NOTE[$s]}" | sed 's/\\/\\\\/g; s/"/\\"/g')"
    printf '    "%s": {"status": "%s", "note": "%s"}' "$s" "${STEP_STATUS[$s]}" "$esc_note"
  done
  printf '\n  }\n'
  printf '}\n'
} > "$SUMMARY_FILE"

log "machine-readable summary: $SUMMARY_FILE"

if [ "$ALIVE" = true ]; then
  exit 0
else
  exit 1
fi
