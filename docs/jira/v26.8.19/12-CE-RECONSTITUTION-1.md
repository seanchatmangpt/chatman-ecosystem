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

The checklist and the benchmark scripts exist; whether any real subject in this repository has
ever been run through the full 16-item checklist to completion, with an original implementation
actually deleted afterward, was not checked in this pass — that would require reading
`33-reconstitution.md` in full and finding a concrete completed instance, not inferring one from
the checklist's existence. This is the honest state: the *mechanism* for `ce-reconstitution/1`
is unusually well-built already; a *completed example* of it running end-to-end was not
confirmed here.

## Explicit non-claims

- The checklist, benchmark, and verify script are confirmed to exist; a completed end-to-end
  reconstitution instance is not confirmed, not denied — unchecked in this pass.
- No external party has reviewed or ratified this fragment.
