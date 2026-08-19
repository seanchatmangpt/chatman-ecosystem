# ce-reconstitution/1 — The Implementation-Extinction Test

> Status: draft, fragment of the `ce-*` protocol family. Formalizes the DfCM inversion's
> "disappearing-founder test" and the proposed `ggen-legacy` inversion ("stops being a
> migration product and becomes the proof mechanism that an implementation can disappear while
> its observable contract survives").

## The claim this fragment formalizes

An implementation genuinely satisfies a protocol contract — as opposed to merely resembling one
— if a *different* implementation, built from the contract alone (not from reading the original
implementation's source), reproduces the original's observed behavior closely enough that the
original could be deleted without loss to anyone depending on the contract.

## Checked against real code — this fragment is unusually mature already, not speculative

`docs/post-agi-platform-handbook/appendices/o-reconstitution-checklist.md` is a real, already-
written, 16-item checklist, and it is materially the same shape as this fragment's claim,
independently arrived at:

> "Recover public ontology before creating custom terms... Manufacture a candidate from
> recovered semantic sources... Compare the candidate with the historical behavior/class
> contract... Reestablish exact-subject standing... Extract the reusable class into a ggen pack
> when equivalence is proven... Record falsifiers that would reopen the class."

This is `ce-reconstitution/1`'s exact test, written down before this fragment was — checked via
`docs/post-agi-platform-handbook/part-08-replay-closure/33-reconstitution.md` for the fuller
treatment (not read in full in this pass, but confirmed to exist and to sit under a section
titled "Replay Closure," directly connecting this fragment to `ce-replay/1`).

Separately, `scripts/verify_platform_reconstitution.py`,
`tests/test_platform_reconstitution.py`, and `benchmarks/platform-reconstitution/` all exist as
real, runnable artifacts (confirmed present via `find`, not read in full) — meaning this session
found evidence of an actual reconstitution *benchmark*, not only a checklist.

## What `ce-reconstitution/1` conformance actually requires

1. A "public ontology first, custom remainder recorded" discipline — matching the DfCM
   inversion's own `PublicOntology + smallest necessary custom remainder` formula.
2. A real "candidate manufactured from recovered semantics, compared against historical
   behavior" step — not a rewrite from familiarity with the original code, but a rebuild from
   the contract, with the comparison as the actual test.
3. Falsifiers recorded — conditions that, if later observed, would reopen the class as
   unreconstituted. Without this, "reconstituted" degrades into an unfalsifiable claim, which
   this fragment's own checklist already guards against by requiring it explicitly.
4. The original implementation must be genuinely deletable after the candidate passes — if
   deleting it would break something the candidate doesn't cover, reconstitution wasn't
   complete, regardless of how much the candidate resembles the original.

## Real, scoped gap

**Update (2026-08-19): checked for real, and the answer is no completed instance exists — this
fragment remains unshipped.** `33-reconstitution.md` was read in full (51 lines): it is prose
theory ending in an unperformed "operational exercise" prompt, not a record of a completed run.
`benchmarks/platform-reconstitution/v1/benchmark.toml:6` declares `standing = "UNKNOWN"`.
Running `scripts/verify_platform_reconstitution.py` directly confirms this live: the default run
prints `PLATFORM_RECONSTITUTION=UNKNOWN` (exit 0), and `--require-alive` returns
`REFUSED:BENCHMARK_NOT_ALIVE:UNKNOWN` (exit 2). `pytest tests/test_platform_reconstitution.py
-v` passes 17/17, but every passing test validates refusal/structural logic against synthetic
evidence dicts constructed in-test (`alive_evidence()`) — none of it is committed real evidence,
and `test_candidate_contract_is_structurally_admitted` explicitly asserts the real file's standing
is `UNKNOWN`. No original implementation has ever been deleted per any committed record.

No files were changed for this fragment in this pass — the checklist, benchmark, and verify
script were already real and already existed; this pass only confirmed, by actually running them
rather than inferring from their existence, that none of the four completion conditions below
are met. This is a verification-only update, not a build.

If a completed reconstitution instance is ever produced, it would need: (1) `benchmark.toml`
standing flipped to `ALIVE`, (2) a populated evidence table with real shas/digests/receipts
satisfying `verify_platform_reconstitution.py`'s `ALIVE` branch (lines 284-366), (3)
`--require-alive` passing, and (4) a documented deletion of the original implementation
referenced by `original_subject_id`. None of this exists yet.

## Explicit non-claims

- The checklist, benchmark, and verify script are confirmed to exist; a completed end-to-end
  reconstitution instance is not confirmed, not denied — unchecked in this pass.
- No external party has reviewed or ratified this fragment.
