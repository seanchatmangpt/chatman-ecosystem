# v26.9.23 overnight driver (GC-26.9.23)

Started 2026-09-22 23:25 PT by Claude session 1fecd79a on operator directive "run ultracode loops overnight until
v26.9.23 is complete for all of my projects". Contract: `prd-ard.md` (this dir; operator-accepted, O* by testimony).
Any executor (Claude heartbeat, ZCode via `ultracode-takeover`) resumes from this file plus the substrate listed below.

## Objective (finite)

STOP(GC-26.9.23) = GC23-0 ∧ … ∧ GC23-12 ALIVE (gate receipts from `mix xaas.stop_court --checkpoint GC-26.9.23`)
∧ RequiredUnknown = ∅ ∧ RequiredLLM_KNOWN = ∅ ∧ RemainingFrontier ⊆ Successor ∪ Blocked ∪ Unsupported ∪ Refused.
"All projects" = GC23-11: every fleet repo has exact-subject standing or an explicit non-required classification
(PRD §10: making every repo ALIVE is a non-goal). Discovered work that falsifies no GC23 proposition goes to GC-26.9.24.

## Substrate

| what | where |
|---|---|
| governing graph | xaas `docs/sjira/v26.9.23/goal.ttl` + `stop.rq` (lane V23-P) |
| int worktrees | `/Users/sac/wt/v26922/fri/{ggen_igniter,xaas}-int`, branch `friday/gc-fri-0800` |
| lane worktrees | `/Users/sac/wt/v26922/v23/<LANE>`, branch `v23/<LANE>` |
| merge lock | `mkdir /Users/sac/wt/v26922/fri/<repo>-int.merge.lock` (COORDINATION.md) |
| lane runner | `~/.claude/workflows/sm-lane-wave.js` (build → 3-lens court → ≤2 repairs → locked integrate) |
| wave specs | `lanes/wave-*.json` (args passed to the runner) |
| tick log | `ticks/<ISO>.md` (one per driver tick) |
| handoff | `~/.claude/workflow-handoff/<runId>.json` |

## Gate → lane map

| gate | meaning (PRD §12) | lane(s) | wave | depends on |
|---|---|---|---|---|
| GC23-0 | accepted prose + admitted semantic projection | V23-P (prose, goal), V23-X (candidates), V23-C (admission) | B0/B1 | — |
| GC23-1 | cold bootstrap, 2 identical reconstructions | V23-B | B1 | FRI-T1, FRI-T6 |
| GC23-2 | prose → finite sJira delta, byte-identical | V23-C | B1 | FRI-T1, V23-X |
| GC23-3 | full tuple on every required order (F1) | V23-P (graph) + V23-C (shapes court) | B0/B1 | FRI-T1 |
| GC23-4 | SA2A conservation (F2) | FRI-T4 (done) + V23-D (live hop digests) | B1 | FRI-T2..T4, FRI-T6 |
| GC23-5 | no-LLM KNOWN execution (F3) | V23-D | B1 | same |
| GC23-6 | independent consequence + revert falsifier (F4) | V23-D | B1 | same |
| GC23-7 | R-projection ADMITTED + OCEL events | V23-D | B1 | same |
| GC23-8 | closed frontier (order leaves, dependent enters) | V23-D | B1 | same |
| GC23-9 | MachineExperience ratchet, episode 2 KNOWN | V23-M | B2 | V23-D |
| GC23-10 | cold replay identical; F5, F6 | V23-R | B1/B2 | V23-D (court) |
| GC23-11 | bounded fleet, F7 | V23-F | B0 | — |
| GC23-12 | successor prose → same pipeline, no bespoke backlog | V23-H | B2 | V23-C, V23-X |
| (ref 9.2) | WD FA first-mile reference + claims ledger | V23-W | B2 | V23-C |
| release | stop court on int, PR → main, exact-head CI, release receipt | V23-Q | C | all |

## Proposition vocabulary contract (PVOCAB; V23-X writes it, V23-C admits it)

`sj:` = the semantic-jira-pack namespace; instances `v23:` = `https://ggen-igniter.dev/sjira/v26.9.23#`.
- `sj:Proposition`; `sj:propositionKind` ∈ Actor Object Role State Transition Capability Trigger Dependency Invariant
  Exclusion Evidence Authority Postcondition Falsifier Metric Successor (ARD §5.2); `sj:statement` (one declarative
  sentence); `sj:sourceDocument` (repo-relative path); `sj:sourceSha256` ("sha256:<hex>" of the source bytes);
  `sj:sourceStart`/`sj:sourceEnd` (xsd:integer UTF-8 byte offsets, half-open); `sj:sourceText` (= bytes[start:end]);
  `sj:boundaryClass` (sj:Bootstrap|FirstMile|Core|LastMile|Successor); `sj:requiredBy` (gate IRI, e.g. v23:GC23-5;
  absent ⇒ not required); `sj:candidateStanding "UNKNOWN"`; `sj:extractedBy` (e.g. "llm:claude-opus-5-5@<runId>").
- Optional tuple hints copied into manufactured WorkOrders: the FRI-T1 tuple properties (sj:postcondition,
  sj:requiresCapability, sj:evidenceHorizon, sj:exclusion, sj:consequenceClass, sj:successorPolicy) plus acceptance and
  falsifier text using the pack's existing properties for those meanings.
- IRI: `v23:P-` + first 16 hex of sha256("<sourceSha256>:<start>:<end>:<kind>").

## Tick procedure (heartbeat or workflow-completion notification)

1. Read the newest `ticks/*.md` and the journals of running waves (handoff registry → transcriptDir/journal.jsonl).
2. For each finished lane: verify on disk — `git -C <int> log --oneline`, rerun the lane gate in the int worktree when it
   merged, `python3 ~/.claude/dfcm/validate_receipt.py <receipt>`. Journal claims are O until this passes.
3. In xaas-int (once V23-P merged): `mix xaas.stop_court --checkpoint GC-26.9.23` with GGEN_IGNITER_DIR=<ggen_igniter-int>;
   record per-gate standing.
3b. Stall handling: a lane agent with no transcript write for >40 min and no child process is stalled (API layer).
   Do NOT resumeFromRunId a concurrent wave: agent() order varies under concurrency, so the cache prefix breaks and
   already-merged lanes re-run their courts (observed 03:50 PT). Instead TaskStop the wave, extract finished verdicts to
   lanes/<wave>-carryover.json, and launch a continuation wave containing only unmerged lanes (existing worktrees are
   reused; the task names the prior head and the court findings still to answer).
4. Launch the next wave whose dependencies merged (never two waves integrating the same lane ids; the runner locks).
   A lane refuted after 2 repairs → one fresh-approach lane with the court evidence; refuted again → BLOCKED with
   broken_term in `lanes/blocked.json`, move on (a blocker branches the graph; it does not halt it).
5. Disk < 20 GB → `oclnr` pressure daemon handles snapshots; < 10 GB → `/Users/sac/.oclnr/bin/oclnr snapshot thin` and
   do not launch new builds. Load is shared with ZCode lanes: cap new builds at ~6 concurrent.
6. Write `ticks/<ISO>.md`: gates table, lanes launched/merged/refuted, next action.
7. Loop ends when STOP=true (then V23-Q release) or every non-ALIVE gate is BLOCKED on an operator edge; by 07:00 PT write
   `MORNING.md` (manufacturing receipt: gates, SHAs, receipts, operator edges, successor list).

## Authority (unchanged from v26.9.22, operator-approved)

Push branches (never force), open PRs, merge PRs on green exact-head CI, create tags; no registry publishes (hex, crates,
GHCR, Homebrew stay manual). Never rebase / force / reset --hard / -X ours|theirs. Fetch with --no-prune. Preserve refs and
stashes are never dropped. Never edit another executor's worktree. Disk actions go through osx-clnr.

## Live handles (session 1fecd79a)

- Heartbeat cron job `1fe5f8ee` (13,43 * * * *), session-only.
- Waves: A = wf_7bb49b92-253 (FRI-T1..T5) + wf_b39b51a5-927 (FRI-T6, refuted at doc2 → repaired by V23-T6R in B1);
  B0 = wf_85494993-6b8 (V23-P, V23-X, V23-F).
- Wave A finished 00:20 PT: FRI-T3/T4/T5 merged; FRI-T1 (receipt evidence only), FRI-T2, FRI-T6 refuted → V23-T1R/T2R/T6R.
- B1 = wf_1848cfc0-c6e, script lanes/wave-B1.run.js (spec embedded by `python3 lanes/mkrun.py lanes/wave-B1.json`;
  Workflow scripts cannot read files, so each wave spec is compiled into a runnable copy of the runner).
- 03:50 PT B1 stopped (gate1:V23-T6R silent 61 min, gate1:V23-D 30 min, no child processes); a resume re-ran merged
  lanes' courts and was stopped. Merged from B1: V23-T1R (52798a0), V23-T2R (a626e7b), V23-C (4e5d196).
  B1b = wf_9bcfbd57-346 (lanes/wave-B1b.run.js): T6R (continue, answer doc1), D<-T6R (continue), B<-T6R, K<-B, R/M<-D, H/W<-K.
- C0 = wf_71400bee-3c9 (V23-L, stop-court order receipts from both repos), launched 07:47 PT.
- 09:15 PT B1b stopped: V23-K build agent silent 91 min after a 40-min compound gate call (no child process). Merged from
  B1b: V23-T6R c90c17b, V23-D c7b0e26, V23-B 3937a4f, V23-R 86345d9, V23-M (xaas-int 3d61787). B1c = wf_84ed34c4-9a6: K (continue), H<-K, W<-K.

## Receipt linking (required for every v26.9.23 lane receipt)

The stop court links a lane receipt to its goal.ttl order only when `identity.tuple_digest` equals the order's tuple
digest (else ADMITTED-UNLINKED :tuple_digest_mismatch → the order stays open). Set `identity.tuple_digest` and
`identity.work_order` ("v23:WO-<LANE>") in `receipts/v26.9.23/<LANE>.json`. Get the digest from a real run:
`MIX_ENV=test mix xaas.stop_court --checkpoint GC-26.9.23 --only GC23-0 --receipts-dir <your scratch>` in an xaas
checkout at friday/gc-fri-0800 (it prints `order <LANE> ... digest=...`). Digests at xaas-int c18ecd3 (goal.ttl unchanged):

| order | tuple digest |
|---|---|
| V23-B | sha256:5bee8ea4d45e0cc88a311a2a910240211441b2f82fae54372622a1b93647f97f |
| V23-C | sha256:007031d1b404fe3952e106c69b8d8156528829d3e2687b9eafaa5da9f858d873 |
| V23-D | sha256:3d3b9cf4ea96e6498d1d5c1a0c490fb8fd67f7cd68cf210eb889dd5b92801d58 |
| V23-H | sha256:9f666dd9c31ca278923c55898c57e49ecf59700b9c3987fe7c3cb2e3512ee845 |
| V23-M | sha256:10199e1d08495cc7bcb4423e76cabd9878375f7e695dfe5e8603201c3818fa02 |
| V23-Q | sha256:79cf01e19ce4b3ee1f7064e607a1c8deb272aecbcc544003affcb015fe735e9f |
| V23-R | sha256:01861be76e742250e796228de64e8dde326ed035812f8532743c930d55520cc3 |
| V23-W | (successor bucket; typed Successor in goal.ttl) |

Repair lanes V23-T1R/T2R/T6R have no v23 order (they finish Friday lanes FRI-T1/T2/T6); their receipts are not linked.
- 10:25 PT operator 'git push': pushed friday/gc-fri-0800 (xaas b4ef5d6, ggen_igniter 3937a4f) and 8 ggen_igniter v23/episode-* receipt-subject branches to origin (new branches, no force). Re-push after V23-H/V23-W merges.

- 10:50 PT operator input `chatman-ce23.md` (Chatman Ecosystem v26.9.23 release requirements CE23-0..11): the release is a
  dependency-closed composition around GC-26.9.23 + a chatman-ecosystem release subject with a 16-role crosswalk; V23-W (WD FA)
  is NOT a v26.9.23 blocker → B1c stopped (V23-W work kept on v23/V23-W @ de51e88, continues as successor GC-26.9.24).
- Release lane V23-Q launched: wf_d70620b5-8b1 (lanes/release.run.js). Loop scan (generation-first additions, CE23 lanes):
  wf_cf07ec8e-051 → synthesized wave specs to be launched as wave CE.

## Release closure procedure (operator, 2026-09-23 ~10:55 PT) — supersedes step 7 above

Finish the graph before expanding it. Chain:
V23-Q qualification → fresh durable receipts → operator GC23-12 acceptance → GC23-12 ALIVE → STOP=true on integration heads →
exactly two PRs (xaas, ggen_igniter → main) + exact-head CI (fix forward; classify every failure: subject defect | environment |
pre-existing | generator drift | evidence defect | infrastructure; generator-owned failures are fixed in the generator) → merge both →
rebind to the new main SHAs → all 13 gates + cold replay + fresh fleet classification + STOP court at the main pair (reproducible
STOP=true) → CE23 generated from chatman-ce23.md (+ chatman-ce23-12-bench.md) through prose → candidates → admission → delta →
WorkOrders → generated lane plan → chatman-ecosystem root crown (identity, 16-role crosswalk, imported SM STOP by digest, fleet
closed, exact main heads, replay, root receipt, CE23-12 non-LLM benchmark crown) → tag v26.9.23 last.
- Release subjects are FROZEN (xaas + ggen_igniter friday/gc-fri-0800): no successor work is admitted (V23-W stays on its branch).
- Part A = lanes/rel-a.run.js (wf_255d8b21-5fe): V23-S evidence repair (verifier/toolchain identity + derived counters in receipts),
  freeze, qualify, court (expect GC23-0..11 ALIVE, GC23-12 not ALIVE, STOP=false), reseal committed receipts from the owning court,
  push, stage operator/ACCEPTED.proposed + operator/ACCEPT-GC23-12.md. The driver NEVER creates successor/ACCEPTED.
- Part B (after the operator commits docs/sjira/v26.9.23/successor/ACCEPTED): rerun GC23-12, full court STOP=true, reseal, PRs, CI,
  merge, rebind, final crown. Heartbeat detects ACCEPTED via git -C xaas-int log -- docs/sjira/v26.9.23/successor/ACCEPTED and
  git ls-tree origin/friday/gc-fri-0800.
- Scan findings (wf_cf07ec8e-051) and benchmark design (wf_2f1cc752-e29) enter only through the admission function: Required_23 iff the
  candidate names the current proposition it falsifies with evidence, an owning generator/pack/template, consequence, verifier and
  falsifier; otherwise Successor_24+. "Useful" is not admission.
- CE23-12 (operator, chatman-ce23-12-bench.md): DfLSS non-LLM operational benchmark crown (>=5 KNOWN classes, >=30 unseen/class,
  false-KNOWN=0, LLM=0, RTY>=90% ...), benchmark cases/reports/CI matrix projected from RDF via ggen; executor additions land on
  branches off main after the release merges.
- Tagging is the consequence of closure, never the mechanism.
- 11:12 PT operator refinement (chatman-ce23-12-standings.md): CE23-12 for v26.9.23 = BenchmarkDesign ∧ MSAContract ∧
  GeneratedQualificationPlan (standing BENCHMARK_DESIGN_ALIVE). NON_LLM_OPERATIONAL_ALIVE(C) needs executed unseen-member receipts +
  MSA_ALIVE + statistical qualification + zero LLM + replay and is never implied by the design. Standing is evidence-volume typed
  (class, n, defects, confidence, upper bound, environment scope, factors, receipt); tiers N 30/100/300/3000. OS factor UNSUPPORTED on this
  macOS-only executor (no fake cross-OS evidence). Frozen-subject rule: every pre-acceptance receipt is a function of
  S23 = (sha_xaas, sha_igniter, graphDigest); if either SHA moves, the 12/13 court must be rerun. The operator independently verifies
  the successor digest before creating ACCEPTED. Bench DMA relaunched with the MSA scanner: wf_a0af447e-5fa.
- 12:30 PT REL-A found release defects F1-F5 at the freeze (xaas e999e62 / ggen_igniter 3937a4f); REL-A2 wf_1c477da3-9b7 = repair wave R1
  (4 courted lanes) → re-freeze → qualification under .tool-versions pins → court → reseal → push → ACCEPTED staging → verify.
- 12:50 PT repair wave R1a = wf_7a7c7064-905 (lanes/wave-R1a.json): F1 R1-X-LOCK, F2 R1-X-DIGEST, F3/F4 R1-GI-FMT, F5 R1-X-PGREP,
  GC23-5 R1-X-GUARD (fail-closed allowlist; provider list as data), GC23-4/GC23-7 R1-X-COURTS (anchor + receipt consistency),
  authority R1-X-FENCE (publish-image/deploy no longer run on push to main), then R1-X-PIN and R1-GI-PIN (full suites under the
  .tool-versions pins). After R1a merges and the scan's skeptics finish (admission rule), launch REL-A3 = rel-a2 without the child
  wave: re-freeze → pinned qualification → 12/13 court → reseal → push → ACCEPTED staging → verify.
  (Tick filenames 2026-09-23T20-00Z.md was written at ~12:40 PT; its Z label is off by ~20 min.)
- 14:20 PT operator: "launch an orthogonal swarm to assist" → wf_2755fdff-28e: CI pre-flight (ggen_igniter failed push run at 3937a4f;
  xaas dispatch on friday/gc-fri-0800) → wave-R2.json fix lanes (pre-freeze, after R1a); CE23-0 identity (GitHub clone
  /Users/sac/wt/v26922/chatman-ecosystem/repo + int worktree /Users/sac/wt/v26922/fri/chatman-ecosystem-int, branch release/v26.9.23-int;
  local checkout untouched, lineage pinned as preserve refs) → child wave CE0 (CE-INTAKE prose→orders, CE-LANEPLAN generated wave spec).
- 14:25 PT operator: "you are the expert, answer the questions yourself" → cleanup policies recorded in COORDINATION.md; cleanup-2
  wf_0cf7ad0a-425. GC23-12 acceptance stays the operator's by the operator's own closure contract (not a cleanup question).
- 15:05 PT loop scan wf_cf07ec8e-051 finished: 75 candidates → 56 kept by skeptics → 8 waves in lanes/scan-plan.json
  (R1c, R2, MP, CE0b, CE1 generated, CE2 generated, CE-REL, S24 successor). MP launched: wf_51e9fcdb-d6f (ggen-marketplace int
  /Users/sac/wt/v26922/fri/ggen-marketplace-int, branch release/v26.9.23-int from origin/main 420bc91e). Sequence: R1a → R1c → R2
  (reconciled with the swarm's wave-R2.json by defect_key, ≤5 concurrent builds) → REL-A3.

## Driver decisions on scan operator-edges (operator: "you are the expert, answer the questions yourself"; 2026-09-23 15:05 PT)
- GC23-12 acceptance: NOT decided by the driver — the operator's closure contract makes it operator authority.
- chatman lineage: the local checkout /Users/sac/chatman-ecosystem is a disjoint lineage (no shared ancestry with GitHub main). The
  release subject is GitHub main; the local-only refs are pinned as preserve refs in the GitHub clone (CE23-0 lineage proof); importing
  local-only content (v26.9.22 jurisdiction contracts) is successor GC-26.9.24. The local checkout is never modified.
- Tag scope: no v26.9.23 tag is created by the Semantic Manufacturing release (Part B). All v26.9.23 tags (xaas, ggen_igniter,
  chatman-ecosystem) are created together only at CE-REL after the Chatman root crown (operator: "tag last").
- CE23-9 strict crown membership: every existing chatman CI/crown check is in the root court with a typed disposition; checks that
  fail on base for pre-existing causes unrelated to CE23 propositions (e.g. cargo-deny advisories) are typed BLOCKED/SUCCESSOR with
  evidence, not silently dropped and not gating.
- wd-cs2: if R2-X-WDCS2 cannot make the WD-specific court green, path-filter wd-cs2-exact-head.yml to WD paths (WD FA is successor);
  it keeps gating WD changes.
- Image Rust toolchain: Docker builder installs a pinned Rust toolchain (R2-X-IMAGE-CARGO); no RustlerPrecompiled/hex publish.
- ggen-marketplace: packs are vendored byte-identically into the chatman subject for v26.9.23; the marketplace release/v26.9.23-int
  branch is pushed but not merged to marketplace main (upstream merge = successor S24-MP-RELPACK-UPSTREAM).
- Friday WBPR (GC-FRI-0800 G0): superseded by the operator PRD/ARD v26.9.23 (PRD §24 M3: GC-FRI-0800 results are predecessor evidence).
- WD FA proposal (V23-W): successor GC-26.9.24 per chatman-ce23.md; no v26.9.23 text freeze required.
- 17:17 PT R1c = wf_18c25526-098 (R1-X-LOCK continue → R1-X-PIN full suite + dialyzer + r_projection guard + manifest vsn-2 under the 1.20.2 pin); launched while R1-GI-PIN repairs (ggen_igniter, independent). All other R1a xaas lanes merged (xaas-int c561d9f).
- 18:25 PT R1a wf_7a7c7064-905 complete (7 merged; LOCK via R1c; PIN in R1c). ggen_igniter-int d6a6e5b.
- 18:45 PT swarm wf_2755fdff-28e complete: CE23-0 ALIVE (chatman int a896e16c pushed); wave-R2.json (7 witnessed lanes, gates in
  lanes/r2/gates, candidates in lanes/r2/candidates). Launched R2g wf_6b532918-9da (ggen_igniter: GI-CI, PROBE-ISOLATION, BLOOM) and CE0b
  wf_d392b2d8-3f7 (CE-INTAKE continue with the corrected gate → CE-LANEPLAN → CE-ANNEX). Prepared R2x (lanes/wave-R2x.run.js: 4 swarm +
  5 scan xaas lanes, driver gate-conflict decisions in its context) — launch when R1c's R1-X-PIN merges. Then REL-A3.
- 19:25 PT Claude weekly usage limit hit (resets 2026-09-27 16:00 PT): all subagents fail. Loop halted: cron 1fe5f8ee deleted, MP stopped. State + resume procedure: HANDOFF.md.

## Finish directive (operator, 2026-09-23 22:05 PT): "ultracode finish all work then merge to the default branches"
- Merge authority is now explicit: after the release graph finishes, the int branches merge to each repo's default branch
  (xaas main, ggen_igniter main, chatman-ecosystem main, ggen-marketplace main) through PRs with a merge commit, only on green
  exact-head CI, fix-forward only. This supersedes the earlier "marketplace not merged to main" decision (S24-MP-RELPACK-UPSTREAM
  is pulled into v26.9.23).
- GC23-12 acceptance is still NOT inferred from this directive (operator closure contract: acceptance cannot come from the
  conversation). Merging proceeds pre-acceptance: the main-head court reports GC23-12 open on the operator edge, STOP=false, and no
  tag is created (tags remain the consequence of STOP=true at CE-REL). operator/ACCEPT-GC23-12.md is restaged to target main.
- Sequence: F1 continuation waves (F1x xaas R1-X-PIN + R2x, F1g ggen_igniter R2g, F1mp MP-RELPACK-COURT, F1ce CE-LANEPLAN →
  CE-ANNEX) → exact-head CI preflight on the int heads → REL-A3 (freeze, pinned qualification, 12/13 court, reseal, push, stage) →
  PRs + CI + merge (xaas, ggen_igniter) → rebind main heads, qualification + court at main → CE1/CE2 generated waves → CE-REL root
  crown + receipt (STOP-conditional parts typed open) → chatman and marketplace PRs + merge → HANDOFF.
- 22:10 PT disk: osx-clnr merged2 (merged-lane build dirs) + idle-targets (cargo target/ of worktrees idle >12 h) + thin → 57 GB free.
- 22:55 PT operator: "what about ~/dev/zcode-cli to execute" → "no I don't want this mess of worktrees". Execution model changed:
  * No lane worktrees and no mutation worktrees. One checkout per repo: the int trees (fri/{xaas,ggen_igniter,chatman-ecosystem,
    ggen-marketplace}-int). Lanes run serially per repo ON the int branch (lanes/serial.py; queues lanes/queue-{SX,SG,SM,SC}.json),
    in parallel across repos. ZCode (`node ~/dev/zcode-cli/bin/zcode.js -p … --cwd <int> --mode yolo --json`) is the constructor;
    the court is deterministic and in place (lane gate rerun with LLM variables stripped + in-place revert-mutation, touched paths
    restored); refuted → ZCode repair ≤2 → one inverse-diff revert commit (fix-forward) + BLOCKED. Court records:
    receipts/serial/<LANE>.court.json. Another repo's code at a SHA = `git archive` into scratch, never a worktree.
  * F1x/F1g/F1mp/F1ce Claude waves stopped; their in-flight work committed as labelled WIP on the lane branches (pushed) and brought
    into the int trees by the queues (merge_branch). Runner smoke-tested on a real tmp repo (admit / vacuous-refute+revert /
    blocked-dep / already-merged base recovery).
  * Worktree collapse: lanes/wt_collapse.py (dirty → refs/preserve/v26.9.23/wt-collapse/<slug> snapshot, unreferenced detached HEAD →
    preserve ref, branches kept, *.key recorded by sha256 only); receipt disk/wt-collapse.json. Kept: main checkouts, the 4 int trees,
    anything another executor touched <12 h or holds a live cwd.
  * Release: lanes/release.py (deterministic; ZCode only for CI fix-forward) chained after SX+SG by lanes/chain-release.sh: PR+CI →
    freeze → qualify in the int trees → 12/13 court → reseal → CI → stage acceptance → merge (--match-head-commit) → ff int to main →
    qualify + court at main → release receipt → reproduce. No tags (CE-REL tags all repos together, after STOP=true).
