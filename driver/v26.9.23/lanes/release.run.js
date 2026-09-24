export const meta = {
  name: 'sm-release-v26923',
  description: 'v26.9.23 release lane V23-Q: exact-head qualification of both critical-path int heads, stop court, PRs to main with exact-head CI and fix-forward, merge on green, requalify at main heads, release receipt, tags only if STOP=true',
  whenToUse: 'After every GC23 gate except operator-blocked ones is ALIVE on the int heads (DRIVER.md step 7)',
  phases: [
    { title: 'Qualify-int', detail: 'full gate at the exact int heads -> fleet receipts' },
    { title: 'Stop-int', detail: 'stop court at int heads; proceed only if only operator edges remain' },
    { title: 'PR', detail: 'push release branch, PR, exact-head CI, fix-forward, merge on green' },
    { title: 'Court', detail: 'independent verification of each merge' },
    { title: 'Qualify-main', detail: 'full gate at the merged main heads -> fleet receipts' },
    { title: 'Release', detail: 'stop court at main heads, ARD 27 release receipt, tags iff STOP=true' },
  ],
}

const REPOS = {
  xaas: { path: '/Users/sac/xaas', int: '/Users/sac/wt/v26922/fri/xaas-int', slug: 'seanchatmangpt/xaas',
    gate: 'mix format --check-formatted && MIX_ENV=test mix compile --force --warnings-as-errors && mix test' },
  ggen_igniter: { path: '/Users/sac/ggen_igniter', int: '/Users/sac/wt/v26922/fri/ggen_igniter-int', slug: 'seanchatmangpt/ggen_igniter',
    gate: 'mix format --check-formatted && mix compile --warnings-as-errors --force && mix credo && mix test' },
}
const REL = '/Users/sac/wt/v26922/v26923/release'
const FLEET_R = '/Users/sac/wt/v26922/v26923/receipts/fleet'
const BIND = `Binding (the ~/.claude/rules files are loaded): read /Users/sac/wt/v26922/v26923/DRIVER.md (Authority section) and
/Users/sac/wt/v26922/COORDINATION.md. Authority for this lane (operator-approved): push branches (NEVER force, never delete
remote branches), open PRs, merge PRs with a merge commit (gh pr merge --merge) only when every check on the EXACT PR head
is green, create and push annotated tags only when the stop court prints STOP=true. No registry publishes (hex, crates,
GHCR, Homebrew). Never rebase, reset --hard, force, or -X ours/theirs. Commits via -F. Work in the named worktrees or in
fresh detached worktrees under /Users/sac/wt/v26922/v23/rel-*; never touch /Users/sac/xaas or /Users/sac/ggen_igniter
working trees (other executors run there) beyond git fetch/worktree/push. Keep every shell command under ~20 minutes
(long suites write to a scratch log under /private/tmp/claude-501/v23-scratch/REL-<step>). Receipts use the fleet R schema
and must print ADMITTED from python3 ~/.claude/dfcm/validate_receipt.py. Report real command output only; separate
pre-existing failures (also failing on origin/main) from new ones.`

const STEP = { type: 'object', properties: {
  step: { type: 'string' }, repo: { type: 'string' }, ok: { type: 'boolean' }, head_sha: { type: 'string' },
  pr: { type: 'string' }, merge_sha: { type: 'string' }, standing: { type: 'string' },
  gates: { type: 'array', items: { type: 'string' }, description: 'GC23-n STANDING exit, one per gate' },
  receipts: { type: 'array', items: { type: 'string' } }, commands: { type: 'array', items: { type: 'string' } },
  blocked_reason: { type: 'string' }, notes: { type: 'string' },
}, required: ['step', 'ok', 'commands'] }

const qualify = (name, where) => agent(`Target repo: ${REPOS[name].path} (${where === 'int' ? 'integration head of ' + REPOS[name].int : 'origin/main after the release merge'}).
${BIND}
Exact-head qualification of ${name} for GC23-11 (the fleet court needs an ALIVE receipt whose subject_sha is the repo's exact head).
1. ${where === 'int' ? `SHA = git -C ${REPOS[name].int} rev-parse HEAD; the int tree must be clean (git status --porcelain empty) or stop with blocked_reason.` : `git -C ${REPOS[name].path} fetch origin --no-prune; SHA = git -C ${REPOS[name].path} rev-parse origin/main.`}
2. git -C ${REPOS[name].path} worktree add --detach /Users/sac/wt/v26922/v23/rel-${name}-${where} $SHA (reuse if it exists at $SHA);
   provision deps/_build by APFS clone (cp -cR) from ${REPOS[name].int} when mix.lock is identical.
3. Run the full gate there, one command per step: ${REPOS[name].gate}. With GGEN_IGNITER_DIR pointing at the ggen_igniter
   subject of the same stage for xaas (int: ${REPOS.ggen_igniter.int}; main: /Users/sac/wt/v26922/v23/rel-ggen_igniter-main if it exists).
4. Write ${FLEET_R}/${name}-$SHA.json: fleet R receipt, identity.subject=${name}, identity.repo=${REPOS[name].slug},
   identity.subject_sha=$SHA, standing ALIVE only if every gate step exited 0 (else the observed standing + broken_term),
   replay = the exact commands with exits. Validate it. Return head_sha=$SHA.`, { label: `REL:qualify-${where}:${name}`, phase: where === 'int' ? 'Qualify-int' : 'Qualify-main', schema: STEP })

const stopCourt = (where, label, phase) => agent(`Target: xaas ${where === 'int' ? REPOS.xaas.int : '/Users/sac/wt/v26922/v23/rel-xaas-main'}.
${BIND}
Run the GC-26.9.23 stop court at the ${where} heads: cd to that xaas checkout;
MIX_ENV=test GGEN_IGNITER_DIR=${where === 'int' ? REPOS.ggen_igniter.int : '/Users/sac/wt/v26922/v23/rel-ggen_igniter-main'} GC23_FLEET_RECEIPTS_DIR=${FLEET_R}
mix xaas.stop_court --checkpoint GC-26.9.23 --receipts-dir ${REL}/${where}-stop (bounded by timeout 1800). Validate the STOP receipt.
Return gates = one line per GC23 gate "GC23-n STANDING exit", standing = "STOP=true" or "STOP=false", and in notes the
order table and, for every non-ALIVE gate, its last output line. ok=true iff every gate is ALIVE except gates whose last
line names an operator edge (operator_acceptance).`, { label, phase, schema: STEP })

const pr = (name) => agent(`Target repo: ${REPOS[name].path}; integration worktree ${REPOS[name].int} (branch friday/gc-fri-0800).
${BIND}
Release PR for ${name}:
1. H = git -C ${REPOS[name].int} rev-parse HEAD. git -C ${REPOS[name].path} ls-remote origin refs/heads/release/v26.9.23: if it
   exists and is not an ancestor of H, use release/v26.9.23-sm instead. Push: git -C ${REPOS[name].int} push origin
   friday/gc-fri-0800:refs/heads/<release branch> (no --force).
2. If an open PR from that branch exists, reuse it; else gh pr create -R ${REPOS[name].slug} --base main --head <release branch>
   --title "v26.9.23 semantic manufacturing reference loop (GC-26.9.23)" --body-file <file>: body = what landed (lanes and
   courts from /Users/sac/wt/v26922/v26923/MORNING.md for this repo), the stop-court gate table from
   ${REL}/int-stop, the exact-head qualification receipt ${FLEET_R}/${name}-<H>.json, and "no registry publish".
3. Wait for checks on the exact PR head: poll gh pr checks <n> -R ${REPOS[name].slug} (each poll command < 20 min; total up to
   ~4 h). Compare any failing check with the same workflow on origin/main (pre-existing vs new).
4. On failure: diagnose from gh run view --log-failed; fix forward with NEW commits in ${REPOS[name].int} (take the int merge
   lock: until mkdir ${REPOS[name].int}.merge.lock 2>/dev/null; do sleep 15; done; release it after), rerun the local gate
   for the touched area, push (no force), wait again. Pre-existing failures must still be fixed for a green head, or stop
   with blocked_reason naming each failing check and its evidence. At most 4 fix rounds.
5. When every check on the exact head is green: gh pr merge <n> -R ${REPOS[name].slug} --merge (merge commit; never squash or
   rebase). Record pr URL, head_sha (the PR head that was green), merge_sha.`, { label: `REL:pr:${name}`, phase: 'PR', schema: STEP })

const verifyMerge = (name, p) => agent(`Target repo: ${REPOS[name].path}. Read-only.
${BIND}
Independently verify the release merge claimed for ${name}: ${JSON.stringify(p).slice(0, 3000)}.
Check with gh api: the PR is merged; the merge commit's second parent equals the claimed green head; every check run on that
head concluded success (gh api repos/${REPOS[name].slug}/commits/<head>/check-runs); origin/main contains the merge; the
release branch history contains the previous int history as ancestors (no force push: every commit reported earlier for
this branch is still an ancestor). ok=true only if all hold; list each check with its conclusion.`, { label: `REL:court:${name}`, phase: 'Court', schema: STEP })

const final = (qx, qg) => agent(`Target: xaas /Users/sac/wt/v26922/v23/rel-xaas-main and ggen_igniter /Users/sac/wt/v26922/v23/rel-ggen_igniter-main.
${BIND}
Release receipt for GC-26.9.23 at the merged main heads (xaas ${qx.head_sha}, ggen_igniter ${qg.head_sha}; qualification
receipts ${JSON.stringify([...(qx.receipts || []), ...(qg.receipts || [])])}).
1. Stop court as in the int step but at the main worktrees, receipts to ${REL}/main-stop (GC23_FLEET_RECEIPTS_DIR=${FLEET_R}).
2. Write ${REL}/release-receipt.json (ARD §27: exact checkpoint, graph digest of docs/sjira/v26.9.23/goal.ttl, subject identities
   and repo SHAs, ontology digest of the ggen_igniter semantic-jira-pack ontology.ttl, receipt schema digest, toolchain
   identity (elixir/erlang versions), provider registry identity (the :ultracode_construction_recipes config digest), gate
   receipts, replay result, remaining frontier classifications, LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH from the fmt-1 and
   me-2 OCEL, UNRECEIPTED_ACTUATION, REQUIRED_UNKNOWN, UNCLASSIFIED_REQUIRED_WORK, STOP) in the fleet R schema; validate it.
3. Only if the court printed STOP=true: git -C <each main worktree> tag -a v26.9.23 <head> -F <msgfile naming the release
   receipt sha256>; push the tag (git push origin v26.9.23; fail if the tag exists remotely at another commit). If STOP=false,
   do not tag; list the open gates and whether each is an operator edge.`, { label: 'REL:final', phase: 'Release', schema: STEP })

const verifyFinal = (f) => agent(`Target: xaas /Users/sac/wt/v26922/v23/rel-xaas-main. Read-only except your own scratch receipts dir.
${BIND}
Reproducibility court (PRD §28: ALIVE only if the STOP receipt is reproducible): rerun the stop court exactly as REL:final did
but into /private/tmp/claude-501/v23-scratch/REL-verify, and compare per-gate standing and the STOP value with the claim
${JSON.stringify(f).slice(0, 3000)}. If tags were pushed, confirm v26.9.23 resolves to the qualified main heads on origin.
ok=true only if everything reproduces.`, { label: 'REL:verify', phase: 'Release', schema: STEP })

phase('Qualify-int')
const qi = await parallel(Object.keys(REPOS).map(n => () => qualify(n, 'int')))
if (qi.some(q => !q || !q.ok)) return { stage: 'qualify-int', result: qi }
phase('Stop-int')
const si = await stopCourt('int', 'REL:stop-int', 'Stop-int')
if (!si || !si.ok) return { stage: 'stop-int', result: si, qualify: qi }
phase('PR')
const prs = await pipeline(Object.keys(REPOS), n => pr(n), (p, n) => (p && p.ok ? verifyMerge(n, p).then(v => ({ p, v })) : { p, v: null }))
if (prs.some(x => !x || !x.p || !x.p.ok || !x.v || !x.v.ok)) return { stage: 'pr', result: prs, stop_int: si }
phase('Qualify-main')
const qg = await qualify('ggen_igniter', 'main')
const qx = await qualify('xaas', 'main')
if (!qg || !qg.ok || !qx || !qx.ok) return { stage: 'qualify-main', result: [qx, qg], prs }
phase('Release')
const f = await final(qx, qg)
const v = f ? await verifyFinal(f) : null
return { stage: 'done', qualify_int: qi, stop_int: si, prs, qualify_main: [qx, qg], final: f, verify: v }
