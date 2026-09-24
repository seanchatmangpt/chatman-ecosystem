# chatman-ecosystem-release-pack

Reusable release-composition law for dependency-closed, exact-SHA ecosystem releases, plus
(0.2.0) the projections a successor release needs to dispose of every role of its predecessor
without erasing the old topology. The pack holds law, vocabulary, rules and templates only;
every release-instance fact (component SHAs, role names, decisions) is consumer-owned.

Version 0.2.0 serves the Chatman Ecosystem v26.9.23 requirements CE23-1 (independent release
subject) and CE23-2 (explicit disposition of all 16 roles of `release/v26.9.1/manifest.toml`).
Version 0.3.0 serves CE23-3 (import the Semantic Manufacturing crown by exact digest: STOP=true,
all 13 gate receipts admitted) and CE23-8 (`LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH=0` and
`UNRECEIPTED_ACTUATION=0` carried into the root release, not merely documented).
Version 0.4.0 serves CE23-9 (exact-head root court: every court step generated from graph facts,
every non-success check typed) and CE23-10 (root release receipt rendered from the court's own
observations, with a standing transition chatman's receipt law admits).

## Consumer shape

A consumer's `ggen.toml` (frontmatter schema) takes the pack by path or by `git` + `subdir`
pinned to an exact marketplace SHA, and feeds its independent inputs through
`extra_ontologies`, which join the sync closure hash:

```toml
[project]
name = "chatman-ecosystem-release-v26-9-23"

[ontology]
source = "release.ttl"          # the er:Release, its er:Component rows and role mappings

[templates]
dir = "templates"               # tracked, may be empty (.gitkeep)

[packs]
chatman-ecosystem-release-pack = { path = "../..", lock = false, extra_ontologies = [
  "imports/legacy-v26.9.1.ttl",       # lift/manifest_to_er.py output
  "imports/fleet-classification.ttl", # byte copy, identity in er:classificationSource
  "imports/court-references.ttl",     # er:courtReferencesComponent observations
  "imports/ce23-orders.ttl",          # sj:WorkOrder graph for requirements.toml
  "observed.ttl",                     # 0.4.0: the court's own observation (COURT_OBSERVED)
] }
```

`qualification/consumer-v26.9.23/` is a complete, runnable instance of this shape built from
real inputs (see its `SOURCES.md`).

## Vocabulary added in 0.2.0

- `er:LegacyRelease` / `er:LegacyComponent`: lifted predecessor facts. They are not
  `er:Release` / `er:Component`, so gates 010-060 never re-judge frozen facts.
- `er:RoleDisposition` with `er:boundary` in the value class `er:RoleBoundary`
  (`er:ROLE_REQUIRED`, `er:ROLE_SUCCESSOR`, `er:ROLE_BLOCKED`, `er:ROLE_UNSUPPORTED`,
  `er:ROLE_REFUSED`). `er:ROLE_UNCLASSIFIED` is an untyped sentinel that gate 070 refuses.
  Component dispositions (`er:Disposition`) and standings (`er:StandingState`) are unchanged.
- `er:crosswalkFrom` binds the successor release to the predecessor it must dispose.
- Row properties: `er:legacyRole`, `er:legacyComponent`, `er:legacySha`, `er:legacyStanding`,
  `er:sourceRelease`, `er:targetRelease`, `er:reason`, `er:decidedBy`, `er:derivedBy`,
  `er:suppliedBy`, `er:classificationSource`, plus `er:legacyRequiredRole`,
  `er:courtReferencesComponent`, `er:componentId`, `er:sourceSha256`.
- Constitutional mapping: `er:RoleMapping` (`er:releaseRole`, `er:primary`, `er:capability`,
  `er:authorityCeiling`, `er:brceExclusive`) over the 11 `er:ConstitutionalRole` individuals.

## Imported crown (0.3.0)

A receipt schema cannot decide STOP truth: `validate_receipt.py` admits the stale `0/13` STOP
receipt of GC-26.9.23 because its shape is valid. The law is therefore gate 090 over facts
lifted from the receipt bytes.

1. `bin/import-crown-lift.py <receipts_dir> <crown_sha> <paired_sha>` lifts a stop-court receipt
   directory (one STOP receipt, `identity.subject` = `<checkpoint>/STOP`, plus the gate receipts
   whose `gate.checkpoint` is that checkpoint) into an `er:ImportedCrown`: STOP standing, subject
   SHA and byte digest; one `er:ImportedGateReceipt` per gate (standing, subject SHA, paired SHA
   from `gate.ggen_igniter_sha` or `--paired-field`, byte digest); the two CE23-8 counters (a null
   counter is omitted); the court's own gate count (`N/M gates ALIVE`, or `--required-gates`); and
   two `er:ImportedComponent` rows carrying the SHAs the importing release binds. The output has no
   paths or clock, so a committed lift is re-checked with `cmp`.
2. Gate 090 refuses the crown unless every one of these holds: STOP standing ALIVE; STOP digest
   present; `er:requiredGateCount` distinct gates ALIVE at the crown subject; STOP subject SHA =
   crown component commit; every gate receipt ALIVE, digested, at the crown subject and run against
   the paired component commit; both counters present and exactly 0. A multi-valued fact must hold
   for every value, so a union with a second, conflicting fact is refused.
3. `bin/import-crown-generate.sh <receipts_dir> <crown_sha> <paired_sha> <consumer_dir> <workdir>`
   stages the consumer, re-lifts and compares with the committed `imported/crown.ttl`, runs the
   explicit runner, runs `ggen sync run` (native gate 090, FM-PACK-013) and compares
   `out/imported-crown.toml` with the committed render. Exit 0 only when both committed files
   reproduce; exit 3 when nothing is committed yet (a first render proves nothing).

`er:ImportedComponent` is deliberately not `er:Component`: gates 010-060 judge release components,
and a consumer's release graph and imported crown can be unioned without re-judging the crown SHAs
as release rows.

## Release court and root receipt (0.4.0)

Vocabulary: `er:Gate` (`er:gate` from the release, `er:gateOrder` 1..99, `er:gateName`,
`er:command`), `er:Probe` (`er:probe`, `er:probeName`, `er:probeOrder`, `er:command`),
`er:courtRoot` (the court's working directory relative to the consumer root, default `.`),
`er:CheckDisposition` (`er:checkDisposition`, `er:checkName`, `er:checkWorkflow`,
`er:failureClass`, `er:checkBoundary`, `er:checkEvidence`), `er:FailureClass` with the six
operator individuals `er:subject_defect`, `er:environment`, `er:pre_existing`,
`er:generator_drift`, `er:evidence_defect`, `er:infrastructure`, `er:ImportedReceipt`
(`er:importName`, `er:importPath`, `er:importDigest`, `er:ordinal`, `er:importSource`),
`er:RootReceipt` (`er:receiptRelease`, `er:receiptId`, `er:subjectRepository`, `er:subjectProbe`,
`er:actor`, `er:receiptAuthority`, `er:receiptGrant`, `er:intention`, `er:timestamp`,
`er:changedPath`, `er:standingBefore`, `er:standingAfter`), the court observations
`er:observedExit` / `er:observedOutput` / `er:observedCommandSha256` / `er:observedCourtInput`, and
the transition law
`er:permitsStanding`
(chatman-ecosystem `Standing::permits`, `crates/ecosystem-core/src/lib.rs:208-232` at c59596f5,
restricted to UNKNOWN, PARTIAL_ALIVE, ALIVE, BLOCKED and UNSUPPORTED; UNKNOWN -> ALIVE is not in it).

Both laws are closed against consumer data. RDF is open-world and a consumer graph is unioned with
the pack ontology, so a law read from graph triples could be widened by one consumer triple (for
example `er:UNKNOWN er:permitsStanding er:ALIVE .` or `er:flaky a er:FailureClass .`). Gate 097
therefore decides the transition on its own table of the nine pairs and gate 095 decides the
failure class on its own list of the six IRIs; the ontology's `er:permitsStanding` triples and
`er:FailureClass` individuals are copies that the same gates hold equal to those tables (an extra
triple, a missing pair or class, or a relabelled class is refused). The receipt renders a failure
class from its IRI, not from a label.

The loop is sync, court, sync:

1. `ggen sync run` renders `out/scripts/crown_v<version>.sh` (one per release that declares a
   gate; `.` in the version becomes `_`), `out/typed-checks.txt`, `out/receipts/IMPORTS.sha256`
   and both receipts. The receipts are never omitted: before the court has observed, their subject
   is `UNOBSERVED`, every gate is `UNOBSERVED` (fleet exit `-1`), standing_after is not ALIVE and
   ROOT.json carries `broken_term` `R_missing_identity` (the fleet validator refuses the missing
   subject SHA), so an unobserved receipt is typed, never admitted and never silently absent.
2. `COURT_OBSERVED=observed.ttl bash out/scripts/crown_v<version>.sh` re-hashes every
   `er:ImportedReceipt` (exit 100 on a missing file or a digest mismatch), runs every probe (exit
   101 on a failure) and then every gate in `er:gateOrder` order, each command as one single-quoted
   word run by `bash -euo pipefail -c` (a syntax error in a command is that gate's own refusal). A
   failing gate stops the court with exit status equal to its order and a
   `COURT_GATE_REFUSED order=N name=... exit=...` line; exit 103 means the consumer root or the
   court root is not a directory. The observation file (probe outputs, gate exits, each with the
   SHA256 of the command text that ran, and the release's `er:observedCourtInput` set naming the
   whole court input: `court|<version>|<court root>`, `component|<repo>|<sha>` per component,
   `import|<ordinal>|<name>|<path>|sha256:<hex re-hashed>` per import, and
   `probe|`/`gate|<IRI>|<order>|<name>|<command sha256>`) is replaced only when the court reaches a
   gate verdict; an import, probe or court-root failure leaves the previous observation untouched.
   Replacing the observation also removes `out/receipts/root-receipt.unsealed.toml` and
   `out/receipts/ROOT.json` (`COURT_RECEIPT_SUPERSEDED` lines): they were rendered from the
   superseded observation, and the next sync renders them from the new one instead of refusing the
   changed render (FM-WRITE-005).
   Gate 095 rebuilds the current input from the graph and refuses any element present on one side
   only (and an observed court without the set), so an import digest or path, a component SHA, the
   court root or version, or a probe or gate edited, added or removed after the court ran makes the
   observation stale: re-run the court (empty `observed.ttl`, sync, court, sync) instead of
   re-rendering receipts from it.
3. `ggen sync run` again renders `out/receipts/root-receipt.unsealed.toml` (chatman `Receipt`
   shape, digest `""`, for `ecosystem receipt seal`) and `out/receipts/ROOT.json` (fleet R schema:
   replay exits are the observed exits, `-1` with an UNOBSERVED summary for a gate the court never
   reached). Every standing but ALIVE carries a typed `broken_term`: `mu_on_O` when a gate refused,
   `R_missing_identity` when no subject was observed, otherwise `R_missing_consequence` (a gate of
   the court input has no observed exit).

`er:standingAfter` is derived by the `construct:` of `root-receipt.toml.tmpl`: BLOCKED when any
observed exit is non-zero, ALIVE only when every gate of the release has exactly one observed exit
and all are 0, otherwise `er:standingBefore` (no new evidence), except that a standing before of
ALIVE becomes BLOCKED: ALIVE is never carried without complete evidence, and chatman
`Standing::permits` lets ALIVE only stay ALIVE or become BLOCKED. A declared value that differs
from the derivation makes two values and gate 097 refuses it, so standing is never a literal. The receipt
binds the court subject from `er:subjectProbe` (for example `git rev-parse HEAD`); a commit cannot
contain its own SHA, so the receipt and its observation land in a receipts-only child commit.

The receipt's `observed[]` holds the release components (`repo@sha`) and every probe output,
`verified[]` every import `name=sha256:...` plus, per `er:ImportedCrown`, its STOP standing and the
two CE23-8 counters, `excluded[]` every non-REQUIRED role disposition and every typed check, and
`replay[]` the gate commands. A release's own STOP condition (for chatman, CHATMAN_STOP) is a
consumer `er:Gate` command checked at court time, never a generic pack gate: a generic STOP gate
would refuse this pack's own `qualification/consumer.ttl` and every pre-crown sync.

## Disposition rule

`templates/role-disposition-rule.toml.tmpl` carries the rule as a `construct:` frontmatter
(Stage-2 enrich; `[[inference.rules]]` is refused FM-CONFIG-101 in the frontmatter schema).
For each required role of the predecessor without an explicit decision:

1. its repository is classified in the imported fleet classification (join on the basename of
   the `owner/name` slug; collisions are refused): CriticalPath -> REQUIRED, Successor ->
   SUCCESSOR, Blocked -> BLOCKED, Refused -> REFUSED, Unsupported -> UNSUPPORTED, any other
   class -> UNCLASSIFIED (refused);
2. otherwise, when no court of the governing checkpoint executes the repository: SUCCESSOR,
   `er:derivedBy "rule:no-GC23-court-reference"` (a successor repository becomes required only
   when a court executes it);
3. otherwise nothing is derived and gate 070 refuses the role as undisposed.

## Gates

| gate | refuses |
|---|---|
| 010-060 | release contract, component identity, dependency closure, required-role law, external ref observation, unique repository (law unchanged; 010 and 020 now bind the subject in every UNION branch, see below) |
| 070_role_crosswalk_total | a predecessor role with 0 or >1 dispositions; an untyped/UNCLASSIFIED or multi-valued boundary; a row without reason or without derivedBy/decidedBy; REQUIRED not supplied by a required component of the target; an explicit decision for a classified repository; basename collisions |
| 075_constitutional_role_mapping | a required role or required component role without exactly one mapping; non-constitutional primary/capability; empty authority ceiling; Actuate without BRCE exclusivity |
| 080_critical_path_coverage | a CriticalPath repository, or a court-executed repository, that is not a required component of the release |
| 085_requirement_row_identity | a checkpointed sj:WorkOrder without owner/name repository, 40-hex base SHA or falsifier description (every UNION branch binds the order) |
| 095_release_court | an er:Gate not owned by exactly one release, with an order outside 1..99 or duplicated, a name outside `[A-Za-z0-9][A-Za-z0-9._:-]*`, a blank or multi-valued command, or an observed exit outside 0..255; an observed gate or probe without er:observedCommandSha256 equal to SHA256 of its current command; an observed court without its er:observedCourtInput set, or a set that differs from the current court input in any element (court version and root, component SHAs, import ordinal/name/path/digest, probe and gate IRI/order/name/command hash); an er:Probe not owned by exactly one release, with a bad or duplicated name/order or a blank command, or two observed outputs; an er:CheckDisposition not owned by exactly one release, with a missing or multi-line or duplicated name, a failure class that is not one of the six operator classes (closed list in the gate), a boundary other than SUCCESSOR/BLOCKED/UNSUPPORTED/REFUSED, or no evidence; an er:FailureClass individual other than the six, one of the six missing, or one of them labelled other than its own name; a gate or probe IRI containing `'`; an unsafe er:courtRoot; probes or typed checks without a gate |
| 097_root_receipt | more than one er:RootReceipt; a receipt id outside `receipt:[a-z0-9_-]+`; no court release; an empty or multi-valued subject repository, actor, intention or timestamp; an authority that is not a chatman Authority; a standing before outside the five receipt standings; not exactly one derived standing after; a before -> after pair outside the gate's closed table of the nine chatman Standing::permits pairs; an er:permitsStanding triple outside that table, or a table pair missing from the graph; a subject probe not of the release, or an observed court without one 40-hex subject; no import; an import without exactly one name, path, sha256 digest and integer ordinal, with an unsafe name or path, or duplicated; an er:ImportedCrown digest that is not imported, or a crown or paired component that is not the release component of that repository at the same commit |
| 090_imported_crown | an er:ImportedCrown whose STOP is not ALIVE, whose STOP or gate digest is absent, with fewer than er:requiredGateCount distinct ALIVE gates at the crown subject, whose STOP subject differs from the crown component commit, with a gate not ALIVE, at a foreign subject or against a foreign paired commit, or with a CE23-8 counter absent, null or not 0 |

Gates are enforced natively by `ggen sync run` (FM-PACK-013) when the pack is consumed through a
`[packs]` entry, and by the explicit rdflib runner `bin/run-gates.py <graph.ttl> [gates]`, which
unions the same inputs (pack ontology, the graph, the sibling `ggen.toml` imports) and applies the
templates' `construct:` rules before gating.

The two executors disagreed on one query shape, now removed from gates 010, 020 and 085: a UNION
branch holding only `FILTER NOT EXISTS { ?x ... }` under an outer `?x a ...` pattern. SPARQL
evaluates a UNION branch bottom-up with `?x` unbound (SPARQL 1.1 section 18.6), so ggen matched the
inner pattern on any subject and admitted the violation whenever another subject satisfied it (a
second component with a valid ref-check mode, 20 other orders with a falsifier, components with an
`er:standing`), while rdflib substituted the outer binding and refused. Rows C29, C34 and C35 of
`court-mutants.EXPECTED.tsv` were admitted natively with the old shape and are refused natively
now that every branch binds its own subject.

## Projections

All outputs go to `out/` and are written without `force`: an existing file that differs from the
render refuses the sync (FM-WRITE-005), so a hand edit is never silently kept or silently
overwritten. To regenerate after an input change, delete the stale output and run
`ggen sync run` again.

| template | output |
|---|---|
| release-manifest.toml.tmpl | `out/manifest.toml`: every verify_release field (id, repository, ref, ref_check, sha, role, disposition, standing, required, depends_on; version from er:version) |
| constitutional-role-crosswalk.toml.tmpl | `out/constitutional-role-crosswalk.toml` (release_role, primary, capabilities, authority_ceiling) |
| legacy-role-crosswalk.toml.tmpl | `out/legacy-role-crosswalk.toml`, one row per predecessor role through OPTIONAL joins |
| requirements.toml.tmpl | `out/requirements.toml`, one row per checkpointed WorkOrder: gate, repo@sha subject, falsifier |
| crosswalk.ttl.tmpl | `out/crosswalk.ttl`, every er:RoleDisposition as Turtle (ggen does not emit its enriched graph) |
| role-disposition-rule.toml.tmpl | the disposition rule, and `out/role-derivations.toml` (derived vs decided rows) |
| imported-crown.toml.tmpl | `out/imported-crown.toml`: per crown the checkpoint, STOP standing, subject and digest, both component repo@sha, required gate count, the two CE23-8 counters, and one row per gate receipt (id, standing, subject, paired subject, digest); `crown_count = 0` for a consumer without a crown |
| release-court.sh.tmpl | `out/scripts/crown_v<version>.sh` per release with gates (`for_each` fan-out): imports re-hashed, probes, gates in order, each command one single-quoted word run by `bash -euo pipefail -c`, typed exits 1..99 / 100 / 101 / 102 / 103, optional observation output including the whole court input |
| typed-checks.txt.tmpl | `out/typed-checks.txt`: one er:checkName per line, sorted, nothing else, for a consumer check such as `comm -23 <failing check-runs> <(sort -u out/typed-checks.txt)` |
| imports.sha256.tmpl | `out/receipts/IMPORTS.sha256`: `<hex>  <er:importPath>` per import, so `shasum -a 256 -c --strict out/receipts/IMPORTS.sha256` from the court root recomputes every digest |
| root-receipt.toml.tmpl | `out/receipts/root-receipt.unsealed.toml` (every sync; typed UNOBSERVED before the court observes), and the standing derivation `construct:` |
| root-receipt.json.tmpl | `out/receipts/ROOT.json` (every sync; `broken_term` for any standing but ALIVE), validated by `~/.claude/dfcm/validate_receipt.py` |

## Qualification

`qualification/qualify.sh` runs everything in a scratch copy with the real ggen and rdflib:
the synthetic `consumer.ttl`, a double render of `consumer-v26.9.23` (byte-identical), a control
and a positive explicit-decision witness, and the 12 mutants of `qualification/mutants/`
(expected code, gate and reason in `EXPECTED.tsv`); each graph mutant is also run through the
runner without its named gate, and every one except M3 and M5 (also refused by gate 080) is then
admitted, so those refusals come from gates 070, 075, 080 and 085; M6 is refused by the no-force
write law.

Step 6 qualifies the imported crown (fixtures and their provenance: `qualification/fixtures/SOURCES.md`):
every committed `qualification/imported-crown.<name>.ttl` must equal the lift of
`qualification/fixtures/<name>-receipts`; the lift refuses 0 or 2 STOP receipts; the positive crown
passes both executors through `import-crown-generate.sh`, its committed lift and render reproduce,
and a hand-edited render or a stale committed lift is refused. Every row of
`qualification/imported-crown.EXPECTED.tsv` (six receipt mutants: stale R_0, LLM counter 1, null
actuation counter, 12 gates, foreign gate subject, foreign ggen_igniter subject; three graph
mutants: no gate count, no STOP digest, no gate digest) is returned by gate 090 with the exact row
count, refused natively (FM-PACK-013 at gate 090), and admitted once gate 090 is removed.
`XAAS_REPO=<xaas checkout>` also re-derives the fixtures byte-identically from the real receipt
blobs.

Step 7 qualifies the release court and root receipt in a copy of the pack made a real git
repository (deterministic identity and clock): the consumer-v26.9.23 court script and both
receipts render before any observation (typed PARTIAL_ALIVE -> PARTIAL_ALIVE at subject
`UNOBSERVED`, ROOT.json `R_missing_identity`, refused by the fleet validator); the court exits 0,
writes its observation and removes the two superseded receipts; the re-sync renders a
PARTIAL_ALIVE -> ALIVE receipt bound to the repository HEAD (fleet validator ADMITTED,
chatman `schemas/receipt.schema.json` valid, `shasum -c --strict` on IMPORTS.sha256), and a third
sync writes nothing. The committed `consumer-v26.9.23/observed.ttl` must equal a fresh court
observation except for its subject line, its subject must be an ancestor of HEAD, and the pack
tree at that subject must equal the current one; the observation names the whole court input (1
court, 2 components, 3 imports, 5 probes, 3 gates). Witnesses: an added refusing gate exits with its
order and renders a BLOCKED receipt (`mu_on_O`); a gate command with a shell syntax error is that
gate's refusal (court exit = its order, observed exit 2) while a command full of single quotes runs
verbatim; a missing court root exits 103; an observation without one gate's exit renders
PARTIAL_ALIVE with `R_missing_consequence`; a standing before of ALIVE stays ALIVE only with every
gate observed exit 0 and otherwise renders BLOCKED (`R_missing_consequence` with one gate
unobserved, `R_missing_identity` with no observation), and a copy of the pack whose `construct:`
lacks that clause renders ALIVE -> ALIVE without evidence (the witness measures the clause); a
tampered import exits 100 and a probe that cannot
observe exits 101, both leaving the observation untouched; a hand edit of the rendered court script
or receipt is refused by the next sync (FM-WRITE-005).
Every row of `qualification/court-mutants.EXPECTED.tsv` (UNKNOWN -> ALIVE, a declared standing
after, a duplicated gate order, an unknown failure class, a REQUIRED typed check, a malformed or
unsafe import, a non-SHA subject, an out-of-range exit, a crown at another subject, crown bytes not
imported, an observation of an edited command, consumer triples that extend the transition or
failure-class law, ontology copies that drift from them, and C20-C27: an import digest or path, the
court root, a component SHA, an added gate, a withdrawn import or the version edited after the
committed observation, or the observation's court-input set dropped) is refused natively
(FM-PACK-013 at the named gate) and by the runner with the named reason, and admitted by the runner
once that gate is removed; the admitted row carries a consistent crown into `verified[]`. Rows
C28-C35 give each release-law gate its own witness on the same consumer: ambient DO authority
(010), a ref-check mode that is a string instead of an `er:RefCheckMode` (020), a dependency cycle
(030), a required component disposed OUT_OF_RELEASE (040), EXTERNAL_EXACT without a ref observation
(050), a second component of the same repository (060), one of 21 orders without a falsifier
description (085) and the release without an `er:standing` (010); C29, C34 and C35 were admitted
natively before gates 010, 020 and 085 bound the subject in every UNION branch. The rows run
concurrently (`QUALIFY_JOBS`, default 8).
Step 7j closes the gate set against vacuity: every `gates/*.rq` must be the only refusing gate of at
least one passing mutant row (step 5 with the runner admitting it once that gate is removed, step 6e
or step 7g), so a gate that no mutated consumer can make refuse fails qualification.
`CHATMAN_REPO=<git clone of chatman-ecosystem>` builds the committed `qualification/chatman-harness`
(the `receipt seal` / `receipt verify-all` arms of chatman's CLI over the same ecosystem-core
functions) against ecosystem-core extracted from c59596f5 with `git archive` (`cargo --offline`), or
`CHATMAN_ECOSYSTEM_BIN=<binary>` names one; either seals the rendered receipt with chatman's own
receipt law, requires the UNKNOWN -> ALIVE variant to be refused there, and runs gate 097 against
chatman's `Standing::permits` on all 25 pairs of the five receipt standings.

Lane gate (MP-RELPACK-CROWN), from the pack directory:

```bash
python3 bin/run-gates.py qualification/imported-crown.positive.ttl gates \
  && for f in stale-r0 llm1 unreceipted-null drop-gate foreign-subject gi-mismatch; do
       ! python3 bin/run-gates.py qualification/imported-crown.$f.ttl gates || { echo VACUOUS $f; exit 1; }; done \
  && F=qualification/fixtures/positive-receipts \
  && python3 bin/import-crown-lift.py $F $(cat $F/XAAS_SHA) $(cat $F/GI_SHA) | cmp - qualification/imported-crown.positive.ttl \
  && python3 bin/run-gates.py qualification/consumer.ttl gates
```

Lane gate (MP-RELPACK-COURT), from the pack directory:

```bash
C=qualification/consumer-v26.9.23 && R=$(mktemp -d) && (cd $C && rm -rf out && ggen sync run > /dev/null \
  && cp -R out $R/r1 && ggen sync run > /dev/null && diff -r out $R/r1 \
  && test -s out/scripts/crown_v26_9_23.sh && test -s out/typed-checks.txt \
  && test -s out/receipts/root-receipt.unsealed.toml && test -s out/receipts/ROOT.json \
  && test -s out/receipts/IMPORTS.sha256 && grep -qx 'standing_after = "ALIVE"' out/receipts/root-receipt.unsealed.toml) \
  && python3 bin/run-gates.py qualification/consumer.ttl gates && ! grep -rl CHATMAN_STOP gates/ \
  && bash qualification/qualify.sh
```

With the committed observation the receipts render PARTIAL_ALIVE -> ALIVE; `qualify.sh` includes
the mutation corpora (`mutants/EXPECTED.tsv`, `imported-crown.EXPECTED.tsv`,
`court-mutants.EXPECTED.tsv`) and step 7j.

## See also

- `HANDWRITTEN.md`: the code residue ledger (`lift/manifest_to_er.py`, `bin/run-gates.py`,
  `bin/import-crown-lift.py`, `bin/import-crown-generate.sh`,
  `qualification/fixtures/derive-fixtures.py`, `qualification/qualify.sh`,
  `qualification/chatman-harness/`). The 0.4.0 court and receipt add no product code residue: the
  court script, the observation writer and both receipts are rendered from graph facts.
- `qualification/fixtures/SOURCES.md`: the xaas receipt blobs behind every imported-crown fixture.
- `qualification/consumer-v26.9.23/SOURCES.md`: provenance and sha256 of every imported input.
- `qualification/mutants/README.md`: each mutation as a one-change diff from the mutant base.
