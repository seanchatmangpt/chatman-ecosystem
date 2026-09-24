# v26.9.22 multi-executor coordination (written 2026-09-22 by Claude session autonomic-loop-completion)

Two executors act on the same `release/v26.9.22` integration worktrees (`/Users/sac/wt/v26922/<repo>/int`):

| executor | owns |
|---|---|
| ZCode lanes L1..L10 (`/private/tmp/v26922-wos/L*.txt`) | the synthesized orders listed in its lane files |
| Claude session (workflow lanes) | law-derived orders GGEN_IGNITER-26922-15..19,21; XAAS-26922-19..25; ASH_A2A-26922-14; FERROPLAN-26922-09 (see /Users/sac/wt/v26922/orders.json), and the qualification court over every merge into release/v26.9.22 |

## Merge protocol (both executors)
1. Acquire: `until mkdir /Users/sac/wt/v26922/<repo>/.merge.lock 2>/dev/null; do sleep 10; done; echo "<executor>:<WO>:$(date -u +%FT%TZ)" > /Users/sac/wt/v26922/<repo>/.merge.lock/owner`
2. Merge only into a CLEAN int worktree (`git status --porcelain` empty); never merge on top of another executor's uncommitted files.
3. Release: `rm /Users/sac/wt/v26922/<repo>/.merge.lock/owner; rmdir /Users/sac/wt/v26922/<repo>/.merge.lock`
4. Build and test in your own worktree, never inside another executor's `wo*`/`law-*` worktree.

## Receipts
Every order writes `receipts/v26.9.22/<WO>.json` that validates:
`python3 ~/.claude/dfcm/validate_receipt.py receipts/v26.9.22/<WO>.json` (schema `~/.claude/dfcm/receipt.schema.json`:
identity/authority/consequence/replay/standing; BLOCKED/REFUSED carry `broken_term`).

## Court gate
Court verdicts land in `/Users/sac/wt/v26922/court/<repo>/<WO>.json`. Push/PR-merge/tag of `release/v26.9.22`
proceeds only for orders whose court verdict is `pass` (acceptance re-run + revert-mutation must make acceptance fail +
doctrine lens). Refuted orders are recorded, not silently reverted.

## Doctrine
Global rules for all runtimes: `~/.claude/rules/{operating-doctrine,chatman-equation,dfcm-composition}.md`
(projected into `~/.zcode/AGENTS.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md`).

## Conservation rules (added after the W0 audit, 2026-09-22)
- Fetch with `git fetch --all --tags --no-prune`: repo config `fetch.prune=true` (e.g. autofde-lab) silently prunes
  remote-tracking refs even without `--prune` (lost ref origin/feat/sa2a-gnn-candidate-inference, re-pinned as
  preserve/v26.9.22/origin-feat-sa2a-gnn-candidate-inference).
- Cleaning a checkout (checkout/clean/restore) is lawful ONLY after verifying that a preserve ref covers every dirty and
  untracked path, and the receipt must list the covering ref (L10 did this for beam4pm/ggen-ecosystem/gitvan: content
  now lives only in preserve/v26.9.22/* — never delete those refs).
- Stash commits without a reflog entry (not in `git stash list`) must be pinned too: gymact e3b5fa9 is now
  preserve/v26.9.22/orphan-stash-e3b5fa9.
- Dirty submodule content is snapshotted as refs/preserve/v26.9.22/dirty-snapshot inside each submodule repo.

## Friday Stop Court scope (GC-FRI-0800, added 2026-09-22 21:50 PT) — supersedes open-ended v26.9.22 scope
- The governing object is `GC-FRI-0800` (xaas `docs/sjira/v26.9.22/friday/goal.ttl`, branch `friday/gc-fri-0800`).
  STOP = gates G0..G12 all ALIVE ∧ remaining frontier ⊆ Successor|Blocked|Unsupported|Refused ∧ no required UNKNOWN ∧ no
  LLM on the KNOWN path. Court: `mix xaas.stop_court --checkpoint GC-FRI-0800`.
- Critical path = ggen_igniter + xaas only, integrated on `friday/gc-fri-0800` (worktrees /Users/sac/wt/v26922/fri/<repo>-int),
  NOT on the shared release/v26.9.22 int worktrees. Reserved files (do not edit outside the Friday lanes):
  ggen_igniter priv/ggen/semantic-jira-pack/{ontology.ttl,shapes/*}; xaas lib/xaas/ultracode/{recipe_worker,engine,court_receipt,
  target_suites,semantic_receipt,semantic_crown}.ex, lib/xaas/sa2a/route.ex, lib/mix/tasks/xaas.stop_court.ex, docs/sjira/v26.9.22/friday/**.
- Everything else (the 176 v26.9.22 orders, ZCode lanes L2–L8/L10, takeover runtime, ggen-ecosystem crown laws, ZOE Wednesday) is
  successor GC-026923: keep working if useful, but it cannot hold Friday open and must not modify reserved files.
- Exception on the critical path: ZCode L1 WO-03 (mix semantic_jira.* restore) — Friday lanes fix-forward its two known defects
  (cli.ex TransitionLog.read returns a list; build_xaas_contract must admit the eligible row) after it merges.
- 2026-09-22 21:45 PT: ZCode L1 WO-03 was idle since 18:54 (no process cwd in wo-03). Its WIP is preserved as
  ggen_igniter `preserve/v26.9.22/wo-03-wip` and ADOPTED by Friday lane FRI-T6 (branch fri/FRI-T6). ZCode L1: do not
  continue WO-03 in wo-03; the restored mix semantic_jira.* surface lands via friday/gc-fri-0800.

## v26.9.23 scope (GC-26.9.23, added 2026-09-22 23:25 PT) — successor of GC-FRI-0800
- Operator-accepted product contract: `/Users/sac/wt/v26922/v26923/prd-ard.md` (PRD + ARD, verbatim; committed as xaas
  `docs/sjira/v26.9.23/prd-ard.md`). Governing object `GC-26.9.23` (xaas `docs/sjira/v26.9.23/goal.ttl`), gates GC23-0..12,
  STOP per PRD §13. GC-FRI-0800 results are predecessor evidence (PRD §24 M3); its gates G1..G11 share courts with GC23.
- Driver protocol and wave state: `/Users/sac/wt/v26922/v26923/DRIVER.md`. Lanes: branch `v23/<LANE>`, worktree
  `/Users/sac/wt/v26922/v23/<LANE>`, receipts `receipts/v26.9.23/<LANE>.json`, integrated into the same critical-path int
  worktrees `/Users/sac/wt/v26922/fri/<repo>-int` (branch `friday/gc-fri-0800`).
- Merge lock for the fri int worktrees (both Friday and v26.9.23 lanes, every executor):
  `until mkdir /Users/sac/wt/v26922/fri/<repo>-int.merge.lock 2>/dev/null; do sleep 15; done` + owner file; release with
  rm owner + rmdir. (The `/Users/sac/wt/v26922/<repo>/.merge.lock` lock above guards the release/v26.9.22 int worktrees only.)
- Non-required work (PRD §10 non-goals, the 176 v26.9.22 orders, ZCode lanes, takeover runtime, crown laws) is successor
  `GC-26.9.24`; GC-026923 folds into it. It may continue but cannot hold GC-26.9.23 open (PRD PR-017, falsifier F8).

## Cleanup policies (driver decisions, 2026-09-23 14:25 PT)
- Per-checkout ggen signing keys (`*.key` other than `verifying.key`, gitignored) are ephemeral credentials of that checkout. When a
  worktree is retired, its evidence (receipts, receipt logs, `verifying.key`) is preserved in a `refs/preserve/v26.9.23/cleanup/*` commit;
  the private key is retired with the checkout and only its sha256 is recorded. A private key is never written into any git object.
- `git worktree remove --force` is lawful for a clean superproject whose initialized submodules are each clean and whose HEADs are reachable
  from the submodule's own remote refs (reproducible from the gitlinks); any other submodule is preserved inside its own repo first.
- Dirty observation worktrees (e.g. W0 baselines) are PRESERVE_THEN_REMOVE; another executor's active worktree is left until it has been idle
  for 12 h.
- SECURITY (found 2026-09-23 14:52 PT by the cleanup-2 skeptic + driver scan): PUBLIC repos seanchatmangpt/gymact and
  seanchatmangpt/open-ontologies track `.ggen/keys/signing.key` on their default branches (committed ggen receipt-signing private keys).
  Treat both keys as compromised: receipts they signed carry no signing authority. Remediation is operator-owned (key rotation was out of
  scope): rotate the keypairs, stop tracking the key (+ .gitignore), and fix the generator default in ggen so `.ggen/keys/signing.key` is
  never committable. History is not rewritten (no force-push). Filed as successor GC-26.9.24 (security).
