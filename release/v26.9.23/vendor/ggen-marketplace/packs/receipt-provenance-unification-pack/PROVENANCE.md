# PROVENANCE — receipt-provenance-unification-pack

## Authority boundary

This pack carries **no runtime actuation authority**. It generates four
artifacts:

1. `generated/unified_receipt_validator.py` — a predicate over JSON
   documents. It opens a receipt read-only, runs only **read-only git probes**,
   returns a verdict, and exits. It writes nothing, mutates no git state, and
   admits nothing. The probes are ontology facts (`rp:ResolutionKind`), each
   an argument vector after `git -C <repo>`:
   - `cat-file -e <sha>^{commit}` (subject_commit),
   - `cat-file -e <sha>:<path>` (blob_at_commit),
   - `merge-base --is-ancestor <subject_sha> <sha>` (ancestor_of),
   - `notes --ref=<ref> list <sha>` (notes_object).

   `gates/05_probes_read_only.rq` refuses any other argv in the ontology, and
   the generated module refuses at run time any probe whose argv does not
   start with one of those prefixes.
2. `generated/receipt_contract_matrix.json` — data (a census).
3. `generated/gate_report.json` — data (the gate verdicts).
4. `generated/qualification_runner.py` — test harness. It runs the validator
   on the fixtures under `qualification/`, and creates one throwaway git
   repository under the system temp directory (removed afterwards) to exercise
   the git-notes location. It is not on any product path.

Consequential DO — writing a receipt, admitting an actuation, moving a gitlink,
publishing a release — stays behind GymAct/BRCE admission and is out of scope
here. `gates/01_no_actuation.rq` refuses any individual in this ontology that
claims actuation authority.

## Where every fact came from

Every `rp:ReceiptContract` and `rp:Validator` individual in `ontology.ttl`
carries `rp:sourceFile` (gate 02). Every fact of the `dfcm_fleet_v1` contract,
and every `rp:ImplicationRule`, `rp:ResolutionKind`, `rp:LocationAlternative`
and `rp:Profile`, carries both `rp:sourceFile` and `rp:sourceLine` (gate 04).
Nothing here was inferred from a repo name or a field name.

| Contract | Read from |
|---|---|
| `ecosystem_sync` | `vendor/ggen-ecosystem/docs/RECEIPT-SCHEMA.md` + `scripts/verify-receipt.sh` |
| `ecosystem_bootstrap` | `vendor/ggen-ecosystem/receipts/bootstrap-ggen-ecosystem-sync.json` |
| `gym_autonomic_crown` | `artifacts/autonomic-crown.json` + `scripts/crown-submodules.py` |
| `autofde_ledger` | `vendor/autofde-lab/src/autofde_lab/receipts/receipt.schema.json` + `receipt_store.py` |
| `clean_session` | `vendor/autofde-lab/schemas/chatman-clean-session-receipt.schema.json` |
| `dfcm_fleet_v1` | `/Users/sac/.claude/dfcm/receipt.schema.json` (sha256 `c19451fa…`) + `/Users/sac/.claude/dfcm/validate_receipt.py` (sha256 `bc703c76…`) |

The durable profile cites three more sources: the V23-S stop court
(`xaas lib/mix/tasks/xaas.stop_court.ex:277` for the GitHub slug regex,
`:1455` for identity.repo becoming the slug), the schema's own rule for
`replay.durable_location` (`receipt.schema.json:55`, "path tracked in git or
CI artifact, never gitignored tmp"), and PRD 28 (`prd-ard.md:2016`, "a named
receipt without validated contents is not ALIVE").

## dfcm_fleet_v1: default profile and durable profile

- **Default profile** (no flag): exit-code parity with
  `~/.claude/dfcm/validate_receipt.py`, including its JSON Schema edge cases
  (an integral float is an integer; `summary` and `durable_location` may be
  empty strings; a present `null` fails a typed optional field; enums refuse a
  trailing newline while `$`-anchored patterns admit one) and its
  local-directory-only subject probe. `validate_receipt.py` is not edited: it
  is unversioned and its sha256 is the verifier identity V23-S binds into
  every receipt.
- **Durable profile** (`--require-durable [--repo-map owner/repo=path ...]`):
  adds bindings that refuse with `R_missing_identity` (identity.repo not a
  mapped owner/repo slug, or subject_sha not a commit there), `R_missing_replay`
  (durable_location not a resolvable git-notes / git blob / https location)
  and `R_missing_standing` (standing.value with a trailing newline, which the
  schema pattern admits and the ALIVE check then skips).

## Published vocabularies reused

`prov:` (Entity/SoftwareAgent/used), `dcterms:` (title/source),
`dcat:Dataset`, `skos:` (Concept/prefLabel), `dqv:` (QualityAnnotation,
inDimension dqv:Consistency). Only `rp:` terms with no public equivalent are
minted — `rp:dottedPath`, `rp:valueForm`, `rp:reasonDelimiter`,
`rp:contractKey`, and the v26.9.23 generator vocabulary listed in
`ontology.ttl` (array/length/nullability keywords, conditional requirement,
implication rule, broken term, profile, resolution kind, location
alternative, qualification suite).

## What is NOT claimed

- The generated validator reaches **exit-code parity with the real
  `verify-receipt.sh` on the 4 fixtures exercised**, not "on all inputs".
  `verify-receipt.sh`'s forward-compatibility clause (unknown fields permitted)
  is preserved; its exact stderr *wording* is not reproduced.
- **Parity with `validate_receipt.py`** is claimed only on what was run: the
  xaas and ggen_igniter v26.9.23 receipts the MP-RPV lane gate loops over and
  the fixtures under `qualification/fixtures/dfcm_fleet_v1/`. Its output
  wording is not reproduced. Input that is not JSON is a known non-parity
  class: this validator exits 2 (parse error, no verdict), `validate_receipt.py`
  exits 1 through an uncaught traceback.
- An `https` durable location is accepted by **lexical form only**; no
  network probe runs, and the VALID output says so.
- `receipt_store.verify_chain`'s BLAKE3/sha256 **chain-link re-derivation is
  not subsumed** by this pack. Chain verification is an algorithm over an
  ordered ledger, not a field-shape predicate; only `autofde_ledger`'s field
  shapes are covered here. `verify_chain` remains authoritative for the chain.
- `chatman_root_v1` is **not** a contract here: chatman
  `crates/ecosystem-core` `Receipt::verify` owns it.
- No existing pack, script, schema, or receipt outside this pack was modified.
  Adopting the validator in any repo is a separate, human-gated decision.
