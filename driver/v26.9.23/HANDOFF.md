# v26.9.23 handoff — Claude weekly usage limit reached (2026-09-23 ~19:20 PT)

Every Claude subagent now fails with "You've hit your weekly limit · resets Sep 27 at 4pm (America/Los_Angeles)". The
overnight loop is stopped: heartbeat cron 1fe5f8ee deleted, the MP wave (wf_51e9fcdb-d6f) stopped, no merge lock held, all
int worktrees clean. Nothing below was merged by an agent whose courts did not run. Resume from this file (Claude after the
reset, ZCode via the operating doctrine in ~/.zcode/AGENTS.md, or by hand). DRIVER.md has the full procedure; COORDINATION.md
the locks and conservation rules.

## Standing right now

- GC-26.9.23: last full stop court (10:19 PT, xaas-int b4ef5d6) GC23-0..GC23-10 ALIVE (11/13). GC23-11 needs exact-head fleet
  receipts (release part A3/B); GC23-12 waits on the operator's ACCEPTED (V23-H merged; successor prose sha256
  b1d3d24fc1937f48b2986b1b701409090d765d3d33c4ff75dc498558bb390dc1). Since then the release-defect repairs moved both heads, so
  a fresh court is owed.
- CE23 (Chatman): CE23-0 ALIVE (chatman int a896e16c, pushed); CE-INTAKE merged (int 717d52cd, local: not pushed) — the three
  operator prose files compiled into 54 WorkOrders byte-identically. Everything else UNKNOWN.
- CE23-12: design capital in bench/ (DESIGN.md, ontology-draft.ttl, orders.json); BENCHMARK_DESIGN_ALIVE UNKNOWN;
  NON_LLM_OPERATIONAL UNKNOWN for every class (n=0).

## Integration heads (branch in parentheses)

| repo | int worktree | local head | origin |
|---|---|---|---|
| xaas | fri/xaas-int (friday/gc-fri-0800) | c68c74d | c561d9f (push pending) |
| ggen_igniter | fri/ggen_igniter-int (friday/gc-fri-0800) | d6a6e5b | 3937a4f (push pending) |
| chatman-ecosystem | fri/chatman-ecosystem-int (release/v26.9.23-int) | 717d52cd | a896e16c (push pending) |
| ggen-marketplace | fri/ggen-marketplace-int (release/v26.9.23-int) | e3988aba4 | not pushed |

Merged since the morning: V23-K, V23-H, V23-L, V23-S; release-defect repairs R1-GI-FMT, R1-GI-PIN (ggen_igniter full suite under
its 1.18.4 pin), R1-X-GUARD (fail-closed no-LLM guard), R1-X-COURTS (GC23-4 anchor, GC23-7 receipt consistency), R1-X-FENCE
(publish/deploy no longer on push to main), R1-X-PGREP, R1-X-DIGEST, R1-X-LOCK; marketplace packs MP-RELPACK-XW, MP-RPV,
MP-RELPACK-CROWN; chatman CE23-0 and CE-INTAKE.

## Built but NOT admitted (courts could not run — rerun courts, then integrate)

1. **R1-X-PIN** — branch v23/R1-X-PIN @ fc6c133 (worktree v23/R1-X-PIN). Builder reports: lane gate green under the xaas
   1.20.2 pin, full suite twice, dialyzer, r_projection guard, vsn-2 manifest, HOSTSKIP; hosted `ci` job green at its exact
   head. Needs its 3 courts (gate, revert-mutation, doctrine) then the locked merge into xaas-int. Last pre-freeze xaas defect.
2. **R2-GI-PROBE-ISOLATION** — branch v23/R2-GI-PROBE-ISOLATION @ 6c335f0 (pushed). Gate exit 0, base and mutant fail; hosted
   witness owed after R2-GI-CI raises the job timeout.
3. **MP-RELPACK-COURT** — marketplace branch @ 8012f35ed, doctrine refuted twice (admission_vacuous); repair 2 was cut off.

## Not started (specs ready)

- lanes/wave-R2g.json: R2-GI-CI (fetch-depth restore + timeout 30→90), R2-GI-BLOOM. Witnessed gates in lanes/r2/gates.
- lanes/wave-R2x.run.js: 9 xaas lanes (HOSTSKIP, WDCS2, PROD-TIMEOUT=35, IMAGE-CARGO=45 pinned Rust, COHERENCE, FIXEDPOINT,
  TOOLCHAIN, PYLOCK, TRAVERSAL) — after R1-X-PIN merges.
- lanes/wave-CE0b.json lanes CE-LANEPLAN (orders → generated wave-CE1/CE2.json) and CE-ANNEX.
- lanes/rel-a2.run.js (without its child wave): re-freeze → pinned qualification → 12/13 court → reseal committed receipts →
  push → stage operator/ACCEPTED.proposed → verify.
- Then Part B (13/13 STOP=true, two PRs, exact-head CI fix-forward, merge, rebind main heads, final crown), CE1/CE2 generated
  waves, CE-REL, and tags last (all three repos together).

## Resume commands

- Claude after Sep 27 16:00 PT: open this session or a new one in /Users/sac/wt/v26922/v26923 and say "resume v26.9.23 from
  HANDOFF.md"; it relaunches courts for the three built lanes first (a continuation wave with `worktree` set per lane), then
  R2g/R2x, then REL-A3. Runner: ~/.claude/workflows/sm-lane-wave.js; compile a spec with `python3 lanes/mkrun.py <spec.json>`.
- ZCode now: the lane specs are plain JSON (id, repo, gate, task, after); each lane is: build in its worktree → rerun the gate →
  revert-mutation check → doctrine review → `mkdir /Users/sac/wt/v26922/fri/<repo>-int.merge.lock` → `git merge --no-ff` →
  gate on the int head → release the lock. ~/.zcode/AGENTS.md carries the doctrine. (The automatic takeover runtime was
  court-refuted in v26.9.22 and is successor work; follow the lanes by hand or with ZCode's own loop.)

## Operator items (only you)

1. GC23-12: after REL-A3 stages it (or now, since the prose is on xaas friday/gc-fri-0800), verify the digest above and commit
   docs/sjira/v26.9.23/successor/ACCEPTED containing `sha256:b1d3d24fc1937f48b2986b1b701409090d765d3d33c4ff75dc498558bb390dc1`.
2. Security: seanchatmangpt/gymact and seanchatmangpt/open-ontologies (PUBLIC) track `.ggen/keys/signing.key` — rotate both.
3. The Friday 08:00 PT target is not reachable with Claude agents (reset is Sep 27 16:00); the release chain continues after the
   reset or under ZCode.
