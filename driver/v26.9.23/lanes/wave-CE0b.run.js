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
const A = (args && args.wave) ? args : {"repos": {"chatman": "/Users/sac/wt/v26922/chatman-ecosystem/repo"}, "ints": {"chatman": "/Users/sac/wt/v26922/fri/chatman-ecosystem-int"}, "base_branch": "release/v26.9.23-int", "worktree_root": "/Users/sac/wt/v26922/v23", "branch_prefix": "ce23", "receipts_dir": "receipts/v26.9.23", "max_repairs": 2, "wave": "CE0b", "context": "- chatman-ecosystem lanes: int worktree /Users/sac/wt/v26922/fri/chatman-ecosystem-int (branch release/v26.9.23-int, pushed; CE23-0 receipt a896e16c), repo handle /Users/sac/wt/v26922/chatman-ecosystem/repo; release/v26.9.1 is never modified; the preserved local lineage (refs/preserve/v26.9.23/local-checkout/*) is never pushed.\n- First-mile tools READ-ONLY from their frozen homes: python3 /Users/sac/wt/v26922/fri/xaas-int/scripts/sjira/prose_spans.py (for CE units ALWAYS pass --namespace 'https://ggen-igniter.dev/sjira/chatman-26.9.23#' --prefix ce; its default namespace is v26.9.23#), and ggen_igniter mix semantic_jira.* from your own detached ggen_igniter worktree at /Users/sac/wt/v26922/fri/ggen_igniter-int HEAD under its pin (PATH=/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin:/Users/sac/.asdf/installs/erlang/27.2.4/bin:$PATH).\n- The CE wave is GENERATED from admitted CE23 semantics (operator); the LLM edge is only the extraction JSON (extractedBy recorded). CE23-12 for v26.9.23 = BenchmarkDesign ∧ MSAContract ∧ GeneratedQualificationPlan; NON_LLM_OPERATIONAL is never implied by design (chatman-ce23-12-standings.md). Benchmark design capital: /Users/sac/wt/v26922/v26923/bench/{DESIGN.md,ontology-draft.ttl,orders.json}.\n- Scan-verified implementation facts for the CE lanes are in /Users/sac/wt/v26922/v26923/lanes/scan-plan.json (waves CE0b, CE1, CE2) — read them, re-verify, cite in the subject; do not cite /private/tmp scratch paths as durable.", "lanes": [{"id": "CE-INTAKE", "repo": "chatman", "worktree": "/Users/sac/wt/v26922/v23/CE-INTAKE", "branch": "ce23/CE-INTAKE", "after": [], "gate": "sh release/v26.9.23/sjira/compile_check.sh && for c in release/v26.9.23/sjira/candidates/*.ttl; do echo $c; done", "task": "CONTINUATION of swarm lane CE-INTAKE (subject 96fb0bfb, receipt f318fd24): the work is correct; the earlier failure was the DRIVER's gate string, which omitted --namespace 'https://ggen-igniter.dev/sjira/chatman-26.9.23#' --prefix ce for prose_spans.py (its default namespace v26.9.23# can never match the ce: root). The gate is now compile_check.sh, which runs the ce-namespaced prose_spans check and compile_prose --check for all 3 units. Verify compile_check.sh really runs prose_spans check with --namespace/--prefix ce and --require-gates over the CE23 gates for every unit (if not, fix compile_check.sh), merge the current release/v26.9.23-int forward, rerun, refresh receipts/v26.9.23/CE-INTAKE.json (standing from these runs; no goal.ttl order linking unless the CE goal graph defines one), commit -F. Original task: prose intake of chatman-ce23.md, chatman-ce23-12-bench.md, chatman-ce23-12-standings.md -> CE goal graph (root ce:GC-CE-26.9.23, gates CE23-0..12, CE23-12 as its three conjuncts) -> candidates (LLM edge recorded) -> compile_prose outputs, byte-identical across runs."}, {"id": "CE-LANEPLAN", "repo": "chatman", "after": ["CE-INTAKE"], "gate": "sh release/v26.9.23/sjira/laneplan_check.sh", "task": "Generated lane plan (operator: the CE wave is generated from admitted CE23 semantics). Build a projection turning the compiled sj:WorkOrders (release/v26.9.23/sjira/compiled/*/orders.ttl, as laid out by CE-INTAKE) into the sm-lane-wave spec JSON (read /Users/sac/.claude/workflows/sm-lane-wave.js for the exact contract: {wave, repos, ints, base_branch, worktree_root, branch_prefix, receipts_dir, context, lanes:[{id, repo, after, gate, task}]}). Ontology-first: SPARQL SELECTs (lanes.rq: one row per order; edges.rq: dependencies -> after) rendered through a template with existing generation machinery (prefer stock `mix ggen_igniter.sync` from your detached ggen_igniter worktree or ggen with a small pack under release/v26.9.23/sjira/laneplan-pack/, per scan-plan CE-LANEPLAN-C); lane task text assembled only from order fields. Output release/v26.9.23/lanes/wave-CE1.json (runnable-now lanes) and wave-CE2.json (lanes gated on the Semantic Manufacturing main heads: CE23-3/5/8/10/11). Court laneplan_check.sh: two renders byte-identical; an order missing a tuple field is refused (typed); deleting one order removes exactly its lane and its dependents' edges; every lane traces to an order IRI and every order to a proposition span. Receipt receipts/v26.9.23/CE-LANEPLAN.json."}, {"id": "CE-ANNEX", "repo": "chatman", "after": ["CE-LANEPLAN"], "gate": "set -e; cd /Users/sac/wt/v26922/v23/CE-ANNEX && A=release/v26.9.23/sjira/annex && for g in CE23-1 CE23-2 CE23-3 CE23-7 CE23-9 CE23-10 CE23-11 CE23-12; do test -s $A/$g.md; done && sh release/v26.9.23/sjira/courts/lane_plan.sh && python3 -c \"import json;w=json.load(open('release/v26.9.23/sjira/lane-plan/wave-CE1.json'));import os;assert all(('annex/'+l['id']+'.md') in l['task'] and os.path.exists('release/v26.9.23/sjira/annex/'+l['id']+'.md') for l in w['lanes'])\" && mv $A/CE23-7.md /tmp/annex.bak && { sh release/v26.9.23/sjira/courts/lane_plan.sh > /tmp/annex.m 2>&1; r=$?; mv /tmp/annex.bak $A/CE23-7.md; test $r -ne 0; } && grep -q annex_missing /tmp/annex.m", "task": "Required_23 bridge between the generated lane plan and the verified scan evidence. The generated lane task is assembled only from order fields (postcondition, acceptance, falsifier, capability), which carry the operator's requirement but not the scan-verified implementation facts (generator paths, prototypes, falsifier commands). Commit those facts IN THE SUBJECT, bound by gate id, instead of hand-writing lane specs: release/v26.9.23/sjira/annex/<gate>.md for every construct gate. For CE23-1, CE23-2, CE23-3, CE23-7, CE23-9, CE23-10 and CE23-11 the annex contains verbatim the task, generation path, residue, gate and falsifier of the matching lane in the scan synthesis (driver copy of /private/tmp/claude-501/v23-scratch/SCAN-synthesize/plan.json, waves CE1/CE2/CE-REL; source specs /private/tmp/claude-501/v23-scratch/SCAN-synthesize/specs/<candidate-id>.txt), plus a header 'scan evidence, not a requirement source; the order tuple governs'. For CE23-12 it contains the verbatim entries CE23-12-BD-01..BD-09 of /Users/sac/wt/v26922/v26923/bench/orders.json with bench/DESIGN.md row references; the OP-* entries are successor and go under an 'out of scope' heading. CE23-11's annex states that it runs through the driver release script lanes/ce-release.run.js, not sm-lane-wave. Extend lane_wave.json.eex so every construct lane's task ends with 'Implementation annex: release/v26.9.23/sjira/annex/<gate>.md' and the template refuses REFUSED:SJIRA_LANE_PLAN annex_missing when a construct lane's annex file is absent (add it to lane_plan.sh's mutation corpus); re-render and commit wave-CE1.json. Gates without a construct lane (CE23-0 done by bootstrap; CE23-4/5/6/8 court delegations) need no annex. Residue: the annex files (verified evidence carried into the subject; owner: the future semantic-jira-pack annotation of WorkOrders, successor) and ~6 template lines. Falsifier: removing one annex still renders (the gate's mutation clause), or a rendered lane task omits its annex path. Receipt receipts/v26.9.23/CE-ANNEX.json. NOTE: derive every path from the merged CE-INTAKE/CE-LANEPLAN layout on release/v26.9.23-int (the scan's paths assumed a different layout); if a path in this lane's gate does not exist in that layout, adapt the gate to the equivalent real path and record the mapping in the receipt."}]}
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
