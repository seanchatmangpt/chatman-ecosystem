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
const A = (args && args.wave) ? args : {"wave": "R1a", "repos": {"xaas": "/Users/sac/xaas", "ggen_igniter": "/Users/sac/ggen_igniter"}, "ints": {"xaas": "/Users/sac/wt/v26922/fri/xaas-int", "ggen_igniter": "/Users/sac/wt/v26922/fri/ggen_igniter-int"}, "base_branch": "friday/gc-fri-0800", "worktree_root": "/Users/sac/wt/v26922/v23", "branch_prefix": "v23", "receipts_dir": "receipts/v26.9.23", "max_repairs": 2, "context": "v26.9.23 contracts for this wave (also in DRIVER.md):\n- Governing graph: xaas docs/sjira/v26.9.23/goal.ttl. Instance prefix v23: = https://ggen-igniter.dev/sjira/v26.9.23# .\n  Root v23:GC-26.9.23 (dcterms:identifier \"GC-26.9.23\", sj:successorOf fri:GC-FRI-0800 from docs/sjira/v26.9.22/friday/goal.ttl),\n  gates v23:GC23-0 ... v23:GC23-12 (dcterms:identifier \"GC23-<n>\"), successor bucket v23:GC-26.9.24 (stopQuery ASK { FILTER(false) }).\n- Court scripts: every gate's sj:courtCommand is exactly \"sh docs/sjira/v26.9.23/courts/GC23-<n>.sh\" run from the xaas root.\n  Env available to courts: XAAS_DIR (xaas checkout under judgement, default: the cwd), GGEN_IGNITER_DIR (ggen_igniter checkout\n  under judgement, default /Users/sac/wt/v26922/fri/ggen_igniter-int). A court whose machinery has not landed prints\n  \"UNKNOWN: <gate> machinery lands in lane <LANE>\" and exits with the code the stop-court runner maps to UNKNOWN\n  (read lib/mix/tasks/xaas.stop_court.ex for the exit->standing mapping; add a distinct UNKNOWN code there if none exists).\n  Machinery lanes later replace their gate's script body; goal.ttl stays stable.\n- The accepted prose: /Users/sac/wt/v26922/v26923/prd-ard.md is committed byte-identical as docs/sjira/v26.9.23/prd-ard.md\n  (sha256:7c8797b2bc9130fc4c8fce9138cc8140cb704e0633715807398451c660658212, 39386 bytes; do not edit the prose).\n- PVOCAB (proposition vocabulary) is in DRIVER.md; use it verbatim.\n- xaas lane gate prefix: mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors.\n- Cross-repo chain for episodes: courts and episode runners resolve the ggen_igniter checkout from GGEN_IGNITER_DIR. A lane that\n  needs ggen_igniter code not yet merged into ggen_igniter-int creates its OWN detached ggen_igniter worktree\n  (git -C /Users/sac/ggen_igniter worktree add --detach /Users/sac/wt/v26922/v23/<LANE>-gi <sha>) and points GGEN_IGNITER_DIR at it\n  for development; its final gate run and court scripts must work against GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int.\n- Reference KNOWN class: format-drift repair (capability recipe:mix-format, suite ggen-igniter-format, provider recipe,\n  executor recipe-worker). Episode subjects are ggen_igniter commits that introduce format drift deterministically in a\n  dedicated episode branch (v23/episode-<name>), never on friday/gc-fri-0800 or main.\n- No-LLM court env (F3): no ANTHROPIC_*, CLAUDE_*, OPENAI_*, ZAI_*, Z_AI_*, GLM_*, ZCODE_* variables; no zcode/claude binary on PATH;\n  HOME a fresh mktemp dir; MIX_HOME/HEX_HOME/database URL passed explicitly as durable configuration (not credentials).\n  A court run with any LLM credential variable set must be refused with a typed REFUSED(llm_credential_present) and\n  broken_term mu_on_O.\n- OCEL: ARD §13 event classes (WorkOrderCreated, CapabilityResolved, LeaseAcquired, ActuationStarted, ActuationCompleted,\n  VerificationCompleted, ReceiptSealed, StandingChanged, FrontierChanged, MachineExperienceAdmitted) and object types;\n  validate with the existing mix xaas.ocel_validate and pm4py (python3, pm4py 2.7.22 is installed).\n- Court script ownership: the lane that lands a gate's machinery replaces that gate's docs/sjira/v26.9.23/courts/GC23-<n>.sh\n  body (keep the path and the exit-code contract from V23-P). ggen_igniter lanes cannot edit xaas: lane V23-K does that.\n- Canonical capabilityId value space (one pattern for every lane; FRI-T2/FRI-T4 already use it):\n  ^[a-z0-9][a-z0-9_.-]*:[a-z0-9][a-z0-9_.:-]*$ . sj:exclusion is 0..n everywhere (absent = empty list), never 1..n.\n  Any shape, template or regex that deviates is aligned to these in the lane that touches it (V23-C owns the pack shapes).\n- RELEASE DEFECT REPAIR (operator release sequence, frozen subjects): only the named defect may change; no successor work. Classify the\n  failure (subject defect | environment | pre-existing | generator drift | evidence defect | infrastructure) in the receipt.\n- TOOLCHAIN PIN: run every mix/elixir command under the repo's .tool-versions pin, not the ambient /opt/homebrew mix:\n  xaas: PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH\n  ggen_igniter: PATH=/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin:/Users/sac/.asdf/installs/erlang/27.2.4/bin:$PATH\n  Verify with `elixir --version` first; compile --force under the pin (a _build from another OTP must not be reused: use a fresh _build\n  in your worktree, cloning only deps/). Record the toolchain in the receipt.\n- Evidence: the release qualification that found these defects is /Users/sac/wt/v26922/v26923/receipts/fleet/xaas-e999e62b63c680517b9a562cef877d8b09b0cfdd.json\n  and its .logs/ dir (defects F1..F5).", "lanes": [{"id": "R1-GI-FMT", "repo": "ggen_igniter", "after": [], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin:/Users/sac/.asdf/installs/erlang/27.2.4/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && mix compile --warnings-as-errors --force && mix test test/ggen_igniter_semantic_jira_bootstrap_test.exs'", "task": "Release defect F3/F4 (subject defect, entered with V23-B): lib/ggen_igniter/semantic_jira/bootstrap.ex is not formatted under ggen_igniter's pinned Elixir 1.18.4-otp-27, so the recipe provider (which formats the target under that pin) rewrites it and xaas semantic_drive_test.exs:107/:345 fail. A candidate exists on local branch rela/gi-bootstrap-fmt-pin (ccb01f6; its revert-mutation control rela/gi-bootstrap-fmt-revert-mutation 4086532 fails the drive tests again). Do: on a branch off friday/gc-fri-0800, run mix format under the pin for the whole repo (not only bootstrap.ex) and commit exactly the formatter's output (never hand-format); prove `mix format --check-formatted` exits 0 under the pin AND under ambient 1.19.5 (report both); run the xaas drive tests against this ggen_igniter subject: cd /Users/sac/wt/v26922/fri/xaas-int is frozen and read-only for you, so use a detached xaas worktree at its HEAD and GGEN_IGNITER_DIR=<your worktree> with the xaas pin to run test/xaas/ultracode/semantic_drive_test.exs (expect 0 failures) and show the revert-mutation control. Receipt receipts/v26.9.23/R1-GI-FMT.json (no goal.ttl order)."}, {"id": "R1-X-LOCK", "repo": "xaas", "after": [], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && mix test test/xaas/zcode_plugin'", "task": "Release defect F1 (generator drift, pre-existing on origin/main): test/xaas/zcode_plugin/projection_test.exs:31 fails because `ggen sync run` exits 1 with FM-PACK-008 — the zcode_plugin pack content hash does not match ggen.lock (merge 068c1d2 edited packs/zcode-plugin-pack/templates/plugin.json.tmpl without re-locking). Repair through the generator only: re-lock/regenerate with the ggen command the projection test uses (read the test to find the exact ggen invocation and binary; record `ggen --version`), commit exactly the generator's output (ggen.lock and any regenerated projections), never hand-edit the lock or projections. If regeneration changes a projection's content, show the diff and explain it from the template change in 068c1d2. Gate includes the zcode_plugin tests. Receipt receipts/v26.9.23/R1-X-LOCK.json."}, {"id": "R1-X-PGREP", "repo": "xaas", "after": [], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && mix test test/xaas/ultracode/dispatch_test.exs'", "task": "Release defect F5 (environment-dependent test, pre-existing): test/xaas/ultracode/dispatch_test.exs:600 checks for surviving processes with a machine-wide `pgrep -f \"zcode.js --prompt\"`, which matches unrelated live ZCode dispatches on this machine (e.g. a long-running mix xaas.ultracode.start in /Users/sac/xaas). Scope the check to what the test itself spawned (its own OS pids / process group recorded at spawn), keeping the assertion's intent (no orphan survives the test). Chicago: prove the fixed test passes while an unrelated `zcode.js --prompt`-named process is running (start a harmless real process with that argv in the test setup or in your gate run, e.g. a sleep via exec -a), and fails when the test's own child is deliberately left alive (mutation). Receipt receipts/v26.9.23/R1-X-PGREP.json."}, {"id": "R1-X-DIGEST", "repo": "xaas", "after": ["R1-GI-FMT"], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int mix test test/xaas/ultracode'", "task": "Release defect F2 (cross-repo contract drift in the release pair, subject defect): test/xaas/ultracode/semantic_jira_e2e_test.exs:148 fails — the SJ-001 snapshot digest xaas computes differs from ggen_igniter's. Cause: ggen_igniter 33c8e86 (FRI-T6, merged via V23-T6R) embeds definition_digest in the admitted snapshot and computes the definition digest over a closed 18-field whitelist; xaas AdmissionBinding still drops fields and does not drop definition_digest. A probe (local branch rela/xaas-sj001-digest-probe ea17922) fixed SJ-001 but broke 7 SemanticWork/SemanticWorkFalsifier tests whose committed descriptors carry the pre-33c8e86 digest. Repair: make the digest form an explicit, versioned part of the contract (the descriptor/snapshot declares its producer digest form; xaas admission computes and checks exactly that form; the pre-33c8e86 form stays verifiable only where a committed historical artifact declares it, never inferred); regenerate every committed descriptor/snapshot fixture that should carry the current form by RUNNING the producer (mix semantic_jira.descriptor / the ggen_igniter tasks in GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int) — never hand-edit digests; if a fixture intentionally pins the legacy form, it must declare it. Prove: SJ-001 e2e passes, the 7 SemanticWork tests pass, a descriptor whose declared form mismatches its digest is REFUSED (typed), and the episode courts GC23-4..8 still pass (run the court scripts). Receipt receipts/v26.9.23/R1-X-DIGEST.json."}, {"id": "R1-X-GUARD", "repo": "xaas", "after": [], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && mix test test/xaas/ultracode/semantic_drive_test.exs && GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int sh docs/sjira/v26.9.23/courts/GC23-5.sh'", "task": "Required_23 (falsifies ARD F3 / GC23-5 as stated: 'expose LLM credentials during the KNOWN no-LLM court -> typed refusal'). Driver-verified defect: Xaas.Ultracode.SemanticDrive.no_llm_guard(%{\"GEMINI_API_KEY\"=>\"x\",\"OPENROUTER_API_KEY\"=>\"y\",\"PATH\"=>\"/usr/bin\"}) returns :ok while ANTHROPIC_API_KEY is refused, because the guard is a hard-coded denylist (@llm_prefixes ANTHROPIC_ CLAUDE_ OPENAI_ ZAI_ Z_AI_ GLM_ ZCODE_; @llm_binaries zcode claude). Make the guard fail closed: (1) the permitted environment of the no-LLM court is an ALLOWLIST of variable names (the durable configuration no_llm_env.sh passes: HOME, PATH, MIX_HOME, HEX_HOME, ASDF_DATA_DIR, MIX_ENV, MIX_TEST_PARTITION, DEV_DB_*, LANG, plus variables the drive itself sets) and any other variable is refused as REFUSED(llm_credential_present or unadmitted_environment) naming only the variable NAME; (2) the known-provider list (Anthropic, OpenAI, Google/Gemini, Mistral, Groq, OpenRouter, DeepSeek, xAI, Cohere, Together, Fireworks, Perplexity, Azure OpenAI, AWS Bedrock, Ollama, Z.AI/GLM, ZCode, Claude Code; env prefixes and CLI binaries such as claude, zcode, ollama, llm, aider, gemini, codex) is declared as DATA (a TTL or JSON under docs/sjira/v26.9.23/ or priv/, generated into code via the repo's generator path if one exists, else read at runtime) and used for reporting which provider leaked; (3) keep no_llm_env.sh and the guard in agreement (one source for the allowlist). Chicago tests: every provider in the list refused (table-driven from the data file), an arbitrary unknown variable refused, the allowlisted environment passes, ANTHROPIC still refused; extend GC23-5.sh's F3 step to prove a non-Anthropic credential (e.g. GEMINI_API_KEY=x) is refused too. Receipt receipts/v26.9.23/R1-X-GUARD.json."}, {"id": "R1-X-COURTS", "repo": "xaas", "after": [], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int sh docs/sjira/v26.9.23/courts/GC23-4.sh && GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int sh docs/sjira/v26.9.23/courts/GC23-7.sh'", "task": "Required_23, two court anti-vacuity defects confirmed by the CE23-12 MSA scan (evidence /private/tmp/claude-501/v23-scratch/BENCH-MSA/p3/): (a) GC23-4 (ARD §8: the digest is checked sJira -> SA2A -> XaaS -> provider -> receipt): SemanticDrive.verify_hops/1 accepts a hops.json forged consistently at every hop (p3/hops-allforged.json), because nothing anchors hop 0 to the admitted order. Fix: the GC23-4 court (and verify_hops, if it is the court's engine) recomputes the sJira-hop request/tuple digest from the committed admitted work graph (docs/sjira/v26.9.23/episodes/fmt-1/work.json through the ggen_igniter descriptor path in GGEN_IGNITER_DIR) and refuses unless it equals every recorded hop; (b) GC23-7 ('the episode produces conformant durable evidence'): 4 of 7 court-owned receipt mutants escape every court (acceptance false with standing ALIVE; commit not the subject; files outside the order's path scope; replay command 'true'). Fix: GC23-7 (or Xaas.Receipt.RProjection.seal/1 if that is the court's engine) refuses internal inconsistency: ALIVE requires acceptance true, consequence.commits ⊆ the subject's commits, files_changed within the order's sj:pathScope, and every replay command equal to the court-recorded command that produced the evidence (never a trivial command). Chicago tests + run both court scripts on the real fmt-1 artifacts (ALIVE) and on each mutant copy (refused, typed). Receipt receipts/v26.9.23/R1-X-COURTS.json."}, {"id": "R1-X-FENCE", "repo": "xaas", "after": [], "gate": "python3 -c \"import yaml,sys; d=yaml.safe_load(open('.github/workflows/ci_cd.yaml')); [print(j, d['jobs'][j].get('if')) for j in ('publish-image','deploy')]\" && sh -c '! grep -nE \"^    if: github.event_name == .push. && github.ref == .refs/heads/main.$\" .github/workflows/ci_cd.yaml'", "task": "Required_23 (authority + CE23-8 UNRECEIPTED_ACTUATION=0): in .github/workflows/ci_cd.yaml the jobs publish-image (GHCR push, line ~307) and deploy (line ~408) run on `github.event_name == 'push' && github.ref == 'refs/heads/main'`, so merging the v26.9.23 release PR into main would publish an image and deploy without operator action — registry publishes are outside the approved authority. Fence both jobs so they run only on an explicit workflow_dispatch whose input names the expected head sha (e.g. inputs.expected_head_sha == github.sha) — or move them behind the repo's existing receipted deploy pattern if one exists (check .github/workflows/fly_deploy.yaml). Do not delete the jobs; do not change any other job. Show with a YAML parse that on push-to-main neither job's condition can be true. Record in HANDWRITTEN.md if workflow YAML is hand-owned. Receipt receipts/v26.9.23/R1-X-FENCE.json."}, {"id": "R1-X-PIN", "repo": "xaas", "after": ["R1-X-GUARD", "R1-X-COURTS", "R1-X-FENCE", "R1-X-LOCK", "R1-X-PGREP", "R1-X-DIGEST"], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int mix test'", "task": "Required_23 (GC23-11 exact-head qualification under the repo's .tool-versions pin, and exact-head CI which uses the same pin): after the other R1a lanes merged, make xaas compile with --warnings-as-errors and pass its FULL test suite under Elixir 1.20.2-otp-28 / Erlang 28.5.0.2 (a fresh _build compiled under the pin). Fix only what the pinned run reports, classifying each (subject defect | environment | pre-existing | generator drift | evidence defect | infrastructure). Known candidates reported by the CI scanner (verify, do not assume): `require Ash.Query` unused at lib/xaas/ultracode/semantic_drive.ex:78 fails --warnings-as-errors under 1.20.2; SemanticDrive.build_manifest/2 (:593-628) matches only the vsn-1 Mix manifest shape {1,{elixir,otp},scm} while 1.20 writes {2,{elixir,otp},scm,lock}; unreachable `nil -> []` branches at machine_experience.ex:539 and :1235 (dialyzer); test/xaas/receipt/r_projection_test.exs lacks the validator-absent skip guard its sibling test has. Also run the full suite a second time to catch order-dependent failures. Generated files are fixed only through their generator. Receipt receipts/v26.9.23/R1-X-PIN.json with the full-suite result under the pin."}, {"id": "R1-GI-PIN", "repo": "ggen_igniter", "after": ["R1-GI-FMT"], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin:/Users/sac/.asdf/installs/erlang/27.2.4/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && mix compile --warnings-as-errors --force && mix credo && mix test'", "task": "Required_23 (GC23-11 exact-head qualification under ggen_igniter's .tool-versions pin, Elixir 1.18.4-otp-27 / Erlang 27.2.4, which CI uses): the release qualification passed only under the ambient Elixir 1.19.5/OTP 28.3.1. After R1-GI-FMT merged, run the full gate under the pin with a FRESH _build compiled under the pin (a prior note: the pinned Erlang 27.2.4 crashed on beams compiled under OTP 28 — never reuse an OTP-28 _build; also rebuild the Rustler NIF under the pin if the test build requires it). Fix only what the pinned run reports, classifying each failure (subject defect | environment | pre-existing | generator drift | evidence defect | infrastructure); generated files only through their generator. Known pre-existing, NOT to fix here (successor): kernel_differential_test rewrites the tracked report receipts/v26.9.22/kernel-differential.json — restore it after the run and note it. Receipt receipts/v26.9.23/R1-GI-PIN.json with the full-suite result under the pin."}]}
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
