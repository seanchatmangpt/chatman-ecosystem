# chatman-ecosystem migration plan v26.11.16

Standing: UNVERIFIED

## Identity
- Path: /Users/sac/chatman-ecosystem
- Remote: https://github.com/seanchatmangpt/chatman-ecosystem.git (origin, 101 remote branches)
- Branch: docs/v27927-closed-manufacture-loop@83ceef8a — last commit 2026-10-02 —
  4954 commits on this branch (origin/main 5010) — 601 MB (.git 315 MB)
- Languages/build: Rust workspace (Cargo.toml, deny.toml, rust-toolchain.toml), Makefile,
  Python (pyrightconfig, .ruff_cache), mdBook (book.toml), west manifests
- Submodules: platform-console/services/gymact, platform-console/services/autofde-lab
  (both uninitialised)
- Nested repos: none beyond the two submodules

## Observed state
- Dirty 0 / untracked 0; ahead 0 / behind 0 vs origin/docs/v27927-closed-manufacture-loop
- stash 0
- Unpushed local branches 23 (no upstream): archive/local-lineage/{exp/pr3-..., main,
  preserve/v26.9.22/main, release/v26.9.22}, feat/aloop-crown-001,
  feat/next-calver-autonomic-crown, feat/v26.9.25-{evidence-binding, hardening-outputs,
  mutation-harness, post-tag-crown, terminality-policy}, fix/v26.9.25-court-minors, plus
  feat/v26.9.25-r25-018-standing-split tracking origin/main (behind 144); the remaining
  local branches do have origin counterparts
- Build dirs: none (no target/); platform-console/ 183 MB; .artifacts/, artifacts/

## What it is
"Standing-bearing software manufacture" — a constitutional control plane composing many
repos, ontologies, receipts and courts (A = mu(O*), R = receipt(A)). Large monorepo of
Rust crates, docs, schemas, and release machinery.

## Classification
ACTIVE (census agrees; checkout is clean but branch-heavy).

## Migration risk
- ~12 local-only branches with unique commits (v26.9.25 crown/mutation/terminality work,
  archive/local-lineage preserve snapshots)
- Current HEAD is a docs branch, not main — easy to lose track of which branch is "live"
- No .env/.db observed at top level
Rate: MEDIUM

## Recommended action
COMMIT-PUSH
1. `cd /Users/sac/chatman-ecosystem && git branch -vv | grep -v '\[origin'` — list local-only
2. DECISION: which of the 23 local branches are worth keeping vs archive-only
3. Push keepers: `for b in <list>; do git push -u origin "$b"; done`
4. Safety net for everything: `git bundle create /Volumes/<archive>/chatman-ecosystem.bundle
   --all` (captures every local branch regardless of decision)
5. No build dirs to remove; do not rsync; clone fresh on the new machine
6. `git clone https://github.com/seanchatmangpt/chatman-ecosystem.git &&
   git submodule update --init platform-console/services/gymact
   platform-console/services/autofde-lab` (only if those services are needed)

## First commands on the new machine
`make check` if present, else `cargo check --workspace` (stated, not run).

## See Also
- ../v26.9.25/
- /Users/sac/docs/jira/v26.11.16/README.md
