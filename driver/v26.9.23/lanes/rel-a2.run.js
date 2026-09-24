export const meta = {
  name: 'sm-release-v26923-a2',
  description: 'v26.9.23 release part A2 (pre-acceptance, after the qualification found release defects F1-F5): repair wave R1 (4 courted lanes), freeze exact SHAs, exact-head qualification, stop court expecting GC23-0..11 ALIVE and GC23-12 not ALIVE, reseal published receipts from the owning court, push, prepare (not commit) the operator ACCEPTED artifact, independent verification',
  phases: [
    { title: 'Evidence-repair', detail: 'child wave R1: release defects F1-F5 repaired through courted lanes' },
    { title: 'Freeze', detail: 'record exact SHAs of both release subjects' },
    { title: 'Qualify', detail: 'full gate at each exact head -> out-of-subject fleet receipts' },
    { title: 'Court', detail: 'stop court at the frozen heads; expected pre-acceptance state' },
    { title: 'Reseal', detail: 'commit the court output verbatim, push' },
    { title: 'Accept-prep', detail: 'verify successor digest, stage ACCEPTED for the operator' },
    { title: 'Verify', detail: 'independent check of everything above' },
  ],
}

const R = {
  xaas: { path: '/Users/sac/xaas', int: '/Users/sac/wt/v26922/fri/xaas-int', slug: 'seanchatmangpt/xaas',
    gate: ['mix format --check-formatted', 'MIX_ENV=test mix compile --force --warnings-as-errors', 'mix test'] },
  ggen_igniter: { path: '/Users/sac/ggen_igniter', int: '/Users/sac/wt/v26922/fri/ggen_igniter-int', slug: 'seanchatmangpt/ggen_igniter',
    gate: ['mix format --check-formatted', 'mix compile --warnings-as-errors --force', 'mix credo', 'mix test'] },
}
const SUB = '/Users/sac/wt/v26922/v26923'
const REL = `${SUB}/release`
const FLEET_R = `${SUB}/receipts/fleet`
const DIGEST = 'b1d3d24fc1937f48b2986b1b701409090d765d3d33c4ff75dc498558bb390dc1'
const BIND = `Binding (the ~/.claude/rules files are loaded). Operator release sequence in force: finish the release graph before
expanding it; the two release subjects are xaas and ggen_igniter branch friday/gc-fri-0800 (int worktrees ${R.xaas.int} and
${R.ggen_igniter.int}); admit NO other work into them (no V23-W, no successor work). Authority: push branches (never force), no
PRs in this part, no tags, no registry publish. Never rebase / reset --hard / -X ours|theirs; commits via -F. Take the int merge
lock (until mkdir <int>.merge.lock 2>/dev/null; do sleep 15; done; owner file; release after) before any commit in an int
worktree. Never edit a receipt's claims to match an expectation: receipts come only from rerunning the owning court. Keep each
shell command under ~20 min (long suites to a log under /private/tmp/claude-501/v23-scratch/RELA-<step>). Report real command
output only; separate pre-existing from new failures.`
const STEP = { type: 'object', properties: {
  step: { type: 'string' }, ok: { type: 'boolean' }, repo: { type: 'string' }, head_sha: { type: 'string' },
  gates: { type: 'array', items: { type: 'string' } }, receipts: { type: 'array', items: { type: 'string' } },
  commands: { type: 'array', items: { type: 'string' } }, defects: { type: 'array', items: { type: 'string' } },
  notes: { type: 'string' },
}, required: ['step', 'ok', 'commands'] }

phase('Evidence-repair')
const s = await workflow({ scriptPath: `${SUB}/lanes/wave-R1.run.js` })
const sLane = s && s.summary
if (!sLane || sLane.some(x => x.status !== 'merged')) return { stage: 'evidence-repair', result: s }

phase('Freeze')
const freeze = await agent(`${BIND}
Record the NEW frozen release subjects (the previous freeze was invalidated by release-defect repairs: move the current ${REL}/FREEZE.json
into a "history" array inside the new file). For each of ${R.xaas.int} and ${R.ggen_igniter.int}: git rev-parse HEAD, git status --porcelain
(must be empty apart from untracked tool caches; tracked changes -> ok=false), git log --oneline -1, and confirm no merge lock is
held. Write ${REL}/FREEZE.json {xaas: {sha, branch}, ggen_igniter: {sha, branch}, recorded_at (date -u)}. ok=false if either tree
has tracked changes.`, { label: 'RELA:freeze', phase: 'Freeze', schema: STEP })
if (!freeze || !freeze.ok) return { stage: 'freeze', freeze }

phase('Qualify')
const qual = await parallel(Object.keys(R).map(n => () => agent(`Target repo: ${R[n].path}; frozen subject = HEAD of ${R[n].int} (see ${REL}/FREEZE.json).
${BIND}
Exact-head qualification of ${n} (GC23-11 needs an ALIVE receipt whose subject_sha is the exact head). git -C ${R[n].path}
worktree add --detach /Users/sac/wt/v26922/v23/rel-${n}-int <frozen sha> (if that path exists at another sha, git -C it checkout
--detach <frozen sha>; it is this lane's own scratch worktree). Provision deps/_build by APFS clone (cp -cR) from ${R[n].int} when
mix.lock is identical. Run under the repo's .tool-versions pin, never the ambient /opt/homebrew mix (xaas: elixir 1.20.2-otp-28 + erlang 28.5.0.2; ggen_igniter:
elixir 1.18.4-otp-27 + erlang 27.2.4; PATH=/Users/sac/.asdf/installs/elixir/<v>/bin:/Users/sac/.asdf/installs/erlang/<v>/bin:$PATH; check
elixir --version first; use a fresh _build compiled under the pin, cloning only deps/). Run each gate step as its own command: ${R[n].gate.join(' ; ')}${n === 'xaas' ? ' (with GGEN_IGNITER_DIR=' + R.ggen_igniter.int + ')' : ''}.
Write ${FLEET_R}/${n}-<sha>.json (fleet R schema: identity.subject=${n}, identity.repo=${R[n].slug}, identity.subject_sha=<sha>,
toolchain versions, replay = the exact commands with exits; standing ALIVE only if every step exited 0, else the observed standing
with broken_term) and validate it. Return head_sha.`, { label: `RELA:qualify:${n}`, phase: 'Qualify', schema: STEP })))
if (qual.some(q => !q || !q.ok)) return { stage: 'qualify', qual }

phase('Court')
const court = await agent(`Target: xaas ${R.xaas.int} at the frozen sha.
${BIND}
Run the stop court at the frozen heads: cd ${R.xaas.int}; MIX_ENV=test GGEN_IGNITER_DIR=${R.ggen_igniter.int} GC23_FLEET_RECEIPTS_DIR=${FLEET_R}
timeout 2400 mix xaas.stop_court --checkpoint GC-26.9.23 --receipts-dir ${REL}/int-stop-pre (under the xaas toolchain pin). Validate every receipt it wrote.
Required pre-acceptance state (operator step 2): GC23-0..GC23-11 ALIVE, GC23-12 NOT ALIVE with its last line naming the operator
acceptance edge, STOP=false. Return gates (one line per gate: "GC23-n STANDING exit last-line"), the STOP receipt counters, and
ok=true only in exactly that state. Any other non-ALIVE gate is a release defect: list it in defects with its full court output tail.`,
  { label: 'RELA:court', phase: 'Court', schema: STEP })
if (!court || !court.ok) return { stage: 'court', freeze, qual, court }

phase('Reseal')
const reseal = await agent(`Target: xaas ${R.xaas.int}.
${BIND}
Reseal the published GC-26.9.23 evidence from the owning court run (operator step 3): the court output in ${REL}/int-stop-pre (13 gate
receipts + STOP-GC-26.9.23.json) replaces, byte for byte, the stale R_0 files in docs/sjira/v26.9.23/receipts/ (copy, never edit).
Under the xaas int merge lock: verify git status clean; copy; confirm with cmp that each committed file equals the court output;
git add only docs/sjira/v26.9.23/receipts/; commit -F with a message naming the subject sha the receipts bind (the frozen sha; this
evidence commit is its child and changes only receipt paths), the gate table and STOP=false (pre-acceptance). Release the lock.
Then push both release subjects without force: git -C ${R.xaas.int} push origin friday/gc-fri-0800 and git -C ${R.ggen_igniter.int}
push origin friday/gc-fri-0800; fetch and confirm origin equals local for both. Return head_sha (new xaas head).`,
  { label: 'RELA:reseal', phase: 'Reseal', schema: STEP })
if (!reseal || !reseal.ok) return { stage: 'reseal', court, reseal }

phase('Accept-prep')
const acc = await agent(`Target: xaas ${R.xaas.int}. Do NOT commit or create anything inside the repo.
${BIND}
Prepare (never perform) the operator's GC23-12 acceptance (operator step 4). Compute sha256 of docs/sjira/v26.9.23/successor/v26.9.24-wbpr.md at
the current xaas head (git show HEAD:<path> | shasum -a 256) and confirm it equals ${DIGEST}; read docs/sjira/v26.9.23/courts/GC23-12.sh
to confirm the exact ACCEPTED format it accepts (expected: one line "sha256:<hex>"). Write ${SUB}/operator/ACCEPTED.proposed with exactly
that content and ${SUB}/operator/ACCEPT-GC23-12.md: what is being accepted (path, digest, one-paragraph summary of the prose), and the
exact commands the operator runs to create and commit docs/sjira/v26.9.23/successor/ACCEPTED in ${R.xaas.int} (taking the merge lock) and
push. State plainly that acceptance cannot come from this conversation, a plan, or an agent. ok=false if the digest differs.`,
  { label: 'RELA:accept-prep', phase: 'Accept-prep', schema: STEP })

phase('Verify')
const ver = await agent(`Target: ${R.xaas.int} and ${R.ggen_igniter.int}. Read-only.
${BIND}
Independently verify part A: (1) ${REL}/FREEZE.json shas are ancestors of the current int heads and the only commit after the xaas freeze
sha touches docs/sjira/v26.9.23/receipts/ exclusively (git diff --name-only); ggen_igniter head equals its freeze sha; (2) each qualification
receipt in ${FLEET_R} for the frozen shas validates ADMITTED and its replay exits are all 0; (3) the committed receipts equal ${REL}/int-stop-pre
byte for byte and validate; each binds subject_sha = the frozen xaas sha, graph_hash, verifier and toolchain identity, and a replay command;
(4) GC23-0..11 ALIVE, GC23-12 not ALIVE, STOP=false in the committed STOP receipt; (5) origin/friday/gc-fri-0800 equals the local head in both
repos; (6) no file docs/sjira/v26.9.23/successor/ACCEPTED exists in any commit of xaas friday/gc-fri-0800; ${SUB}/operator/ACCEPTED.proposed
holds sha256:${DIGEST}. ok=true only if all hold.`, { label: 'RELA:verify', phase: 'Verify', schema: STEP })

return { stage: 'awaiting-operator-acceptance', evidence_repair: sLane, freeze, qual, court, reseal, accept_prep: acc, verify: ver }
