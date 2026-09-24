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
const A = (args && args.wave) ? args : {"wave": "R1c", "repos": {"xaas": "/Users/sac/xaas"}, "ints": {"xaas": "/Users/sac/wt/v26922/fri/xaas-int"}, "base_branch": "friday/gc-fri-0800", "worktree_root": "/Users/sac/wt/v26922/v23", "branch_prefix": "v23", "receipts_dir": "receipts/v26.9.23", "max_repairs": 2, "context": "Pre-freeze repair of the FROZEN release subjects (DRIVER.md 'Release closure procedure'; the full context block of /Users/sac/wt/v26922/v26923/lanes/wave-R1a.json applies verbatim: governing graph xaas docs/sjira/v26.9.23/goal.ttl, court exit contract, no-LLM court env, TOOLCHAIN PIN, RELEASE DEFECT REPAIR). S23=(sha_xaas, sha_igniter, graphDigest): only the named defect may change and no successor work is admitted; every lane of this wave merges BEFORE REL-A3 re-freezes S23, so the 12/13 court reruns once. Pins: xaas PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH ; ggen_igniter PATH=/Users/sac/.asdf/installs/elixir/1.18.4-otp-27/bin:/Users/sac/.asdf/installs/erlang/27.2.4/bin:$PATH ; prove with elixir --version and compile a fresh _build under the pin (APFS-clone deps/ only). Classify every failure: subject defect | environment | pre-existing | generator drift | evidence defect | infrastructure. Generated files change only through their generator; hand-written residue gets a HANDWRITTEN.md row (UNSUPPORTED(generator-capability) + owner pack; append-only, keep both sides on merge). These repair lanes have no goal.ttl order, so their receipts are not order-linked. Scan evidence under /private/tmp/claude-501/v23-scratch/SCAN-* is read-only input: re-run it, copy what you cite into receipts/v26.9.23/<LANE>.gate/, never cite a scratch path as durable. Verified per-lane scan specs: /private/tmp/claude-501/v23-scratch/SCAN-synthesize/specs/<candidate-id>.txt. Hosted CI: pushing the lane branch is allowed (never force); no PRs from lanes; dispatch xaas ci_cd.yaml (gh workflow run ... --ref <lane branch>) only after a YAML parse of the dispatched SHA proves publish-image and deploy cannot run for that dispatch (R1-X-FENCE). Keep every shell command under ~20 min; poll hosted runs in bounded steps.", "lanes": [{"id": "R1-X-LOCK", "repo": "xaas", "after": [], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && mix test test/xaas/zcode_plugin'", "task": "Continuation of R1a lane R1-X-LOCK (release defect F1, generator drift: zcode_plugin pack content hash vs ggen.lock, FM-PACK-008 at test/xaas/zcode_plugin/projection_test.exs). Continue in the EXISTING worktree /Users/sac/wt/v26922/v23/R1-X-LOCK (branch v23/R1-X-LOCK, head fa0d88c). The F1 repair is complete there (27cbcbe, generator-only re-lock through `ggen sync`). The R1a build stopped BLOCKED(admission_vacuous) only because the pinned 1.20.2 compile failed on the pre-existing 'unused require Ash.Query' (lib/xaas/ultracode/semantic_drive.ex:78), which R1-X-COURTS removed (now on friday/gc-fri-0800, merge 246460c). Do: `git merge --no-ff friday/gc-fri-0800 -F <msgfile>` into v23/R1-X-LOCK (merge forward; never rebase; keep both sides on conflict), run the lane gate on the merged head under the xaas pin, paste exits. Change nothing else; a gate failure outside F1 -> stop with blocked_reason + classification. Generation path: `ggen sync` (the same invocation projection_test.exs uses; record `ggen --version`); residue none. Falsifier: restoring ggen.lock to its e999e62 bytes makes projection_test.exs fail with FM-PACK-008. Update and validate receipts/v26.9.23/R1-X-LOCK.json (subject = new head, gate exits, toolchain, classification generator drift).", "worktree": "/Users/sac/wt/v26922/v23/R1-X-LOCK", "branch": "v23/R1-X-LOCK"}, {"id": "R1-X-PIN", "repo": "xaas", "after": ["R1-X-LOCK"], "gate": "PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'elixir --version && mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && GGEN_IGNITER_DIR=/Users/sac/wt/v26922/fri/ggen_igniter-int mix test' && PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH sh -c 'MIX_ENV=dev mix deps.compile --force postgrex && MIX_ENV=dev mix dialyzer --format github' && T=$(mktemp -d) && PATH=/Users/sac/.asdf/installs/elixir/1.20.2-otp-28/bin:/Users/sac/.asdf/installs/erlang/28.5.0.2/bin:$PATH env HOME=$T MIX_HOME=/Users/sac/.mix HEX_HOME=/Users/sac/.hex MIX_ENV=test mix test test/xaas/receipt/r_projection_test.exs > $T/rp.log 2>&1; tail -5 $T/rp.log; grep -Eq '8 tests, 0 failures, 5 skipped|Result: 3 passed, 5 skipped' $T/rp.log", "task": "Required_23: GC23-11 exact-head qualification and CE23-5 green exact-head CI (ci_cd.yaml job ci runs compile --warnings-as-errors, dialyzer and the full suite) under the xaas .tool-versions pin Elixir 1.20.2-otp-28 / Erlang 28.5.0.2. Branch v23/R1-X-PIN off friday/gc-fri-0800 after R1-X-LOCK merged; every other R1a lane (GUARD, COURTS, FENCE, PGREP, DIGEST) must already be merged, else stop with blocked_reason (broken_term mu_on_O). Compile a fresh _build under the pin; run the FULL suite twice (order-dependent failures). Fix only what the pinned run reports and classify each. Verified scan candidates to re-check, not assume: (1) SemanticDrive.build_manifest/2 (semantic_drive.ex ~:593-628) matches only the vsn-1 Mix manifest {1,{elixir,otp},scm}; Elixir 1.20 writes {2,{elixir,otp},scm,lock} (Mix elixir_scm.ex @manifest_vsn 2): accept both declared shapes, refuse any other shape typed. (2) Dialyzer pattern_match at lib/xaas/ultracode/machine_experience.ex ~:539 (closed/5) and ~:1235 (objects/3): unreachable `nil -> []` clauses after RDF.Graph.description/2 (rdf 3.0.1 specs Description.t(), never nil). Replace with `graph |> RDF.Graph.description(subject) |> RDF.Description.triples()` and `graph |> RDF.Graph.description(subject) |> RDF.Description.get(RDF.iri(property), []) |> Enum.sort()` (verified diff /private/tmp/claude-501/v23-scratch/SCAN-CE23-5-XA-dialyzer-dead-nil/fix.diff; at e999e62 before 'Total errors: 31, Skipped: 29', after 'Total errors: 29, Skipped: 29, Unnecessary Skips: 0' exit 0). Never add .dialyzer_ignore.exs entries. With APFS-cloned deps run `MIX_ENV=dev mix deps.compile --force postgrex` first (the ignore entry otherwise misses on a foreign absolute path: false exit 2). Dialyzer took ~20 min cold: run it as its own command, reuse a PLT from /Users/sac/wt/v26922/fri/xaas-int/_build/dev by cp -c if present. (3) test/xaas/receipt/r_projection_test.exs calls ~/.claude/dfcm/validate_receipt.py without an absent-validator guard (hosted runner: 5 failures 'can't open file .../validate_receipt.py'). Add a PER-TEST guard, not @moduletag (that would also skip the 3 fabric-only tests at ~:144/:195/:223): after @validator (~:18) `@needs_validator if File.regular?(@validator), do: false, else: \"needs ~/.claude/dfcm/validate_receipt.py (the fleet R-schema validator)\"` and `@tag skip: @needs_validator` on exactly the 5 tests that call validate/1 (~:58, :90, :107, :127, :164). Ready patch: /private/tmp/claude-501/v23-scratch/SCAN-XA-rproj-validator-guard/rproj-pertest-guard.patch. Classify environment. Generation path: none for these files (machine_experience.ex HANDWRITTEN.md:20, r_projection_test.exs :82, semantic_drive.ex existing rows); the edits shrink or guard already-ledgered files, so update row notes only. Falsifiers: restoring the nil clauses -> dialyzer exit 2 at :539/:1235; removing the guard -> the empty-HOME clause reports 5 failures; restoring the vsn-1-only match -> name the pinned test that fails. Receipt receipts/v26.9.23/R1-X-PIN.json with toolchain, both full-suite results, the dialyzer summary line and every classification."}]}
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
