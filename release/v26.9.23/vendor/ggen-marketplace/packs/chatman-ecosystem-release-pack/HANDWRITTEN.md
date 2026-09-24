# HANDWRITTEN.md

Code in this pack that is not ontology, gate, template or generated projection. Every row is
`UNSUPPORTED(generator-capability)` with the reason no generator covers it. Vocabulary,
gates 070-097, the disposition rule and all twelve templates are pack capital, not residue.
Version 0.4.0 (release court, typed checks, root receipt) adds no product code residue: the court
script, its import re-hash, probe and observation writer (including the court-input set), the
typed-checks list, IMPORTS.sha256 and both receipts are rendered by ggen from graph facts, and the
standing derivation is a template `construct:`. Its only new residue is qualification-side
(`qualify.sh` step 7, `qualification/chatman-harness/`).

| path | standing | reason | owner |
|---|---|---|---|
| `lift/manifest_to_er.py` | UNSUPPORTED(generator-capability) | ggen renders RDF into text; it does not parse TOML into RDF. No marketplace pack lifts TOML to RDF: star-toml-pack generates Rust config structs, and the tomllib users in autofde-semantic-registry-pack and the xaas public-ontology profile are not RDF importers. 32 lines of stdlib tomllib, deterministic, lifted-observation output only. | this pack (manifest-import step) |
| `bin/run-gates.py` | UNSUPPORTED(generator-capability) | Reused from `packs/gym-autonomic-crown-pack/bin/run-gates.py` and extended to union the consumer's `ggen.toml` imports and apply the templates' `construct:` rules. It is the second, independent executor (rdflib next to ggen's own engine) of the same gates; ggen has no mode that runs a pack's gates outside a consumer sync. | this pack |
| `bin/import-crown-lift.py` | UNSUPPORTED(generator-capability) | ggen renders RDF into text; it does not parse receipt JSON into RDF. The lift is generic for any upstream stop-court crown (STOP receipt found by `identity.subject` `<checkpoint>/STOP`, gate receipts by `gate.checkpoint`, gate count from the court's own `N/M gates ALIVE`, paired field configurable) and its output is a pure function of the receipt bytes and the two bound SHAs. Prototype: the scan's 31-line lift_ttl.py; this is 66 lines of stdlib. | this pack (crown-import step) |
| `bin/import-crown-generate.sh` | UNSUPPORTED(generator-capability) | Orchestration only (lift, explicit runner, `ggen sync run`, byte comparison), following `packs/gym-autonomic-crown-pack/bin/crown-generate.sh`; ggen has no mode that lifts JSON, re-checks a committed lift and diffs a committed render in one command. Read-only on the consumer. | this pack |
| `qualification/fixtures/derive-fixtures.py` | UNSUPPORTED(generator-capability) | Provenance replay for the imported-crown fixtures: re-derives every fixture directory from real xaas git blobs (checked by object id) and records each qualification rewrite in the rewritten receipt itself. | this pack |
| `qualification/qualify.sh` | UNSUPPORTED(generator-capability) | Qualification harness (real ggen, real rdflib, real git repositories and the rendered court script in scratch copies; no mocks). The marketplace's `scripts/qualify_packs_r18.py` renders a pack once against `qualification/consumer.ttl` but has no mutant/expected-refusal contract. Step 7 (0.4.0) drives sync -> court -> sync, a fresh-render reproduction, the check that the committed observation is of the current pack tree and names the whole court input, the typed-exit witnesses (gate order, 100, 101, 103, a command syntax error), the unobserved (UNOBSERVED, R_missing_identity) and PARTIAL_ALIVE broken_term witnesses, the ALIVE-before witnesses with their construct anti-vacuity copy, `court-mutants.EXPECTED.tsv` (including the consumer-extension and ontology-drift rows C13-C19, the stale-observation rows C20-C27 and the release-law rows C28-C35, run concurrently), step 5's run of each graph mutant without its named gate, and step 7j, which requires every `gates/*.rq` to be the sole refusing gate of at least one passing mutant. | this pack |
| `qualification/chatman-harness/` (`Cargo.toml`, `src/main.rs`) | UNSUPPORTED(generator-capability) | 40-line Rust binary for qualify step 7h/7i: the `receipt seal` / `receipt verify-all` arms of chatman-ecosystem `apps/ecosystem-cli/src/main.rs` at c59596f5 over the same `ecosystem_core::seal_all_receipts` / `verify_all_receipts` functions and output lines, without the CLI's deploy/MCP dependency tree. It holds no receipt law of its own: qualify builds it against ecosystem-core extracted byte-for-byte from c59596f5 (`CHATMAN_REPO`), so the seal and the 25-pair `Standing::permits` differential execute chatman's code. No marketplace pack generates a Rust client over another repository's crate API. | this pack (qualification only) |

The fixture inputs under `qualification/` are byte copies or lifted observations of real sources,
not handwritten facts; `qualification/consumer-v26.9.23/SOURCES.md` records each source and sha256.
The imported-crown fixtures (`qualification/fixtures/*-receipts/`) are derived by
`derive-fixtures.py` from real xaas receipt blobs; every qualification rewrite (the positive
witness's STOP=true and ALIVE gates, and each one-change mutant) is recorded inside the
rewritten receipt's `qualification_rewrite` object and in `qualification/fixtures/SOURCES.md`.
The two fixture-only choices (the target release's role names and constitutional mappings in
`consumer-v26.9.23/release.ttl`) are qualification data, not v26.9.23 release decisions; so are
its 0.4.0 court facts (gates, probes, the typed check, imports, root receipt). Its `observed.ttl`
is the court's own output (`COURT_OBSERVED`), not hand-written; `qualify.sh` step 7 requires a
fresh court run to reproduce it (subject line excepted). `qualification/chatman-receipt.schema.json`
is a byte copy of chatman-ecosystem `schemas/receipt.schema.json` at c59596f5.
