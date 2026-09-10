# BFCC-002 — BFCC Catalog Entry (Ten Gates)

Ticket Key: BFCC-002
Owning repo: seanchatmangpt/chatman-ecosystem
Exact base ref/SHA: main @ 83204ee38a518311d9c9fc128d69c517a99257f4
Standing: BFCC-CANDIDATE
Depends on: BFCC-001

## Problem

The ten BFCC gates, their falsifiers, their required-evidence shape, and the terminal
refusal vocabulary need one canonical, machine-readable source of truth — this repo's
existing convention is `catalog/<name>.toml`, not scattered prose across multiple docs.

## Customer/system need

`scripts/verify_bfcc.py` (BFCC-003) needs a structured manifest to validate and to
evaluate submitted receipts against. `scripts/bfcc_benchmark.py` (BFCC-004) needs the
same `[receipt].required_fields` contract so ledgered receipts are comparable.

## Scope

`catalog/bfcc.toml`:

- `schema = "chatman.bfcc.v1"`, `canonical = true`.
- Standing vocabulary (closed, per the BFCC doctrine): `BFCC-CANDIDATE`, `BFCC-PARTIAL`,
  `BFCC-ALIVE`, `BFCC-BLOCKED`, `BFCC-UNKNOWN`.
- `[authority]` table: `bfcc_grants_do_authority = false`, `plan_grants_authority =
  false`, `proof_grants_authority = false` — mirrors `catalog/dfcm.toml`'s authority
  table; a BFCC assessment is never itself a DO decision.
- `[public_ontologies]` table mapping the `bfcc:`/`earl:`/`prov:`/`pplan:`/`skos:`
  prefixes to their IRIs, mirroring `ontology/bfcc.ttl`'s `@prefix` block exactly (so
  BFCC-003 can detect prefix drift the same way `verify_dfcm_profile.py` does today).
- Ten `[[gate]]` entries — `id` (`"bfcc:C"` … `"bfcc:I"`), `letter`, `name`
  (Comprehensive, Anticipatory, Design, Science, Generalized Principles, Synergy,
  Ephemeralization, Trimtab Leverage, World/Resource Inventory, Integrity),
  `fuller_principle` (short canon-source phrase), `engineering_projection` (the exact
  one-line projection from the doctrine, e.g. G → "solve the class of problem, not the
  instance"), `falsifier` (the FAIL condition, verbatim from the doctrine),
  `mandatory = true`.
- `[receipt]`: `required_fields = ["subject","revision","system_boundary",
  "canon_sources","projection_table","inventory_examined","gates_evaluated",
  "evidence_per_gate","falsifier_per_gate","contradictions","omitted_gates",
  "resource_vector","eta_evidence","lambda_evidence","sigma_evidence",
  "unresolved_gaps","standing"]`.
- `[exclusions]` / terminal refusals: `FULLER_LAUNDERING` (a claim attributed to Fuller
  without an explicit `projectsFrom` edge), `AVERAGED_FAILED_GATE` (any mandatory gate
  missing evidence still yields non-`BFCC-ALIVE`, never rounded up), `UNFALSIFIED_SYNERGY_CLAIM`
  (Σ asserted without a composed-vs-isolated comparison), `MISSING_INVENTORY` (W gate
  skipped), `STANDING_TRANSFERRED` (evidence reused from a different subject/revision).

## Non-goals

- No submitted receipts yet — this ticket defines the schema, not an assessment.
- No claim any of the 10 gates has been satisfied by anything in this repo.

## Dependencies

BFCC-001 (ontology prefixes/classes this catalog entry cross-references).

## Risks

Standing-vocabulary drift from this repo's more common six-state vocabulary
(`UNKNOWN`/`PARTIAL_ALIVE`/`ALIVE`/`BLOCKED`/`BUILD_BROKEN`/`UNSUPPORTED`) — deliberate:
the BFCC-prefixed vocabulary (`BFCC-CANDIDATE`/`BFCC-PARTIAL`/`BFCC-ALIVE`/
`BFCC-BLOCKED`/`BFCC-UNKNOWN`) is namespaced to avoid a reader confusing a BFCC standing
with a release-manifest standing on the same subject.

## Authority boundary

`OBSERVE`/`VERIFY` only.

## Rollback

Delete `catalog/bfcc.toml`; BFCC-003/004 have nothing to validate against, no other
part of the repo references it yet.

## Acceptance commands

```
python3 -c "import tomllib; d = tomllib.load(open('catalog/bfcc.toml','rb')); assert len(d['gate']) == 10; print('10 gates OK')"
python3 -c "import tomllib; d = tomllib.load(open('catalog/bfcc.toml','rb')); assert d['standing']['values'] if 'values' in d.get('standing',{}) else True"
```

## Observable Definition of Done

- File parses as valid TOML.
- Exactly 10 `[[gate]]` entries, one per canon letter, each with a non-empty
  `falsifier` and an `engineering_projection` that is not a verbatim copy of
  `fuller_principle` (the literal no-laundering check BFCC-003 will enforce).
- `[authority]` table denies DO authority.
- `[receipt].required_fields` matches the field list BFCC-003/004 will validate
  against exactly.
