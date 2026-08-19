# act Local CI Runbook — What Actually Ran, Not a Tutorial

> Status: draft, evidence-grounded. Every claim below cites a real command and real output from
> a single session (2026-08-17/19) on this machine (`act 0.2.87`, colima-backed Docker 29.2.1,
> aarch64 host). This is not a general "how to use act" guide — it is a record of what act
> substituted for successfully, what it did not, and a copy-pasteable procedure limited to what
> was verified.

## Environment this was run against

- `act` 0.2.87, already installed.
- Docker daemon real and reachable, but **not** at the default socket path: the active context
  was colima, whose socket lives at `unix:///Users/sac/.colima/default/docker.sock`, not
  `/var/run/docker.sock`. `docker info` / `docker ps` both exited 0 once `DOCKER_HOST` was set
  explicitly.
- act's own docker-in-docker socket bind-mount does not work against colima's macOS-side socket
  path (`mkdir /Users/sac/.colima/default/docker.sock: operation not supported` inside the Lima
  VM) — every successful run in this session needed `--container-daemon-socket` pointed at the
  in-VM path (`unix:///var/run/docker.sock` or `-` to disable it) instead of letting act infer it
  from `DOCKER_HOST`.

These two workarounds are colima-specific, not act's stock happy path on Docker Desktop, and are
required prerequisites for every command below.

## 1. What act genuinely substitutes for right now

Three repos, three jobs, three real container runs against real source. All three actually
executed steps inside a real Ubuntu-act container on the colima daemon — this is not a dry run
or a description of expected behavior.

### `ggen` — `refused` job (docs.yml)

Chosen because it has no checkout, no Rust toolchain, no external actions — a minimal, isolated
job used here to prove the colima/act plumbing works before spending time on heavier jobs.

```bash
cd /Users/sac/ggen
DOCKER_HOST=unix:///Users/sac/.colima/default/docker.sock \
  act -j refused \
  -P ubuntu-24.04=catthehacker/ubuntu:act-latest \
  --container-architecture linux/amd64 \
  --container-daemon-socket /var/run/docker.sock
```

Result: ran to completion. The job's own designed behavior (`exit 1` with
`REFUSED:OBSOLETE_ONE_OFF_MUTATION`) fired correctly — `act` correctly executed and reported an
intentionally-failing job. This confirms the harness (pull, container create, step exec, exit
code propagation) works end to end under colima.

### `gymact` — `cloudsim` job (ci.yml)

The heaviest job that actually completed its substantive work in this pass.

```bash
cd /Users/sac/gymact
DOCKER_HOST=unix:///Users/sac/.colima/default/docker.sock \
  act -j cloudsim \
  -P ubuntu-24.04=catthehacker/ubuntu:act-latest \
  --pull=false \
  --container-daemon-socket -
```

(Required first: `mkdir -p ~/.cache/tmp` — act's `docker cp` fallback path assumes this directory
exists and does not create it.)

Real steps that ran and passed, in order:

- Real `git checkout`, commit `b59d7aab8ea65df8a5214e0ee5ad963168851b98`.
- Real `actions/setup-python@…` download of CPython 3.13.15 from the actual
  `actions/python-versions` release tarball.
- Real `astral-sh/uv` 0.11.32 install from its actual GitHub release.
- Real `uv sync --group dev`: "Resolved 214 packages in 56.39s", building `gymact` and
  `wasm4pm-compat-pydantic` from real git dependencies, 126 packages installed.
- A real AST-based check step ("Prove cloud package has no vendor SDK dependency") — real output
  `vendor_cloud_sdk_imports=0`.
- Real `pytest` run with `pytest-socket` (external sockets disabled): `collected 38 items … 38
  passed in 1.26s`.
- A real receipt JSON emitted and printed (`standing=ALIVE`, `credentials=EMPTY`,
  `vendor_cloud_sdk_imports=0`).

This is the strongest evidence in this pass that act can substitute for a real GH-hosted Python
CI job: checkout, language setup, dependency resolution, and test execution all ran for real,
against real upstream package registries, inside a local container.

### `castle` — `test` job (ci.yml, stable Rust)

```bash
cd /Users/sac/castle
DOCKER_HOST=unix:///Users/sac/.colima/default/docker.sock \
  act -j test --container-daemon-socket unix:///var/run/docker.sock
```

Real steps that ran and passed:

- `cargo build` (workspace, all targets) — Success in 44.38s.
- `cargo test` (workspace) — 14 test binaries, all passing, e.g. `test result: ok. 11 passed; 0
  failed`, Success in 21.41s.
- `cargo clippy` (reporting only, non-blocking) — 148 warnings, Success in 12.51s.

This confirms act can substitute for a **stable-Rust** build+test+clippy CI job with real crate
compilation on arm64 via colima. `castle`'s `ci.yml` pins stable Rust, so this pass does not say
anything about the nightly-toolchain case (see gaps below).

## 2. What act could not substitute for, and exactly why

Named per real failure/gap actually hit in this pass — not a generic list of act's known
limitations.

- **`actions/upload-artifact@v7.0.1` (gymact `cloudsim`)**: failed with `::error::Unable to get
  the ACTIONS_RUNTIME_TOKEN env variable`. This action version calls the real GitHub Actions
  runtime artifact-service API, which only exists on GitHub-hosted runners; act has no local
  backend for it. This was the job's only failure — every substantive step before it passed.
  **Any job that uploads artifacts with a recent `upload-artifact` version will fail at that
  step under act**, regardless of how correct the rest of the job is.

- **`dtolnay/rust-toolchain` post-action cleanup (castle `test`)**: after all three real CI steps
  passed, the job still reported `Job failed` because the toolchain action's post-step tried
  `lstat` on an act action-cache directory (`~/.cache/act/dtolnay-rust-toolchain@…/`) that was
  never populated — act had cloned the action via git instead of populating that cache path. Not
  a CI-logic problem; an act/action-caching quirk. Not worked around (root cause not fully
  chased) — recorded as an open gap, not fixed.

- **Nightly Rust toolchain + sccache + composite action + sibling-repo fetch (ggen's `admission`
  /`deep` jobs in `ci.yml`, `quality.yml`'s `replay`)**: **not attempted in this pass.** ggen's
  own task documentation warns these jobs use a pinned nightly toolchain via
  `./.github/actions/setup-ggen-build`, sccache, and likely sibling-repo fetches. None of that
  was exercised — their act-compatibility is unknown, not verified working, and should not be
  assumed to work by extension from the `refused` job result above.

- **Secrets-gated jobs (`gymact`'s `release`, `castle`'s `release`)**: not attempted. Both need
  push access and/or secrets act does not have configured in this environment.

- **Provisioning-heavy jobs (`gymact`'s `core` — kind/terraform + 3-version Python matrix, ~25min
  timeout; `gymact`'s `artifact`, `crown`, `docs`, `world-execution` — docker build/run,
  cross-job artifact dependencies, or `push`/`workflow_run` triggers)**: not attempted, explicitly
  excluded as too heavy or structurally unrunnable standalone under act.

- **docker-in-docker inside the job container**: the `--container-daemon-socket -` workaround
  used for `gymact` disables the docker-in-docker bind mount entirely. Any job step that itself
  calls `docker build`/`docker run` (e.g. ggen/gymact `artifact` jobs) would not work under that
  specific flag combination — this was a real, deliberate trade-off made to get `cloudsim`
  running, not a general act capability.

- **act's local git-object action cache**: hit a real corruption/race
  (`~/.cache/act/actions-setup-python@v5`, "object not found", "rename … no such file or
  directory") on first attempt against gymact, requiring `rm -rf` of that cache directory before
  a clean run succeeded. Reproducible risk on any first/interrupted run, not repo-specific.

## 3. Copy-pasteable procedure: "GH Actions queue is stuck, do this instead"

Scoped to exactly what was verified in this pass: a job with checkout + language setup + real
dependency install/build + test execution, on either Python (uv-based) or stable Rust, with **no**
artifact upload, **no** secrets, **no** docker-in-docker, **no** nightly Rust toolchain.

```bash
# 0. One-time: point Docker at the real running daemon (colima, not the default socket)
export DOCKER_HOST=unix:///Users/sac/.colima/default/docker.sock
mkdir -p ~/.cache/tmp   # act's docker-cp fallback assumes this exists

# 1. List jobs in the repo's workflow(s) to find the one you need
cd /path/to/repo
act -l

# 2. Dry-run first — validates the step plan without executing
act -j <job> -n -P ubuntu-24.04=catthehacker/ubuntu:act-latest

# 3a. Python/uv-shaped job (checkout, setup-python, uv sync, pytest, no artifact upload)
act -j <job> \
  -P ubuntu-24.04=catthehacker/ubuntu:act-latest \
  --pull=false \
  --container-daemon-socket -

# 3b. Stable-Rust job (checkout, dtolnay/rust-toolchain stable, cargo build/test/clippy)
act -j <job> \
  --container-daemon-socket unix:///var/run/docker.sock
# Expect a spurious "Job failed" from the dtolnay post-step lstat bug even when every
# real cargo step above it printed Success — read the per-step log, not just the final
# job status, to tell a real failure from this known act quirk.

# 4. If the daemon connection itself fails first ("Cannot connect to the Docker daemon"),
#    confirm the live context and socket path, then re-export DOCKER_HOST:
docker context ls
docker context inspect --format '{{.Endpoints.docker.Host}}' <active-context>
```

If the job you need has any of: artifact upload via `actions/upload-artifact@v7+`, secrets,
`docker build`/`docker run` inside the job, a nightly/pinned custom Rust toolchain via a
composite action, or provisioning (kind/terraform) — this procedure has **not** been shown to
work for it in this pass. Either wait for the GH-hosted queue, or strip the job down to a
temporary local-only variant (checkout + build + test only) before running it under act.

## 4. Explicit non-claims

- Not claiming act works for nightly-Rust, sccache, or sibling-repo-fetching jobs — none were
  attempted.
- Not claiming artifact-upload steps work under act — the one attempted (`upload-artifact@v7.0.1`)
  failed on a real missing-runtime-token error with no workaround applied.
- Not claiming secrets-gated or push/release jobs work under act — none were attempted.
- Not claiming docker-in-docker works under act in this colima setup — the working `cloudsim` run
  explicitly disabled it (`--container-daemon-socket -`), which would break any step needing it.
- Not claiming the `castle` `test` job is fully green under act — it reported `Job failed` overall
  due to a post-step act/action-cache bug, even though every real CI step (build, test, clippy)
  passed. "Passed" above refers to the individual step results shown in the log, not the job's
  final exit status.
- Not claiming this procedure generalizes to Docker Desktop setups — the two socket-path
  workarounds (`DOCKER_HOST` override, `--container-daemon-socket`) are specific to this
  colima-backed environment; a stock Docker Desktop install would not need them, and has not been
  tested here.
- Not claiming any of the three "not attempted" job categories (provisioning-heavy, nightly-Rust,
  secrets/release) would fail under act — their status is genuinely unknown, not a predicted
  failure, because nothing was run against them.
