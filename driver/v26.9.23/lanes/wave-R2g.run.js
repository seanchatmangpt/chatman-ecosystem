export const meta = {
  name: 'sm-lane-wave',
  description: 'Semantic-manufacturing lane wave: dependency-scheduled lanes, each build -> 3-lens court (gate, revert-mutation, doctrine) -> bounded repairs -> mkdir-locked integrate into the critical-path int worktree',
  whenToUse: 'Driver waves for sJira GoalCheckpoints (v26.9.23+). args = wave spec: {wave, repos, ints, base_branch, worktree_root, branch_prefix, receipts_dir, context, lanes:[{id, repo, after?, gate, task}]}',
  phases: [
    { title: 'Build', detail: 'one worktree per lane, branched from the int branch' },
    { title: 'Court', detail: 'gate + revert-mutation + doctrine lenses' },
    { title: 'Repair', detail: 'bounded repair rounds on refutation' },
    { title: 'Integrate', detail: 'mkdir-locked --no-ff merge into the int worktree' },
  ],
}

// Takeover-safe: deterministic control flow; labels `${wave}:<stage>:<lane>` are the public resume key.
const A = (args && args.wave) ? args : {"wave": "R2g", "repos": {"xaas": "/Users/sac/xaas", "ggen_igniter": "/Users/sac/ggen_igniter"}, "ints": {"xaas": "/Users/sac/wt/v26922/fri/xaas-int", "ggen_igniter": "/Users/sac/wt/v26922/fri/ggen_igniter-int"}, "base_branch": "friday/gc-fri-0800", "worktree_root": "/Users/sac/wt/v26922/v23", "branch_prefix": "v23", "receipts_dir": "receipts/v26.9.23", "max_repairs": 2, "status": "spec only (synth; not launched). Pre-freeze; REL-A3 waits for it.", "preconditions": ["wave R1c finished: R1-X-LOCK merged (xaas-int c68c74d); R1-X-PIN merged (60972f8 + 3ea1cfc on its branch at synth time) or re-queued", "reconcile with lanes/scan-plan.json wave R2 by defect_key before launch: R2-X-WDCS2, R2-X-PROD-TIMEOUT, R2-X-IMAGE-CARGO and R2-GI-CI share ids and keys with the scan-plan lanes; R2-X-HOSTSKIP, R2-GI-PROBE-ISOLATION and R2-GI-BLOOM are swarm-only and join; scan-only lanes (R2-X-COHERENCE, R2-X-FIXEDPOINT, R2-X-TOOLCHAIN, R2-X-PYLOCK, R2-X-TRAVERSAL) are not in this CI-only spec", "cap: at most 5 builds at once (6 lanes start without dependencies; R2-X-HOSTSKIP stops at its coverage check when R1-X-PIN merged 3ea1cfc)"], "context": "v26.9.23 contracts for this wave (also in DRIVER.md):\n- Governing graph: xaas docs/sjira/v26.9.23/goal.ttl. Instance prefix v23: = https://ggen-igniter.dev/sjira/v26.9.23# .\n  Root v23:GC-26.9.23 (dcterms:identifier \"GC-26.9.23\", sj:successorOf fri:GC-FRI-0800 from docs/sjira/v26.9.22/friday/goal.ttl),\n  gates v23:GC23-0 ... v23:GC23-12 (dcterms:identifier \"GC23-<n>\"), successor bucket v23:GC-26.9.24 (stopQuery ASK { FILTER(false) }).\n- Court scripts: every gate's sj:courtCommand is exactly \"sh docs/sjira/v26.9.23/courts/GC23-<n>.sh\" run from the xaas root.\n  Env available to courts: XAAS_DIR (xaas checkout under judgement, default: the cwd), GGEN_IGNITER_DIR (ggen_igniter checkout\n  under judgement, default /Users/sac/wt/v26922/fri/ggen_igniter-int). A court whose machinery has not landed prints\n  \"UNKNOWN: <gate> machinery lands in lane <LANE>\" and exits with the code the stop-court runner maps to UNKNOWN\n  (read lib/mix/tasks/xaas.stop_court.ex for the exit->standing mapping; add a distinct UNKNOWN code there if none exists).\n  Machinery lanes later replace their gate's script body; goal.ttl stays stable.\n- The accepted prose: /Users/sac/wt/v26922/v26923/prd-ard.md is committed byte-identical as docs/sjira/v26.9.23/prd-ard.md\n  (sha256:7c8797b2bc9130fc4c8fce9138cc8140cb704e0633715807398451c660658212, 39386 bytes; do not edit the prose).\n- PVOCAB (proposition vocabulary) is in DRIVER.md; use it verbatim.\n- xaas lane gate prefix: mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors.\n- Cross-repo chain for episodes: courts and episode runners resolve the ggen_igniter checkout from GGEN_IGNITER_DIR. A lane that\n  needs ggen_igniter code not yet merged into ggen_igniter-int creates its OWN detached ggen_igniter worktree\n  (git -C /Users/sac/ggen_igniter worktree add --detach /Users/sac/wt/v26922/v23/<LANE>-gi <sha>) and points GGEN_IGNITER_DIR at it\n  for development; its final gate run and court scripts must work against GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int.\n- Reference KNOWN class: format-drift repair (capability recipe:mix-format, suite ggen-igniter-format, provider recipe,\n  executor recipe-worker). Episode subjects are ggen_igniter commits that introduce format drift deterministically in a\n  dedicated episode branch (v23/episode-<name>), never on friday/gc-fri-0800 or main.\n- No-LLM court env (F3): no ANTHROPIC_*, CLAUDE_*, OPENAI_*, ZAI_*, Z_AI_*, GLM_*, ZCODE_* variables; no zcode/claude binary on PATH;\n  HOME a fresh mktemp dir; MIX_HOME/HEX_HOME/database URL passed explicitly as durable configuration (not credentials).\n  A court run with any LLM credential variable set must be refused with a typed REFUSED(llm_credential_present) and\n  broken_term mu_on_O.\n- OCEL: ARD §13 event classes (WorkOrderCreated, CapabilityResolved, LeaseAcquired, ActuationStarted, ActuationCompleted,\n  VerificationCompleted, ReceiptSealed, StandingChanged, FrontierChanged, MachineExperienceAdmitted) and object types;\n  validate with the existing mix xaas.ocel_validate and pm4py (python3, pm4py 2.7.22 is installed).\n- Court script ownership: the lane that lands a gate's machinery replaces that gate's docs/sjira/v26.9.23/courts/GC23-<n>.sh\n  body (keep the path and the exit-code contract from V23-P). ggen_igniter lanes cannot edit xaas: lane V23-K does that.\n- Canonical capabilityId value space (one pattern for every lane; FRI-T2/FRI-T4 already use it):\n  ^[a-z0-9][a-z0-9_.-]*:[a-z0-9][a-z0-9_.:-]*$ . sj:exclusion is 0..n everywhere (absent = empty list), never 1..n.\n  Any shape, template or regex that deviates is aligned to these in the lane that touches it (V23-C owns the pack shapes).\n- RELEASE DEFECT REPAIR (operator release sequence, frozen subjects): only the named defect may change; no successor work. Classify the\n  failure (subject defect | environment | pre-existing | generator drift | evidence defect | infrastructure) in the receipt.\n- TOOLCHAIN PIN: run every mix/elixir command under the repo's .tool-versions pin, not the ambient /opt/homebrew mix:\n  xaas: PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH\n  ggen_igniter: PATH=/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin:/Users/sac/.asdf/installs/erlang/27.2.4/bin:$PATH\n  Verify with `elixir --version` first; compile --force under the pin (a _build from another OTP must not be reused: use a fresh _build\n  in your worktree, cloning only deps/). Record the toolchain in the receipt.\n- Evidence: the release qualification that found these defects is /Users/sac/wt/v26922/v26923/receipts/fleet/xaas-e999e62b63c680517b9a562cef877d8b09b0cfdd.json\n  and its .logs/ dir (defects F1..F5).\nR2 PRE-FREEZE CI REPAIR (this wave; operator release sequence, frozen subjects; DRIVER.md 'Release closure procedure'):\n- Source: the orthogonal swarm's CI pre-flight (wf_2755fdff-28e), synthesized in /Users/sac/wt/v26922/v26923/lanes/swarm-results.json and SWARM.md.\n  Admitted: only failures that block a green exact-head CI on the Part B release PRs, classified subject defect |\n  pre-existing (R2-GI-CI's budget is reclassified from the swarm's 'infrastructure', see its task). Environment and\n  infrastructure items are not lanes (swarm-results.json env_infra).\n- S23=(sha_xaas, sha_igniter, graphDigest): every R2 lane merges BEFORE REL-A3 re-freezes S23, so the 12/13 court reruns once.\n  R2 lanes change CI configuration, the Dockerfile and tests only: no product lib/ code, no GC23 court script, no goal.ttl.\n- Candidates are O, not O*: /Users/sac/wt/v26922/v26923/lanes/r2/candidates/<file>.patch (sha256 per lane task). Apply with `git apply`, then commit -F under your own\n  identity; never `git am` (the ggen_igniter ci candidate carries the scratch author r2-scratch@example.invalid). Take only\n  your lane's hunks. Re-run every witness yourself; copy what you cite into receipts/v26.9.23/<LANE>.gate/.\n- Lane gates are durable scripts under /Users/sac/wt/v26922/v26923/lanes/r2/gates/ (argument: the subject worktree). Copy the script you ran, with its sha256,\n  into receipts/v26.9.23/<LANE>.gate/. Synth witnesses of every gate (base fails, candidate passes, mutants fail) are in\n  /Users/sac/wt/v26922/v26923/lanes/r2/witness/.\n- Pins (TOOLCHAIN PIN above): xaas 1.20.2-otp-28 / 28.5.0.2; ggen_igniter 1.18.4-otp-27 / 27.2.4; fresh _build under the pin.\n- Hosted CI witness is a receipt field, not part of the gate string (courts and the integrate step re-run the gate): push the\n  lane branch (never force; no PRs). xaas: dispatch `gh workflow run <workflow> -R seanchatmangpt/xaas --ref <lane branch>`\n  only after a YAML parse of the pushed SHA shows publish-image/deploy cannot run for that dispatch (R1-X-FENCE). ggen_igniter\n  CI runs on push. Poll in bounded steps (each command under ~20 min); a concurrency cancel under 1 min is rerun, not counted.\n- xaas hosted witnesses need R1c R1-X-PIN (60972f8 or its successor) merged into friday/gc-fri-0800 (r_projection guard,\n  dialyzer). Check `git merge-base --is-ancestor 60972f8 HEAD`; if it is absent, record the hosted witness as UNKNOWN\n  (broken_term mu_on_O) and keep the local gate verdict.\n- Covered elsewhere, do not redo: R1-GI-FMT (format step; merged 3ed6a7a); R1c R1-X-PIN 60972f8 (dialyzer\n  machine_experience.ex:539/:1235 and xaas.episode.ex:191; r_projection per-test validator guard); main's NIF-cache failure\n  (fixed on the branch by c81f8dc + 1e4b95b; main inherits it at the Part B merge).\n- Reconciliation with lanes/scan-plan.json wave R2: lanes that share a defect_key are one lane; this spec uses the scan-plan\n  lane id for shared keys. Where the two gates disagree, the lane task names the conflict; the driver's reconciled gate wins.", "after_wave_driver_steps": ["combined exact-head CI witness at the post-R2 int heads, before REL-A3: push friday/gc-fri-0800 of both repos (fast-forward, never force); ggen_igniter: the push-event 'ggen_igniter CI' run at that exact SHA concludes success (the only whole-suite green on record is 35938454860 @794cb2a = 3ed6a7a + the four ggen_igniter candidates, seed 157513); xaas: after the FENCE YAML proof, dispatch ci_cd.yaml and wd-cs2-exact-head.yml at friday/gc-fri-0800 and require every job success except publish-image/deploy skipped", "REL-A3: re-freeze S23 at the post-R2 heads, pinned qualification, 12/13 court, reseal, push, stage operator/ACCEPTED.proposed"], "sources": {"gates": {"r2-gi-bloom.sh": "26e091f29d53884a72584efb20ab1cdbb2465e12437dad998b49caefa7c3e1ff", "r2-gi-cacheseed.sh": "b7fe15d1aacbbe26891b9a55b99140dea47d245fac4afa7513baed00dddfb078", "r2-gi-depth.sh": "c3ade869b1a8b5861ecc3236fd60c5ad0cc9117a93ef99bd5da24b50cc7b9d96", "r2-gi-probe-isolation.sh": "04b87f58eea52792270be4592b9deecdcf76e29d08ca1f3adb4dd1b555312946", "r2-gi-timeout.sh": "20a074a2498ff3b54820eae1da9df6dc63b7a0d8f1302acabb12c2abf47dd99d", "r2-x-dockerrust.sh": "8860bdb7b3e38bd5b2e24f69bfbbce844bb7793fd17e9b7d333b3de2b1adda2d", "r2-x-hostskip.sh": "e2494ade0f53f3944e9b36e69b1f2cf016e239a651671ceb8c8e91e0f7c18c92", "r2-x-prodcourt.sh": "55ab3721077ca608438dd16aab43ea6e44dc7fc0eb564204b8f0e6102530cda2", "r2-x-wdcs2.sh": "fcf49f48a393d44a6b86fb87d23890e6022132faf509e520de747ec8b9a5a6c4"}, "candidates": {"r2-gi-bloom.patch": "9e491d8dccb9137f7931d3e89f3b177ef4501f702ad28c5c70f1493ae084ecb9", "r2-gi-cacheseed.patch": "2860fb4ad5159ee6d1daf1d6835d4d596809deaa2e5fde2c18d176969798a9cc", "r2-gi-depth-timeout.patch": "764e04f4b196354a817b68e807007aeccaa6016c03ce101f06a81aa7c533fd90", "r2-gi-probe-isolation.patch": "6e61bfd4d92e812f3eba224bd922067d744ce7afb5f9bd24913ec935870e9513", "r2-x-hostskip.patch": "1c1b7baa520e025958ddca55668020aca29ac45d4a88868b103359d514d97994", "r2-x-prodcourt-dockerrust.patch": "539dd3abb48a8ec024f49e1f28c3613e7a6739bd79c12664d4875e0873d40492", "r2-x-wdcs2.patch": "ff3ce3143bd95e75ab4f62fe7ca56c43f9787d7c5bd80e3cf9b158c0bdc9b944"}, "witness_dir": "/Users/sac/wt/v26922/v26923/lanes/r2/witness"}, "lanes": [{"id": "R2-GI-CI", "repo": "ggen_igniter", "after": [], "gate": "sh /Users/sac/wt/v26922/v26923/lanes/r2/gates/r2-gi-depth.sh \"$PWD\" && sh /Users/sac/wt/v26922/v26923/lanes/r2/gates/r2-gi-timeout.sh \"$PWD\"", "task": "Release defect repair (defect_key ggen_igniter-ci-fetch-depth+timeout; same id and key as scan-plan R2-GI-CI; swarm aliases R2-GI-DEPTH + R2-GI-TIMEOUT, one lane because both edit .github/workflows/ci.yml). (a) fetch-depth: actions/checkout defaults to depth 1, so the canonical baseSha d84da1419a6945c6a8a64b8f6cdca9d0b2c9e0f3 is unreachable and 3 tests in describe 'opt-in git ground truth for baseSha' (test/ggen_igniter_semantic_jira_pack_test.exs :1554, :1566, :1637) fail with REFUSED:SEMANTIC_JIRA_BASE_SHA_UNVERIFIED (CI 35895254599, 35895253020, 35895256423; locally under the pin, a depth-1 clone gives 3 failures and full history 0). Merges dropped the fix twice: 070dbd5 dropped 2f26c0b, and 4ffa201 (parents 76279a9 + a39921b) dropped a39921b. That is broken_term mu_unlawful (a merge deleted an admitted capability; conservation class C06). Replay it verbatim, do not retype: `git show a39921b -- .github/workflows/ci.yml | git apply`, and name both dropping merges in the commit message. (b) jobs.test.timeout-minutes 30 -> 90: five consecutive push runs were cancelled at 30m0s (35895253020, 35895253295, 35895254599, 35895254817, 35895256423). Complete cold jobs took 54.6 min (35925710605) and 56.5 min (35933570910); a warm green run took 49.4 min (35938454860). The gate requires >= ceil(1.5 x the longest complete cold job) = 85, and the scan-plan gate asserts == 90. The synth reclassifies (b) from the swarm's 'infrastructure' to subject defect: the budget is a tracked file of the subject, main fit it (29m48s, run 35315548332), and the subject's own growth (1109 -> 1350 tests) broke it. Classify both in the receipt (scan-plan: pre-existing + generator drift by merge). Candidate: /Users/sac/wt/v26922/v26923/lanes/r2/candidates/r2-gi-depth-timeout.patch (sha256 764e04f4b196354a817b68e807007aeccaa6016c03ce101f06a81aa7c533fd90). Its depth hunk adds a restore comment; the scan-plan requires the verbatim a39921b hunk, so use the verbatim replay plus the timeout hunk. The scan-plan gate requires steps[0] named 'Checkout' with fetch-depth 0 and timeout == 90. Synth witness: r2-gi-timeout.sh exit 1 at d6a6e5b (30 < 85), exit 0 with the candidate; r2-gi-depth.sh exit 1 at 3ed6a7a at the reachability probe and exit 0 at aa07ee7 (72 tests, 0 failures, 61 excluded; swarm witness). Hosted: push the lane branch (the cold run is ~55 min, so poll in bounded steps). The 'Elixir tests' job must not be cancelled and the git-ground-truth describe must show 0 failures. A whole-job green run needs R2-GI-PROBE-ISOLATION and R2-GI-BLOOM too, so it is the post-wave combined witness. Generation path: hand-authored ci.yml (github-actions-pack adoption is successor GC24-CI-gha-pack-adoption; UNSUPPORTED(generator-capability)). Falsifiers: a depth-1 checkout gives 3 BASE_SHA_UNVERIFIED failures; timeout 30 is cancelled at 30m0s. Receipt receipts/v26.9.23/R2-GI-CI.json."}, {"id": "R2-GI-PROBE-ISOLATION", "repo": "ggen_igniter", "after": [], "gate": "sh /Users/sac/wt/v26922/v26923/lanes/r2/gates/r2-gi-probe-isolation.sh \"$PWD\"", "task": "Release defect repair (subject defect; defect_key ggen_igniter-test-orphan-dev-beam; swarm-only). Preflight CI 35925710605 @aa07ee7 (seed 648358): 1349 tests, 1 failure. test/ggen_igniter_plan_task_test.exs:91 '--help / -h byte-identical' got output starting with 'Generated ggen_igniter app'. Cause: test/ggen_igniter_base_mix_task_end_user_test.exs writes lib/tmp_ex4pm_probe_N/application.ex into the shared checkout and runs a dev-env child that compiles it into _build/dev/lib/ggen_igniter/ebin. on_exit removes only the source, so the next dev-env mix child purges the orphan beam and Mix compile.app prints that line into the child's stdout. Fix the source of the staleness, not its victims: after File.rm_rf!(probe_dir), on_exit re-syncs the dev build with `{_out, 0} = System.cmd(\"mix\", [\"compile\"], cd: repo_root, stderr_to_stdout: true)`, plus a comment explaining the orphan beam. Candidate: /Users/sac/wt/v26922/v26923/lanes/r2/candidates/r2-gi-probe-isolation.patch (sha256 6e61bfd4d92e812f3eba224bd922067d744ce7afb5f9bd24913ec935870e9513, +13/-1). Do not weaken the byte-identity or single-JSON-document assertions. Preserved alternative: move the probe into a temp Mix project with path/symlink-shared deps, so lib/ and _build/dev are never touched. The defect has been latent on main since 4aa5f36 (2026-08-31), masked there by the NIF failure. Synth witness (scratch, d6a6e5b): without the fix the gate exits 2 at seed 0 ('10 tests, 1 failure', Jason 'unexpected byte at position 0: 0x47 (\"G\")'); with it the gate exits 0 (4 seeds x '10 tests, 0 failures', lib/ clean). Falsifier: any exact-stdout dev-env child test (plan --help/-h, the --json single-document tests, doctor --json) fails with leading Mix compile chatter at the lane head under any seed, or `git status --porcelain -- lib` is non-empty after the suite. Also run the full suite once at the lane head under the pin with --seed 648358 and record the result. Generation path: hand-authored test, not generator-owned. Receipt receipts/v26.9.23/R2-GI-PROBE-ISOLATION.json (classification subject defect)."}, {"id": "R2-GI-BLOOM", "repo": "ggen_igniter", "after": [], "gate": "sh /Users/sac/wt/v26922/v26923/lanes/r2/gates/r2-gi-bloom.sh \"$PWD\"", "task": "Release defect repair (subject defect; defect_key ggen_igniter-test-bloom-commit-graph; swarm-only; the test entered with V23-B and is absent on main). Preflight CI 35933570910 @f5a2652 (runner git 2.55.0, seed 360415): 1349 tests, 1 failure. test/ggen_igniter_semantic_jira_bootstrap_test.exs:836 'an unreadable current covered commit is reported as such' got covered_commit_status 'observed'. With a changed-path (Bloom) commit-graph, `git log -1 HEAD -- lib/` skips commits that did not touch lib/ without reading their trees, so the fixture's deleted HEAD~1 root tree is invisible (the same test passed in 35925710605, so the failure depends on environment or timing). In setup after git init, pin the fixture repository with core.commitGraph false, maintenance.auto false and gc.auto 0, plus a comment. Add the regression test 'the unreadable corruption stays unreadable when a changed-path commit-graph exists': it runs `git commit-graph write --reachable --changed-paths` explicitly and asserts covered_commit nil and status 'unreadable'. Leave Bootstrap.Git alone: when Bloom filters let git answer, 'observed' is a correct answer, and the defect is in the test premise. Candidate: /Users/sac/wt/v26922/v26923/lanes/r2/candidates/r2-gi-bloom.patch (sha256 9e491d8dccb9137f7931d3e89f3b177ef4501f702ad28c5c70f1493ae084ecb9). Synth witness (scratch, d6a6e5b + candidate, local git 2.51.2): gate exit 0 ('27 tests, 0 failures'); a mutant without the three config lines gives '27 tests, 1 failure' (covered_commit_status 'observed'), so the regression test is not vacuous. The runner-side trigger that writes Bloom filters is UNVERIFIED (the git 2.55 release notes do not state the commitGraph.writeChangedPaths default), and the fix does not depend on it. Falsifier: the regression test passes with the three config lines removed (vacuous court), or :836 or the new test fails on any CI run at the lane head. Generation path: hand-authored test. Receipt receipts/v26.9.23/R2-GI-BLOOM.json (classification subject defect)."}]}
const WAVE = A.wave || 'wave'
const REPO = A.repos || {}
const INT = A.ints || {}
const BASE = A.base_branch || 'friday/gc-fri-0800'
const WT = A.worktree_root || '/Users/sac/wt/v26922/v23'
const PREFIX = A.branch_prefix || 'v23'
const RDIR = A.receipts_dir || 'receipts/v26.9.23'
const MAXREP = typeof A.max_repairs === 'number' ? A.max_repairs : 2
const CONTEXT = A.context || ''
const LANES = A.lanes || []
const lockPath = (repo) => `${INT[repo]}.merge.lock`

const DOCTRINE = `Binding for this stage (the ~/.claude/rules files are already loaded; do not re-read them):
- Read /Users/sac/wt/v26922/v26923/DRIVER.md (driver, gate map, PVOCAB) and /Users/sac/wt/v26922/COORDINATION.md
  (merge lock, conservation rules, reserved files). The accepted product contract is
  /Users/sac/wt/v26922/v26923/prd-ard.md (PRD + ARD for v26.9.23); cite its section ids (PR-0xx, AR-0xx, §n) in commits.
- Work ONLY in your own worktree. Never edit ${Object.values(INT).join(' or ')} except in the Integrate stage, and never
  edit any other executor's worktree (/Users/sac/wt/v26922/<repo>/int, wo*, law-*, fri/FRI-*, v23/<other lane>).
- Generation-first: extend the ontology/pack/template/generator before hand-writing; hand-written residue gets a
  HANDWRITTEN.md ledger row (UNSUPPORTED(generator-capability) + reason). Chicago tests only: real git repos in tmp dirs,
  real processes, the repo's real DB test setup; no mocks, no monkeypatch.
- git: commit with -F <message file>; never rebase, force, reset --hard, or -X ours/theirs; fetch with --no-prune.
- Receipt: ${RDIR}/<LANE>.json in the fleet R schema, validated by python3 ~/.claude/dfcm/validate_receipt.py (must
  print ADMITTED). Standing words: ALIVE only for an observed run on the exact committed subject; otherwise
  PARTIAL_ALIVE/UNKNOWN/BLOCKED/UNSUPPORTED/REFUSED with a broken_term.
- No LLM, network model API, or zcode binary on any executed product path (the LLM edge is only candidate extraction
  from prose, and it is recorded as such).
- Disk: check df -g /Users/sac before every compile/test/clone. Below 10 GB free: run /Users/sac/.oclnr/bin/oclnr snapshot
  thin --bytes 20GB (receipted), then wait (sleep 60, up to 20 min) for space before continuing; an ENOSPC failure is an
  environment failure to report, never a code verdict. Never rm -rf outside your own scratch dirs. Prefer APFS clones
  (cp -c) of existing _build/deps over fresh builds. Load is shared with other executors: no -j over-subscription.
- Keep every single shell command under ~20 min: run long suites as separate commands with output to a scratch log,
  never one compound gate with a 40-minute timeout (two agents went silent for 60-90 min after such calls).
- Report only real command output (cmd => exit, one-line summary). Distinguish pre-existing failures from new ones.
${CONTEXT}`

const BUILD = { type: 'object', properties: {
  lane: { type: 'string' }, worktree: { type: 'string' }, branch: { type: 'string' }, base_sha: { type: 'string' },
  head_sha: { type: 'string' }, standing: { type: 'string' },
  files_changed: { type: 'array', items: { type: 'string' } },
  commands: { type: 'array', items: { type: 'string' }, description: 'cmd => exit, summary' },
  receipt_path: { type: 'string' }, receipt_validator_output: { type: 'string' },
  blocked_reason: { type: 'string', description: 'set only when the lane cannot proceed (with broken_term)' },
  notes: { type: 'string' },
}, required: ['lane', 'worktree', 'branch', 'head_sha', 'standing', 'commands'] }
const VERDICT = { type: 'object', properties: {
  lane: { type: 'string' }, lens: { type: 'string' }, verdict: { type: 'string', enum: ['pass', 'refuted'] },
  reasons: { type: 'array', items: { type: 'string' } }, commands: { type: 'array', items: { type: 'string' } },
  broken_term: { type: 'string' },
}, required: ['lane', 'lens', 'verdict', 'reasons', 'commands'] }
const INTEG = { type: 'object', properties: {
  lane: { type: 'string' }, merged: { type: 'boolean' }, int_head: { type: 'string' },
  conflicts: { type: 'array', items: { type: 'string' } }, post_merge: { type: 'array', items: { type: 'string' } },
  reason: { type: 'string' },
}, required: ['lane', 'merged', 'post_merge'] }

const wtOf = (L) => L.worktree || `${WT}/${L.id}`
const scratchOf = (L) => `/private/tmp/claude-501/v23-scratch/${WAVE}-${L.id}`
const build = (L) => agent(`Target repo: ${REPO[L.repo]}. Lane ${L.id} of wave ${WAVE}.
${L.worktree
  ? `Worktree: continue in the EXISTING lane worktree ${L.worktree} (branch ${L.branch}); it is yours for this lane (the
"never edit fri/FRI-*" rule does not apply to it). Do not create another worktree. cd ${L.worktree} && pwd && git branch --show-current && git rev-parse HEAD (record base_sha = merge-base with ${BASE}).`
  : `Worktree: if ${wtOf(L)} already exists, cd into it and continue from its committed state (a prior run of this lane);
otherwise: cd ${REPO[L.repo]} && git worktree add -b ${PREFIX}/${L.id} ${wtOf(L)} ${L.from || BASE}. Provision deps/_build by
APFS clone (cp -cR deps _build from ${INT[L.repo]} when mix.lock is identical) instead of a fresh fetch+compile. Then
cd ${wtOf(L)} && pwd && git branch --show-current && git rev-parse HEAD (record base_sha = merge-base with ${BASE}).`}
Scratch: use ONLY ${scratchOf(L)} (mkdir -p it) for temp files, logs and clones; never cite another lane's scratch output
as evidence (a receipt was refuted for quoting a shared scratch file from another tree). Remove your scratch clones when done.
${DOCTRINE}
Task (${L.id}): ${L.task}
Lane gate (run it on the committed head, paste exits): ${L.gate}
Write and validate ${RDIR}/${L.id}.json, commit with -F. If a real dependency is missing (e.g. a predecessor lane is not
merged into ${BASE}), stop, set blocked_reason with broken_term, and return. Return the structured result.`,
  { label: `${WAVE}:build:${L.id}`, phase: 'Build', schema: BUILD })

const court = (L, b, round) => parallel([
  () => agent(`Target: worktree ${b.worktree} (repo ${REPO[L.repo]}), head ${b.head_sha}. cd there && pwd && git rev-parse HEAD && git status --porcelain.
${DOCTRINE}
Lens GATE for ${L.id}: re-run the lane gate yourself (${L.gate}) and every command the builder claims
(${JSON.stringify(b.commands || []).slice(0, 3000)}); validate the receipt ${b.receipt_path || '(missing)'}.
Refute on any failing command, a claim that does not match real output, an unvalidated receipt, or a dirty tree. Do not edit or commit.`,
    { label: `${WAVE}:gate${round}:${L.id}`, phase: 'Court', schema: VERDICT }),
  () => agent(`Target: repo ${REPO[L.repo]}. cd ${REPO[L.repo]} && pwd.
${DOCTRINE}
Lens REVERT-MUTATION for ${L.id}: git worktree add --detach /tmp/v23-mut-${L.id}-r${round} ${b.head_sha}; in it restore every
NON-TEST source file changed since ${b.base_sha} to its ${b.base_sha} content (keep test files and fixtures); run the lane's
tests (${L.gate}). This lens passes only if the lane's new tests FAIL on the mutated subject for the reason the change
exists (not only UndefinedFunction noise: name which assertions fail). If they still pass -> refuted, broken_term
admission_vacuous. Finally remove your scratch worktree with git worktree remove --force (it is yours).`,
    { label: `${WAVE}:mut${round}:${L.id}`, phase: 'Court', schema: VERDICT }),
  () => agent(`Target: worktree ${b.worktree}. cd there && pwd. Read-only.
${DOCTRINE}
Lens DOCTRINE for ${L.id}: read git diff ${b.base_sha}..${b.head_sha}. Refute for: mocks or monkeypatching; weakened,
skipped or deleted tests; deviations from the vocabulary contracts in DRIVER.md (IRIs, field names, digest rules);
edits outside the lane's scope or to another lane's reserved files; hand-written code where a generator exists without a
HANDWRITTEN row; any LLM/model call on an executed product path; swallowed errors (rescue/catch without typed return,
rethrow or log); receipts that overclaim ALIVE; requirements of the task left unimplemented while claimed done.`,
    { label: `${WAVE}:doc${round}:${L.id}`, phase: 'Court', schema: VERDICT, agentType: 'Explore' }),
])
const bad = (vs) => vs.some(v => !v || v.verdict !== 'pass')

const chains = {}
const serial = (repo, fn) => {
  const prev = chains[repo] || Promise.resolve()
  const p = prev.then(fn, fn)
  chains[repo] = p.catch(() => null)
  return p
}

const integrate = (L, b) => serial(L.repo, () => agent(`Target: critical-path integration worktree ${INT[L.repo]} (branch ${BASE}).
${DOCTRINE}
Integrate ${b.branch} (${b.head_sha}) for lane ${L.id}:
1. Lock (shared with other executors): until mkdir ${lockPath(L.repo)} 2>/dev/null; do sleep 15; done;
   echo "claude:${WAVE}:${L.id}" > ${lockPath(L.repo)}/owner. ALWAYS release at the end (rm owner; rmdir), also on failure.
2. cd ${INT[L.repo]} && pwd && git branch --show-current && git status --porcelain (untracked files that belong to another
   lane's receipt dir are not yours: leave them; tracked modifications you did not make -> stop, release, merged=false).
3. git merge --no-ff ${b.branch} -F <msgfile>. Conflicts: read both sides and keep both contents (append-only ledgers keep
   every row); never take one side wholesale.
4. Post-merge: run the lane gate (${L.gate}) in ${INT[L.repo]}. If the merge breaks it and one small fix-forward commit
   cannot repair it, git revert -m 1 the merge and report merged=false with the failing output.
5. Append one JSON line to /Users/sac/wt/v26922/transitions.jsonl:
   {"wo":"${L.id}","repo":"${L.repo}","executor":"claude","to":"<standing>","subject_sha":"<int HEAD>","receipt":"${RDIR}/${L.id}.json","wave":"${WAVE}"}
6. Release the lock.`, { label: `${WAVE}:int:${L.id}`, phase: 'Integrate', schema: INTEG }))

const lane = async (L) => {
  let b = await build(L)
  if (!b) return { lane: L.id, status: 'build-null' }
  if (b.blocked_reason) return { lane: L.id, status: 'blocked', build: b }
  let q = await court(L, b, 1)
  let round = 1
  while (bad(q) && round <= MAXREP) {
    const r = await agent(`Target: worktree ${b.worktree}. cd there && pwd && git branch --show-current && git rev-parse HEAD.
${DOCTRINE}
Repair round ${round} for lane ${L.id}. Task: ${L.task.slice(0, 1500)}
Court verdicts to answer: ${JSON.stringify(q).slice(0, 9000)}
Fix with NEW commits (never rewrite). Rerun the lane gate (${L.gate}); refresh and validate ${RDIR}/${L.id}.json; commit -F.
If a refutation is wrong, include the disproving command output in notes instead of changing code.`,
      { label: `${WAVE}:repair${round}:${L.id}`, phase: 'Repair', schema: BUILD })
    if (r) b = r
    round += 1
    q = await court(L, b, round)
  }
  if (bad(q)) return { lane: L.id, status: 'refuted', build: b, court: q }
  const m = await integrate(L, b)
  return { lane: L.id, status: m && m.merged ? 'merged' : 'unmerged', build: b, court: q, integrate: m }
}

const byId = {}
LANES.forEach(L => { byId[L.id] = L })
const memo = {}
const run = (L) => {
  if (!memo[L.id]) {
    memo[L.id] = (async () => {
      const deps = await Promise.all((L.after || []).filter(d => byId[d]).map(d => run(byId[d])))
      const failed = deps.filter(d => !d || d.status !== 'merged').map(d => (d && d.lane) || '?')
      if (failed.length) {
        log(`${L.id}: not started, dependencies not merged: ${failed.join(', ')}`)
        return { lane: L.id, status: 'blocked-dep', deps: failed }
      }
      try { return await lane(L) } catch (e) { return { lane: L.id, status: 'error', error: String(e) } }
    })()
  }
  return memo[L.id]
}

log(`${WAVE}: ${LANES.length} lanes: ${LANES.map(L => L.id + (L.after && L.after.length ? '<-' + L.after.join('+') : '')).join(', ')}`)
const results = await Promise.all(LANES.map(run))
return {
  wave: WAVE,
  summary: results.map(r => ({ lane: r.lane, status: r.status, head: r.build && r.build.head_sha, int_head: r.integrate && r.integrate.int_head })),
  results,
}
