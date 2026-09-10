# BFCC-003 — BFCC Verifier

Ticket Key: BFCC-003
Owning repo: seanchatmangpt/chatman-ecosystem
Exact base ref/SHA: main @ 83204ee38a518311d9c9fc128d69c517a99257f4
Standing: BFCC-CANDIDATE
Depends on: BFCC-001, BFCC-002

## Problem

`catalog/bfcc.toml` (BFCC-002) is a manifest, not a check. Without a verifier, nothing
in the repo can actually distinguish a well-formed BFCC manifest from a malformed one,
or evaluate a submitted assessment receipt against it, so "BFCC-ALIVE" stays
unfalsifiable.

## Customer/system need

Any future subject (a repo, a module, a change) that wants to claim BFCC compatibility
needs a real command to run that either admits or refuses that claim with a typed
reason — the same discipline `scripts/verify_dfcm_profile.py` and
`scripts/verify_formal_discovery_loop.py` already provide for their own domains.

## Scope

`scripts/verify_bfcc.py`, following `verify_formal_discovery_loop.py`'s split (fits
BFCC better than the flat `verify_dfcm_profile.py` shape because BFCC has a real
receipt-evaluation phase distinct from manifest structure):

- `validate_manifest(catalog: dict) -> list[str]` — structural: all 10 gates present;
  each has a non-empty `falsifier`; each `engineering_projection` is textually distinct
  from its `fuller_principle` (the literal Fuller-laundering check — refuse
  `FULLER_LAUNDERING` if a gate's projection is just the canon phrase restated with no
  engineering-specific noun); `[authority]` denies DO; `[receipt].required_fields`
  present and non-empty.
- `evaluate_receipt(catalog: dict, receipt: dict) -> str` — receipt-driven: every
  mandatory gate must have a non-empty entry in both `evidence_per_gate` and
  `falsifier_per_gate`; refuse `AVERAGED_FAILED_GATE` if any mandatory gate lacks
  evidence while the receipt's own `standing` field claims `BFCC-ALIVE`; refuse
  `UNFALSIFIED_SYNERGY_CLAIM` if `sigma_evidence` is empty but the receipt's prose
  claims a synergy/composition benefit; refuse `STANDING_TRANSFERRED` if `subject`/
  `revision` don't match what the evidence entries themselves cite; return
  `BFCC-PARTIAL` if evidence is incomplete but non-contradictory; return `BFCC-ALIVE`
  only if every mandatory gate is evidenced and no contradiction exists.
- `argparse`: `--root` (default `.`), `--manifest` (default `<root>/catalog/bfcc.toml`),
  `--receipt` (optional), `--json`. No `--receipt` given → print `MANIFEST_ALIVE`,
  exit 0 (mirrors `verify_formal_discovery_loop.py`'s zero-receipt case — this only
  confirms the manifest itself is well-formed, never that any subject is compatible).
- Exit codes: `0` = ALIVE/manifest-well-formed, `2` = REFUSED, `3` = PARTIAL_ALIVE.

`tests/test_bfcc.py`:

- Plain `unittest`, real fixtures (`catalog/bfcc.toml` read off disk via `tomllib`,
  never mocked — this repo's Chicago-style testing rule).
- One test asserting the canonical `catalog/bfcc.toml` validates as-is.
- One test per terminal refusal (`FULLER_LAUNDERING`, `AVERAGED_FAILED_GATE`,
  `UNFALSIFIED_SYNERGY_CLAIM`, `MISSING_INVENTORY`, `STANDING_TRANSFERRED`) — each
  triggered by mutating a `copy.deepcopy` of the real fixture, never a fabricated
  minimal dict.
- One test each for the `BFCC-ALIVE`/`BFCC-PARTIAL`/refused receipt-evaluation paths
  using a small, real, hand-written fixture receipt dict.

## Non-goals

- No SHACL execution against `ontology/bfcc.shacl.ttl` in this ticket — structural
  validation here is TOML-level only; a SHACL-execution gate is a candidate future
  ticket if the ontology-vs-catalog correspondence needs machine enforcement beyond
  what `validate_manifest()` already checks by hand.
- No receipt-generation tooling — this ticket only evaluates receipts someone else
  produced, per the existing repo pattern of separating manifest verification from
  assessment authorship.

## Dependencies

BFCC-001 (ontology terms referenced in prefix-drift checks), BFCC-002 (the manifest
this verifies).

## Risks

A verifier that's too permissive would let `BFCC-ALIVE` become as unfalsifiable as
plain prose — mitigated by the mandatory adversarial test-per-falsifier requirement
above and by never allowing partial gate coverage to round up to `BFCC-ALIVE`.

## Authority boundary

`OBSERVE`/`VERIFY` only. Running this script performs no DO action.

## Rollback

Delete `scripts/verify_bfcc.py` and `tests/test_bfcc.py`; no other script imports them
yet.

## Acceptance commands

```
python3 -m unittest discover -s tests -p test_bfcc.py -v
python3 scripts/verify_bfcc.py --root . --json
python3 scripts/verify_bfcc.py --root .
```

## Observable Definition of Done

- `python3 -m unittest discover -s tests -p test_bfcc.py -v` — all green, real output
  pasted, not described.
- `python3 scripts/verify_bfcc.py --root .` → `MANIFEST_ALIVE`, exit 0.
- Every one of BFCC-002's five terminal refusals has a passing test that triggers it
  via a real mutated fixture, not a synthetic minimal dict.
- `grep -rn "unittest.mock\|Mock(\|MagicMock\|patch(\|monkeypatch" tests/test_bfcc.py`
  returns zero matches (Chicago-style testing discipline, verified not assumed).
