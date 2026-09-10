# BFCC-007 — v26.9.10 Case Study: HTN/FOND/HDDL Episode as First BFCC Assessment Subject

Ticket Key: BFCC-007
Owning repo: seanchatmangpt/chatman-ecosystem
Exact base ref/SHA: main @ 83204ee38a518311d9c9fc128d69c517a99257f4
Standing: BFCC-CANDIDATE
Depends on: BFCC-001, BFCC-002, BFCC-003, BFCC-004, BFCC-005, BFCC-006

## Problem

BFCC-001 through BFCC-006 build the standard but assess nothing. The user supplied a
concrete candidate first subject — a development episode (HTN/hierarchical planning,
FOND under nondeterminism, HDDL solving, exposed through Ferroplan/Beam4pm/Ex4pm/
AshEx4pm) that plausibly demonstrates several BFCC gates in one bounded chain:
inventory before invention (W), a repository-boundary correction (C), a canonical
ontology extension as the highest-leverage intervention (T), a forward-declared-vs-live
distinction encoded in the system rather than left as tribal knowledge (D), a staged
transition plan (A), a generalized state-representation fix instead of a special-case
patch (G), an explicit refusal of unsupported scope instead of silent partial
implementation (I), a downgraded test-count claim and a preserved CI-coverage gap (S),
a removed planned dependency (E), and a claimed but not-yet-earned synergy (Σ).

## Important scoping note — subject location

**Checked in this repo, not assumed:** `beam4pm` and `ferroplan` are not committed
parts of `chatman-ecosystem`. The only matches found (`find . -iname "*beam4pm*"`) are
session-scratch checkouts under `.ws2work/beam4pm` and `.ggen-verify-tmp/vendor/beam4pm`
— both already gitignored this session as accidental scratch artifacts, not real
repo content. The HTN/FOND/HDDL episode this ticket assesses happened in a sibling
repository this session has not independently inspected. Every quantitative claim in
the user's case study (test counts, the ~1.8ms/20s+ timing comparison, the 112,000-state
figure, the "141 vs 227 tests" correction, dependency-manifest/subprocess/code-copy
zero-count claims) is **carried here as-reported, not independently re-verified by
this session** — treat them as the subject's own claimed evidence, to be checked for
real during the actual BFCC-003 assessment run this ticket schedules, not accepted now.

## Customer/system need

A worked example proves BFCC-003's verifier actually distinguishes real evidence from
narrative, and gives BFCC-004's benchmark its first real ledger entry.

## Scope

1. Once BFCC-001–006 land, run `scripts/verify_bfcc.py` in receipt-evaluation mode
   against a real, hand-authored receipt for this episode, with `subject` pointing at
   the exact repo/commit(s) where the HTN/FOND/HDDL work actually landed (to be
   identified — not this repo).
2. For each of the ten gates, populate `evidence_per_gate` only with claims this
   session (or a future session with access to that repo) has independently checked
   against real files/commits/CI runs — not transcribed from the user's prose. Where
   independent verification isn't yet possible, the gate's evidence entry states that
   explicitly and the receipt's overall `standing` stays `BFCC-PARTIAL` or
   `BFCC-UNKNOWN`, never rounded up.
3. Record the result as the first row in `.artifacts/bfcc/receipts.jsonl` for
   BFCC-004's benchmark to aggregate.
4. Write up the assessed result (not the user's original narrative) as
   `docs/BFCC-CASE-STUDY-v26.9.10.md`, following this repo's provenance-record
   convention (`docs/jira/v26.8.21/00-PROTOCOL-VISION-NOW.md`'s "Verdict, stated
   first" / "Real state today" structure) rather than press-release framing — the
   press-release register is fine for the user's own exploratory writing, but this
   repo's evidentiary docs use `no-overclaiming-conversational.md`'s register instead.

## Non-goals

- This ticket does not itself claim `BFCC-ALIVE` for the episode — that's an outcome
  of running the assessment, not a premise of writing the ticket.
- No re-derivation of the blocksworld performance numbers or test counts in this
  ticket — those get checked when the assessment actually runs against the real
  subject repo, with real command output pasted.

## Dependencies

BFCC-001 through BFCC-006 (the full standard must exist before it can be applied).
Access to the actual sibling repo(s) where Ferroplan/Beam4pm/Ex4pm/AshEx4pm live —
not yet confirmed available to this session.

## Risks

The largest risk is exactly the failure mode BFCC-S exists to prevent: treating a
well-written narrative as evidence. This ticket's own scope section is written to
guard against that by requiring independent re-verification per gate before any
evidence entry is written, not transcription of the user's claims.

## Authority boundary

`OBSERVE`/`VERIFY` only.

## Rollback

Delete the receipt ledger row and `docs/BFCC-CASE-STUDY-v26.9.10.md`; no other
artifact depends on this specific assessment.

## Acceptance commands

```
python3 scripts/verify_bfcc.py --root . --receipt .artifacts/bfcc/receipts/htn-fond-hddl-v26.9.10.json --json
python3 scripts/bfcc_benchmark.py --receipts .artifacts/bfcc/receipts.jsonl --json
```

## Observable Definition of Done

- A real receipt file exists with `evidence_per_gate` entries each traceable to a
  specific checked file/commit/CI-run in the actual subject repo.
- `scripts/verify_bfcc.py --receipt <that file>` returns a standing consistent with
  the evidence actually gathered (expect `BFCC-PARTIAL`, not `BFCC-ALIVE`, until every
  mandatory gate — especially Σ synergy, which the ticket above flags as "claimed but
  not yet earned" — has real end-to-end verification, not component-level evidence
  alone).
- `docs/BFCC-CASE-STUDY-v26.9.10.md` states plainly which of the user's original
  claims were independently confirmed, which were not yet checked, and which (if any)
  were found inaccurate on inspection.
