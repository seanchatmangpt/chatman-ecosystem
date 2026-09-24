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
const A = (args && args.wave) ? args : {"wave": "S", "repos": {"xaas": "/Users/sac/xaas", "ggen_igniter": "/Users/sac/ggen_igniter"}, "ints": {"xaas": "/Users/sac/wt/v26922/fri/xaas-int", "ggen_igniter": "/Users/sac/wt/v26922/fri/ggen_igniter-int"}, "base_branch": "friday/gc-fri-0800", "worktree_root": "/Users/sac/wt/v26922/v23", "branch_prefix": "v23", "receipts_dir": "receipts/v26.9.23", "max_repairs": 2, "context": "v26.9.23 contracts for this wave (also in DRIVER.md):\n- Governing graph: xaas docs/sjira/v26.9.23/goal.ttl. Instance prefix v23: = https://ggen-igniter.dev/sjira/v26.9.23# .\n  Root v23:GC-26.9.23 (dcterms:identifier \"GC-26.9.23\", sj:successorOf fri:GC-FRI-0800 from docs/sjira/v26.9.22/friday/goal.ttl),\n  gates v23:GC23-0 ... v23:GC23-12 (dcterms:identifier \"GC23-<n>\"), successor bucket v23:GC-26.9.24 (stopQuery ASK { FILTER(false) }).\n- Court scripts: every gate's sj:courtCommand is exactly \"sh docs/sjira/v26.9.23/courts/GC23-<n>.sh\" run from the xaas root.\n  Env available to courts: XAAS_DIR (xaas checkout under judgement, default: the cwd), GGEN_IGNITER_DIR (ggen_igniter checkout\n  under judgement, default /Users/sac/wt/v26922/fri/ggen_igniter-int). A court whose machinery has not landed prints\n  \"UNKNOWN: <gate> machinery lands in lane <LANE>\" and exits with the code the stop-court runner maps to UNKNOWN\n  (read lib/mix/tasks/xaas.stop_court.ex for the exit->standing mapping; add a distinct UNKNOWN code there if none exists).\n  Machinery lanes later replace their gate's script body; goal.ttl stays stable.\n- The accepted prose: /Users/sac/wt/v26922/v26923/prd-ard.md is committed byte-identical as docs/sjira/v26.9.23/prd-ard.md\n  (sha256:7c8797b2bc9130fc4c8fce9138cc8140cb704e0633715807398451c660658212, 39386 bytes; do not edit the prose).\n- PVOCAB (proposition vocabulary) is in DRIVER.md; use it verbatim.\n- xaas lane gate prefix: mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors.\n- Cross-repo chain for episodes: courts and episode runners resolve the ggen_igniter checkout from GGEN_IGNITER_DIR. A lane that\n  needs ggen_igniter code not yet merged into ggen_igniter-int creates its OWN detached ggen_igniter worktree\n  (git -C /Users/sac/ggen_igniter worktree add --detach /Users/sac/wt/v26922/v23/<LANE>-gi <sha>) and points GGEN_IGNITER_DIR at it\n  for development; its final gate run and court scripts must work against GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int.\n- Reference KNOWN class: format-drift repair (capability recipe:mix-format, suite ggen-igniter-format, provider recipe,\n  executor recipe-worker). Episode subjects are ggen_igniter commits that introduce format drift deterministically in a\n  dedicated episode branch (v23/episode-<name>), never on friday/gc-fri-0800 or main.\n- No-LLM court env (F3): no ANTHROPIC_*, CLAUDE_*, OPENAI_*, ZAI_*, Z_AI_*, GLM_*, ZCODE_* variables; no zcode/claude binary on PATH;\n  HOME a fresh mktemp dir; MIX_HOME/HEX_HOME/database URL passed explicitly as durable configuration (not credentials).\n  A court run with any LLM credential variable set must be refused with a typed REFUSED(llm_credential_present) and\n  broken_term mu_on_O.\n- OCEL: ARD §13 event classes (WorkOrderCreated, CapabilityResolved, LeaseAcquired, ActuationStarted, ActuationCompleted,\n  VerificationCompleted, ReceiptSealed, StandingChanged, FrontierChanged, MachineExperienceAdmitted) and object types;\n  validate with the existing mix xaas.ocel_validate and pm4py (python3, pm4py 2.7.22 is installed).\n- Court script ownership: the lane that lands a gate's machinery replaces that gate's docs/sjira/v26.9.23/courts/GC23-<n>.sh\n  body (keep the path and the exit-code contract from V23-P). ggen_igniter lanes cannot edit xaas: lane V23-K does that.\n- Canonical capabilityId value space (one pattern for every lane; FRI-T2/FRI-T4 already use it):\n  ^[a-z0-9][a-z0-9_.-]*:[a-z0-9][a-z0-9_.:-]*$ . sj:exclusion is 0..n everywhere (absent = empty list), never 1..n.\n  Any shape, template or regex that deviates is aligned to these in the lane that touches it (V23-C owns the pack shapes).", "lanes": [{"id": "V23-S", "repo": "xaas", "after": [], "gate": "mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && mix test test/mix/tasks/xaas_stop_court_test.exs test/sjira/v26_9_23_goal_test.exs", "task": "Release evidence defect (operator release sequence step 3: 'Receipts must bind exact subject SHA, graph digest, verifier/toolchain identity and replay command'; step 5 requires derived counters). Today the gate receipts written by lib/mix/tasks/xaas.stop_court.ex carry subject_sha and graph_hash but no verifier or toolchain identity, record the repo as an absolute worktree path, and the STOP receipt carries no release counters. Change the stop court (no other surface) so that every gate receipt and the STOP receipt carry: identity.repo as the GitHub slug (seanchatmangpt/xaas) with the observed worktree path in a separate field; verifier = {runner: 'mix xaas.stop_court', court_command, court_script_sha256 (sha256 of the court script file at the subject), validator_sha256 (python3 ~/.claude/dfcm/validate_receipt.py), schema_sha256 (~/.claude/dfcm/receipt.schema.json), stop_query_sha256}; toolchain = {elixir: System.version(), otp_release, erts_version, python3 version string}; replay.commands with the exact reproducible invocation including env (MIX_ENV=test, GGEN_IGNITER_DIR, GC23_FLEET_RECEIPTS_DIR) and --only <gate>. The STOP receipt additionally derives (never asserts) the ARD §27 counters from observed evidence, each with its source named: REQUIRED_UNKNOWN (required gates or orders not in a terminal standing), UNCLASSIFIED_REQUIRED_WORK (from the GC23-11 court's check-classification result), REQUIRED_LLM_KNOWN and LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH (LLM-provider events in the fmt-1 and me-2 episode OCEL under docs/sjira/v26.9.23/episodes/, counted by the same rule GC23-5/GC23-9 courts use), UNRECEIPTED_ACTUATION (episode ledger actuations without a sealed receipt); a counter whose source cannot be read is null with a reason, never 0. Tests (Chicago, real files, real validator): a gate receipt contains every new field with values recomputed in the test (sha256 of the real court script, System.version()); a court script edited after the run changes court_script_sha256; the counters of a tmp episode with one injected LLM-provider event give LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH=1; unreadable OCEL gives null with reason. Keep GC-FRI-0800 behaviour and every existing test. Receipt receipts/v26.9.23/V23-S.json (no goal.ttl order for this lane: do not set a tuple digest)."}]}
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
