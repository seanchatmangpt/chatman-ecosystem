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
const A = (args && args.wave) ? args : {"wave": "B1c", "repos": {"xaas": "/Users/sac/xaas", "ggen_igniter": "/Users/sac/ggen_igniter"}, "ints": {"xaas": "/Users/sac/wt/v26922/fri/xaas-int", "ggen_igniter": "/Users/sac/wt/v26922/fri/ggen_igniter-int"}, "base_branch": "friday/gc-fri-0800", "worktree_root": "/Users/sac/wt/v26922/v23", "branch_prefix": "v23", "receipts_dir": "receipts/v26.9.23", "max_repairs": 2, "context": "v26.9.23 contracts for this wave (also in DRIVER.md):\n- Governing graph: xaas docs/sjira/v26.9.23/goal.ttl. Instance prefix v23: = https://ggen-igniter.dev/sjira/v26.9.23# .\n  Root v23:GC-26.9.23 (dcterms:identifier \"GC-26.9.23\", sj:successorOf fri:GC-FRI-0800 from docs/sjira/v26.9.22/friday/goal.ttl),\n  gates v23:GC23-0 ... v23:GC23-12 (dcterms:identifier \"GC23-<n>\"), successor bucket v23:GC-26.9.24 (stopQuery ASK { FILTER(false) }).\n- Court scripts: every gate's sj:courtCommand is exactly \"sh docs/sjira/v26.9.23/courts/GC23-<n>.sh\" run from the xaas root.\n  Env available to courts: XAAS_DIR (xaas checkout under judgement, default: the cwd), GGEN_IGNITER_DIR (ggen_igniter checkout\n  under judgement, default /Users/sac/wt/v26922/fri/ggen_igniter-int). A court whose machinery has not landed prints\n  \"UNKNOWN: <gate> machinery lands in lane <LANE>\" and exits with the code the stop-court runner maps to UNKNOWN\n  (read lib/mix/tasks/xaas.stop_court.ex for the exit->standing mapping; add a distinct UNKNOWN code there if none exists).\n  Machinery lanes later replace their gate's script body; goal.ttl stays stable.\n- The accepted prose: /Users/sac/wt/v26922/v26923/prd-ard.md is committed byte-identical as docs/sjira/v26.9.23/prd-ard.md\n  (sha256:7c8797b2bc9130fc4c8fce9138cc8140cb704e0633715807398451c660658212, 39386 bytes; do not edit the prose).\n- PVOCAB (proposition vocabulary) is in DRIVER.md; use it verbatim.\n- xaas lane gate prefix: mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors.\n- Cross-repo chain for episodes: courts and episode runners resolve the ggen_igniter checkout from GGEN_IGNITER_DIR. A lane that\n  needs ggen_igniter code not yet merged into ggen_igniter-int creates its OWN detached ggen_igniter worktree\n  (git -C /Users/sac/ggen_igniter worktree add --detach /Users/sac/wt/v26922/v23/<LANE>-gi <sha>) and points GGEN_IGNITER_DIR at it\n  for development; its final gate run and court scripts must work against GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int.\n- Reference KNOWN class: format-drift repair (capability recipe:mix-format, suite ggen-igniter-format, provider recipe,\n  executor recipe-worker). Episode subjects are ggen_igniter commits that introduce format drift deterministically in a\n  dedicated episode branch (v23/episode-<name>), never on friday/gc-fri-0800 or main.\n- No-LLM court env (F3): no ANTHROPIC_*, CLAUDE_*, OPENAI_*, ZAI_*, Z_AI_*, GLM_*, ZCODE_* variables; no zcode/claude binary on PATH;\n  HOME a fresh mktemp dir; MIX_HOME/HEX_HOME/database URL passed explicitly as durable configuration (not credentials).\n  A court run with any LLM credential variable set must be refused with a typed REFUSED(llm_credential_present) and\n  broken_term mu_on_O.\n- OCEL: ARD §13 event classes (WorkOrderCreated, CapabilityResolved, LeaseAcquired, ActuationStarted, ActuationCompleted,\n  VerificationCompleted, ReceiptSealed, StandingChanged, FrontierChanged, MachineExperienceAdmitted) and object types;\n  validate with the existing mix xaas.ocel_validate and pm4py (python3, pm4py 2.7.22 is installed).\n- Court script ownership: the lane that lands a gate's machinery replaces that gate's docs/sjira/v26.9.23/courts/GC23-<n>.sh\n  body (keep the path and the exit-code contract from V23-P). ggen_igniter lanes cannot edit xaas: lane V23-K does that.\n- Canonical capabilityId value space (one pattern for every lane; FRI-T2/FRI-T4 already use it):\n  ^[a-z0-9][a-z0-9_.-]*:[a-z0-9][a-z0-9_.:-]*$ . sj:exclusion is 0..n everywhere (absent = empty list), never 1..n.\n  Any shape, template or regex that deviates is aligned to these in the lane that touches it (V23-C owns the pack shapes).", "lanes": [{"id": "V23-K", "repo": "xaas", "after": [], "gate": "mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && mix test test/sjira/v26_9_23_goal_test.exs && sh docs/sjira/v26.9.23/courts/check_scripts.sh && GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int sh docs/sjira/v26.9.23/courts/GC23-0.sh && GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int sh docs/sjira/v26.9.23/courts/GC23-2.sh", "task": "CONTINUATION (wave B1b stopped: your build agent went silent for 91 min after launching the lane gate). Your worktree /Users/sac/wt/v26922/v23/V23-K already holds the lane code: a20a247 (wire first-mile + bootstrap machinery into GC23-0..GC23-3 courts), 8ca8211 (merge of friday/gc-fri-0800 incl. V23-R), f7dcab3 (stub-ownership test). No receipt exists yet. Do: merge the current friday/gc-fri-0800 (now incl. V23-M) into v23/V23-K; verify the task below is fully implemented at HEAD (fill any gap with new commits); run the lane gate plus courts GC23-0..GC23-3 on the committed head, each command with its own bounded timeout (never one 40-minute compound command; run the long mix test separately with output to your lane scratch log); write and validate receipts/v26.9.23/V23-K.json with identity.tuple_digest per DRIVER.md (V23-K has no row there: take the digest the stop court prints for order V23-K if it exists, else state that V23-K has no goal.ttl order and do not set one). Original task for reference: Wire the ggen_igniter first-mile and bootstrap machinery into the xaas courts (GC23-0, GC23-1, GC23-2, GC23-3). With GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int (V23-C and V23-B merged there): (1) run mix semantic_jira.compile_prose on docs/sjira/v26.9.23/prd-ard.md + candidates/prd-ard.ttl + goal.ttl, commit docs/sjira/v26.9.23/compiled/{propositions.ttl,orders.ttl}; if admission refuses candidates, fix the candidates only through prose_spans.py emit from a corrected extract.json (the extraction JSON is the only hand/LLM-edited artifact) and record each correction. (2) Court bodies: GC23-0 = prose sha equals the committed prd-ard.md, prose_spans.py check passes, compile_prose --check passes (every gate covered, all candidates admitted); GC23-2 = two fresh compile_prose runs into two temp dirs are byte-identical to each other and to compiled/*.ttl, and a candidate mutation is refused; GC23-3 = every WorkOrder in goal.ttl and compiled/orders.ttl admits under the FRI-T1 WorkOrder/GoalCheckpoint shapes (via a ggen_igniter mix task; add mix semantic_jira.admit --graph ... in ggen_igniter only if none exists — if so, do it in a separate ggen_igniter branch v23/V23-K-gi and report it for integration) and dropping each tuple field from one order is refused (F1); GC23-1 = the ggen_igniter bootstrap_court.sh with --fleet docs/sjira/v26.9.23/fleet/universe.json, --goal goal.ttl, receipts dirs of both int worktrees. (3) F8 at the root: a newly discovered order (fixture) whose proposition falsifies no admitted proposition is placed under v23:GC-26.9.24 by the compiler/goal rules, never under a GC23 gate — make that a checked step in GC23-2 or document the rule location. Update test/sjira/v26_9_23_goal_test.exs for the new court bodies."}, {"id": "V23-H", "repo": "xaas", "after": ["V23-K"], "gate": "mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && mix test test/sjira/v26_9_23_goal_test.exs && sh docs/sjira/v26.9.23/courts/GC23-12.sh", "task": "GC23-12 semantic self-hosting (PRD §12, ARD §24 M9). Demonstrate that a new bounded improvement enters through prose with no bespoke backlog: (1) docs/sjira/v26.9.23/successor/v26.9.24-wbpr.md: a short (<= 60 lines) working-backwards press release for the next KNOWN class, 'ggen projection-drift repair' (ggen sync regenerates drifted projections; verifier = ggen sync --check / generated-file diff; exclusions: no registry publish, no network beyond ggen pack fetch), clearly headed 'DRAFT — awaiting operator acceptance'; it is the successor prose, not accepted yet. (2) Extract candidates (the LLM edge, recorded) with scripts/sjira/prose_spans.py into successor/candidates.ttl, write a successor goal graph successor/goal.ttl for v23:GC-26.9.24 (root + gates derived from the prose), compile with mix semantic_jira.compile_prose (GGEN_IGNITER_DIR int) into successor/compiled/{propositions,orders}.ttl, then run the same frontier -> descriptor --provider recipe -> Xaas.Sa2a.Route.resolve on the first eligible order: an unregistered capability must come out as a typed UNKNOWN/UNSUPPORTED(provider_capability) successor item, not an error and not a hand-authored order. (3) Court GC23-12.sh: the successor orders exist only as compiler output (every order IRI recomputes from a proposition IRI; zero orders in successor/ are hand-authored: goal.ttl there contains no sj:WorkOrder), they carry the full tuple, the frontier over them is non-empty, and the court reports the operator-acceptance edge of successor prose as its only open item: exit with the stop-court code for BLOCKED(operator_acceptance) until docs/sjira/v26.9.23/successor/ACCEPTED exists containing the prose sha256 (which only the operator creates), and ALIVE after. Record this operator edge in the receipt."}, {"id": "V23-W", "repo": "xaas", "after": ["V23-K"], "gate": "python3 scripts/sjira/prose_spans.py check --source docs/sjira/v26.9.23/wd-fa/wbpr.md --candidates docs/sjira/v26.9.23/wd-fa/candidates.ttl && python3 scripts/sjira/wd_claims.py check --ledger docs/sjira/v26.9.23/wd-fa/claims.ttl --proposal docs/sjira/v26.9.23/wd-fa/proposal.md", "task": "PRD §9.2 WD FA reference first-mile scenario + the Friday G12 deliverable (not a GC23 gate; required for Friday). Sources (read, do not modify): the deck in the zip at '/Users/sac/Downloads/FA Morning Brief System.zip' (unzip into a scratch dir; 'FA Case Study 2'), autofde-lab PR #170 wd_fa court (merged eb93405c; gh pr view 170 -R seanchatmangpt/autofde-lab and the files it added), xaas PR #61 (WD-CS2; gh pr view 61), ggen-marketplace PR #474 (WD FA packs; gh pr view 474). (1) docs/sjira/v26.9.23/wd-fa/wbpr.md: a WBPR for the WD FA morning-brief system as a bounded future (DRAFT, awaiting operator acceptance). (2) Extract candidates with prose_spans.py (LLM edge recorded) and compile with mix semantic_jira.compile_prose (GGEN_IGNITER_DIR int) into wd-fa/compiled/{propositions,orders}.ttl under a WD goal graph wd-fa/goal.ttl. (3) wd-fa/claims.ttl: every claim-bearing sentence of the proposal gets exactly one class of SUPPLIED | PUBLICLY_OBSERVABLE | ARCHITECTURAL_INFERENCE | WD_DEPENDENT_UNKNOWN (PRD §9.2) with evidence (receipt path + validate_receipt ADMITTED for observed proof; PR/commit for publicly observable; the reasoning chain for inference; the missing WD input for unknown: MTTR baseline, live data, QMS write-back, internal brief sections 2a-2h are WD_DEPENDENT_UNKNOWN unless supplied). (4) wd-fa/proposal.md: 5-8 pages (~2500-4000 words), proposal to WD compiled from the graph: problem, the reference loop, what is proven (with receipts), what is inferred, what WD must supply, a bounded pilot with stop condition. Every claim sentence carries a ledger id marker like [C12]. (5) scripts/sjira/wd_claims.py check: every [Cn] marker in proposal.md resolves to exactly one claim in claims.ttl, every claim is referenced, every SUPPLIED/observed-proof claim's receipt validates ADMITTED, no sentence containing a number or a 'will/is proven/reduces' verb lacks a marker. Unit tests for wd_claims.py. The DOCX/PDF render and the operator's text freeze are later steps; say so in the receipt."}]}
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
