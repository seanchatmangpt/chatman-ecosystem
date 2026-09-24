export const meta = {
  name: 'sm-lane-wave',
  description: 'Semantic-manufacturing lane wave: dependency-scheduled lanes, each build -> 3-lens court (gate, revert-mutation, doctrine) -> bounded repairs -> mkdir-locked integrate into the critical-path int worktree',
  whenToUse: 'Driver waves for sJira GoalCheckpoints (v26.9.23+). args = wave spec: {wave, repos, ints, base_branch, worktree_root, branch_prefix, receipts_dir, context, lanes:[{id, repo, after?, gate, task}]}',
  phases: [
    { title: 'Build', detail: 'one worktree per lane, branched from the int branch' },
    { title: 'Court', detail: 'gate + revert-mutation + doctrine lenses' },
    { title: 'Repair', detail: 'bounded repair rounds on refutation' },
    { title: 'Integrate', detail: 'mkdir-locked --no-ff merge into the int worktree' },
  ],
}

// Takeover-safe: deterministic control flow; labels `${wave}:<stage>:<lane>` are the public resume key.
const A = (args && args.wave) ? args : {"wave": "MP", "repos": {"ggen-marketplace": "/Users/sac/ggen-marketplace"}, "ints": {"ggen-marketplace": "/Users/sac/wt/v26922/fri/ggen-marketplace-int"}, "base_branch": "release/v26.9.23-int", "worktree_root": "/Users/sac/wt/v26922/v23", "branch_prefix": "mp23", "receipts_dir": "receipts/v26.9.23", "max_repairs": 2, "context": "Generator capital for the Chatman Ecosystem v26.9.23 root crown (operator chatman-ce23.md CE23-1/2/3/8/9/10; DRIVER.md 'Release closure procedure'). Repo seanchatmangpt/ggen-marketplace; int /Users/sac/wt/v26922/fri/ggen-marketplace-int on release/v26.9.23-int, based on GitHub origin/main 420bc91e7c1e291be73ab749b7e443252bc7bab8 (the local /Users/sac/ggen-marketplace main is 96feba8c9 = 5 unpushed operator commits and a dirty tree: never edit, reset or push it; read-only pattern sources there are fine). These lanes touch no frozen subject (xaas/ggen_igniter) and may run now. Generator: ggen 26.9.18 (/Users/sac/.local/bin/ggen; record ggen --version). Pack law stays generic: exact release-instance facts are consumer-owned (chatman-ecosystem-v26-9-1-release-gate/pack.toml:4); no STOP/CHATMAN_STOP gate in the generic pack (it would refuse the pack's own qualification/consumer.ttl). Pack gates must be proven both natively (consumer `ggen sync run` -> FM-PACK-013) and through an explicit rdflib runner (bin/run-gates.py; reuse packs/gym-autonomic-crown-pack/bin/run-gates.py), because a scan observed ggen enforcing pack gates only when the pack is consumed through a consumer [packs] entry. Qualification = real fixtures + mutants under the pack's qualification/, Chicago style, no mocks. Receipts receipts/v26.9.23/<LANE>.json (fleet R schema, python3 ~/.claude/dfcm/validate_receipt.py -> ADMITTED). After the wave the driver pushes release/v26.9.23-int (new branch, never force) and records its SHA; chatman consumes the packs by git+subdir pinned to that exact SHA (precedent: xaas ggen.toml:7-22). Merge to marketplace main is successor GC-26.9.24 (GC24-release-pack-upstream). Verified scan specs: /private/tmp/claude-501/v23-scratch/SCAN-synthesize/specs/<candidate-id>.txt.", "lanes": [{"id": "MP-RELPACK-XW", "repo": "ggen-marketplace", "after": [], "gate": "cd /Users/sac/wt/v26922/v23/MP-RELPACK-XW/packs/chatman-ecosystem-release-pack && test -n \"$(ls templates)\" && P=$PWD && python3 bin/run-gates.py qualification/consumer.ttl gates && (cd qualification/consumer-v26.9.23 && ggen sync run > /tmp/mpxw1.json && cp -R out /tmp/mpxw-out1 && ggen sync run > /tmp/mpxw2.json && diff -r out /tmp/mpxw-out1) && for m in qualification/mutants/*/; do (cd $m && ggen sync run > /tmp/mpxw-m.log 2>&1); r=$?; python3 $P/bin/run-gates.py $m/release.ttl $P/gates > /tmp/mpxw-g.log 2>&1; g=$?; test $r -ne 0 -o $g -ne 0 || { echo VACUOUS $m; exit 1; }; done", "task": "Required_23 generator capital for CE23-1 (independent v26.9.23 release subject) and CE23-2 (explicit disposition of every one of the 16 v26.9.1 roles). Today packs/chatman-ecosystem-release-pack (ontology.ttl, gates/010-060, qualification/consumer.ttl) has NO templates, so `ggen sync run` refuses it FM-PACK-005, and er:Disposition lacks SUCCESSOR/BLOCKED/REFUSED (er:BLOCKED/er:UNSUPPORTED are StandingState IRIs). Extend the pack in lane worktree /Users/sac/wt/v26922/v23/MP-RELPACK-XW (branch mp23/MP-RELPACK-XW off release/v26.9.23-int): (1) Vocabulary (pack namespace er:, no IRI reuse of er:Disposition / StandingState): class er:RoleDisposition; value class er:RoleBoundary with er:ROLE_REQUIRED, er:ROLE_SUCCESSOR, er:ROLE_BLOCKED, er:ROLE_UNSUPPORTED, er:ROLE_REFUSED; sentinel er:ROLE_UNCLASSIFIED (untyped); properties er:legacyRole, er:legacyComponent, er:legacySha, er:legacyStanding, er:boundary, er:sourceRelease, er:targetRelease, er:reason, er:decidedBy, er:derivedBy, er:suppliedBy, er:classificationSource, er:legacyRequiredRole, er:courtReferencesComponent; class er:LegacyRelease so lifted v26.9.1 facts are not re-judged by gates 010-060. (2) gates/070_role_crosswalk_total.rq refuses: a legacyRequiredRole with 0 or >1 dispositions; a boundary not an er:RoleBoundary; duplicate rows per role; ROLE_REQUIRED not supplied by a required component of the target release; a disposition without er:reason or er:derivedBy/er:decidedBy; an explicit decision overriding a repo present in the fleet classification. gates/080_critical_path_coverage.rq refuses any CriticalPath repository of the imported fleet classification that is not a required er:Component of the target release. (3) Disposition rule as a template `construct:` frontmatter (Stage-2 enrich; `[[inference.rules]]` is refused FM-CONFIG-101 in the frontmatter schema; any CONSTRUCT needs ORDER BY, strict_mode E0011): a legacy role with no explicit disposition and no er:courtReferencesComponent fact gets ROLE_SUCCESSOR with er:derivedBy rule:no-GC23-court-reference (the operator topology law: a successor repo becomes required only if a GC23 court executes it); in-universe repos map CriticalPath->REQUIRED, Successor->SUCCESSOR, Blocked->BLOCKED, Refused->REFUSED, Unsupported->UNSUPPORTED by join on the GitHub slug (refuse basename collisions). (4) Templates (frontmatter pattern of packs/frontier-release-factory-pack/templates/acceptance-contract.toml.tmpl): release-manifest.toml.tmpl emitting every verify_release field (id, repository, ref, ref_check, sha, role, disposition, standing, required, depends_on; version from er:version); constitutional-role-crosswalk.toml.tmpl (release_role, primary, capabilities, authority_ceiling, so survey_portfolio RELEASE_ROLE_UNMAPPED stays clean); legacy-role-crosswalk.toml.tmpl (OPTIONAL join + gate, never an inner join that silently drops a row); requirements.toml.tmpl (rows from CE WorkOrders: gate, repo@sha40 subject, falsifier); a crosswalk.ttl.tmpl that wraps <IRI>/\"literal\" (ggen does not emit the inferred graph). (5) lift/manifest_to_er.py (~35 lines tomllib; the only code residue, owned by this pack; no marketplace pack parses TOML into RDF): release manifest TOML -> er:LegacyRelease/er:legacyRequiredRole TTL; gates 010-060 return 0 rows on its output. (6) bin/run-gates.py (reuse packs/gym-autonomic-crown-pack/bin/run-gates.py). (7) qualification/consumer-v26.9.23/ (ggen.toml consuming the pack by relative path + extra_ontologies, a lifted copy of chatman release/v26.9.1/manifest.toml at c59596f5, a copy of xaas docs/sjira/v26.9.23/fleet/classification.ttl with its sha256, court-reference facts) and qualification/mutants/{M1 drop one crosswalk row, M2 disposition UNCLASSIFIED, M3 add a court reference so no disposition derives, M4 drop ggen_igniter consistently (component + dependsOn + requiredRole), M5 reclassify open-ontologies CriticalPath, M6 hand-edited rendered file}; each mutant must be refused by the native sync (FM-PACK-013) or the explicit runner (record which; M1/M3/M4 passed the earlier probe gates, so gates 070/080 must catch them). pack.toml version 0.2.0 (was 0.1.0); update the pack description. Prototypes (verified with ggen 26.9.18): /private/tmp/claude-501/v23-scratch/SCAN-CHATMAN/genprobe-gates2, SCAN-CE23-2-crosswalk-gen/proto (import_manifest.py, crosswalk.construct.rq, gates/070, templates/*.tera), SCAN-VERIFY-CE23-1-2. Residue: lift/manifest_to_er.py only; gate/template/ontology additions are pack capital. Falsifier: any mutant renders with exit 0 and zero gate rows, or two consumer renders differ. Receipt receipts/v26.9.23/MP-RELPACK-XW.json."}, {"id": "MP-RELPACK-CROWN", "repo": "ggen-marketplace", "after": ["MP-RELPACK-XW"], "gate": "cd /Users/sac/wt/v26922/v23/MP-RELPACK-CROWN/packs/chatman-ecosystem-release-pack && P=$PWD && python3 bin/run-gates.py qualification/imported-crown.positive.ttl gates && for f in stale-r0 llm1 unreceipted-null drop-gate foreign-subject gi-mismatch; do ! python3 bin/run-gates.py qualification/imported-crown.$f.ttl gates || { echo VACUOUS $f; exit 1; }; done && F=qualification/fixtures/positive-receipts && python3 bin/import-crown-lift.py $F $(cat $F/XAAS_SHA) $(cat $F/GI_SHA) | cmp - qualification/imported-crown.positive.ttl && python3 bin/run-gates.py qualification/consumer.ttl gates", "task": "Required_23 generator capital for CE23-3 (import the Semantic Manufacturing crown by exact digest; STOP=true; 13 admitted gate receipts) and CE23-8 (LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH=0, UNRECEIPTED_ACTUATION=0 carried into the root receipt). Schema validation cannot decide STOP truth (validate_receipt.py ADMITS the stale 0/13 STOP receipt), so the law is a pack gate. Lane off release/v26.9.23-int after MP-RELPACK-XW (same pack). Add to packs/chatman-ecosystem-release-pack: ontology er:ImportedCrown, er:crownComponent, er:pairedComponent, er:crownSubjectSha, er:stopStanding, er:hasGateReceipt, er:gateStanding, er:gateSubjectSha, er:pairedSubjectSha, er:requiredGateCount, er:llmInvocationsOnKnownReferencePath, er:unreceiptedActuation, er:stopReceiptSha256, er:receiptSha256; gates/090_imported_crown.rq (SELECT-violation style of 010-060) refusing: STOP standing not ALIVE; fewer than er:requiredGateCount distinct ALIVE gate receipts whose subject_sha equals the crown subject; STOP subject_sha != the crown component er:commitSha; any gate.ggen_igniter_sha != the paired component er:commitSha; either counter absent, null or != 0 (V23-S writes null with a reason when unreadable); bin/import-crown-lift.py (receipt JSON dir -> er: TTL; generic for any upstream checkpoint crown; ~30-40 lines, prototype SCAN-CE23-3-8-crown-import/proto/lift_ttl.py); templates/imported-crown.toml.tmpl; bin/import-crown-generate.sh (lift -> run-gates -> consumer `ggen sync run` -> diff against the committed file; precedent gym-autonomic-crown-pack/bin/crown-generate.sh). Qualification fixtures (data): positive = the real V23-S smoke STOP whose counters are 0 with gates rewritten ALIVE at one subject; stale-r0 = xaas 66b52e7 R_0 receipts (STOP subject 11a24fba..., UNKNOWN, 0/13; prototype refused with 18 rows); llm1; unreceipted-null; drop-gate (12 gates); foreign-subject; gi-mismatch; each fixture dir carries XAAS_SHA and GI_SHA files naming its subjects. Prototype gate: SCAN-CE23-3-8-crown-import/proto/080_imported_crown.rq (renumbered 090 here). Residue: bin/import-crown-lift.py (owner: this pack). Falsifier: the stale R_0 fixture, a counter=1 fixture or a foreign-subject gate receipt passes the gates. Receipt receipts/v26.9.23/MP-RELPACK-CROWN.json."}, {"id": "MP-RELPACK-COURT", "repo": "ggen-marketplace", "after": ["MP-RELPACK-CROWN"], "gate": "cd /Users/sac/wt/v26922/v23/MP-RELPACK-COURT/packs/chatman-ecosystem-release-pack && C=qualification/consumer-v26.9.23 && (cd $C && rm -rf out && ggen sync run > /dev/null && cp -R out /tmp/mpct1 && ggen sync run > /dev/null && diff -r out /tmp/mpct1 && test -s out/scripts/crown_v26_9_23.sh && test -s out/typed-checks.txt && test -s out/receipts/root-receipt.unsealed.toml && test -s out/receipts/ROOT.json && test -s out/receipts/IMPORTS.sha256) && python3 bin/run-gates.py qualification/consumer.ttl gates && ! grep -rl CHATMAN_STOP gates/", "task": "Required_23 generator capital for CE23-9 (exact-head root court) and CE23-10 (root release receipt). No template or vocabulary for a release court or root receipt exists anywhere (the pack has no templates/; ggen-release-pack/publish_candidate_workflow.yml.tmpl only echoes a hand-written literal body). Lane off release/v26.9.23-int after MP-RELPACK-CROWN (same pack). Add: ontology er:Gate, er:gate, er:gateOrder, er:command, er:CheckDisposition, er:checkName, er:failureClass (individuals subject_defect, environment, pre_existing, generator_drift, evidence_defect, infrastructure), er:RootReceipt, er:ImportedReceipt (importName, importPath, importDigest, ordinal) and receipt properties; templates release-court.sh.tmpl (one SPARQL SELECT over er:Gate ordered by er:gateOrder, a Tera loop emitting each er:command under `set -euo pipefail`, typed exit per failing gate; pattern /Users/sac/ggen-marketplace/packs/invariant-gate-pack/templates/test_invariants.sh.tmpl — read-only, it exists only in the local unpushed main), typed-checks.txt.tmpl (from er:CheckDisposition rows), root-receipt.toml.tmpl (chatman Receipt shape: id receipt:release-v26-9-23, authority release, standing_before PARTIAL_ALIVE -> standing_after ALIVE — Unknown->Alive is refused by Standing::permits, lib.rs:208-232; observed[] component SHAs, chatman subject SHA, graph_hash, pack/ontology/schema digests, toolchain, V23-Q release-receipt digest; verified[] import name=sha256 pairs, STOP counters, fleet digest; excluded[] successor/blocked/refused typing; replay[] court commands), root-receipt.json.tmpl (fleet R schema; standing and exits from observed facts), imports.sha256.tmpl (so a later `shasum -a 256 -c --strict` recomputes every import digest). CHATMAN_STOP is NOT a generic pack gate (it would refuse the pack's own q:release UNKNOWN fixture and every pre-crown sync); the consumer checks it at court time. qualification/consumer-v26.9.23/ gains er:gate facts, one er:CheckDisposition, an observed.ttl fixture via extra_ontologies. Prototypes (ggen 26.9.18, two byte-identical syncs): SCAN-CE23-9-root-court/probe, SCAN-CE23-10-root-receipt/gen. Residue: none in the pack beyond ontology/templates (pack capital); the consumer's court-set facts stay consumer-owned. Falsifier: a hand-edited rendered crown script survives a re-sync without diff, or the rendered receipt accepts Unknown->Alive. Receipt receipts/v26.9.23/MP-RELPACK-COURT.json."}, {"id": "MP-RPV", "repo": "ggen-marketplace", "after": [], "gate": "set -e; cd /Users/sac/wt/v26922/v23/MP-RPV/packs/receipt-provenance-unification-pack && ggen sync run > /dev/null && ggen sync run | grep -q 'skipped: unchanged' && V=$PWD/generated/unified_receipt_validator.py && for f in /Users/sac/wt/v26922/fri/xaas-int/docs/sjira/v26.9.23/receipts/*.json /Users/sac/wt/v26922/fri/xaas-int/receipts/v26.9.23/*.json /Users/sac/wt/v26922/fri/ggen_igniter-int/receipts/v26.9.23/*.json qualification/fixtures/dfcm_fleet_v1/*.json; do a=0; python3 $V $f --contract=dfcm_fleet_v1 >/dev/null 2>&1 || a=$?; b=0; python3 /Users/sac/.claude/dfcm/validate_receipt.py $f >/dev/null 2>&1 || b=$?; [ $a = $b ] || { echo DIVERGE $f; exit 1; }; done && python3 $V --contract dfcm_fleet_v1 /Users/sac/wt/v26922/fri/xaas-int/docs/sjira/v26.9.23/receipts/GC23-4.json > /dev/null && for f in qualification/fixtures/durable/neg-*.json; do set +e; python3 $V --contract=dfcm_fleet_v1 --require-durable --repo-map seanchatmangpt/xaas=/Users/sac/wt/v26922/fri/xaas-int $f > /tmp/rpv.o 2>&1; e=$?; set -e; test $e -eq 1 && grep -Eq 'R_missing_identity|R_missing_replay' /tmp/rpv.o && ! grep -q Traceback /tmp/rpv.o; done && python3 $V --contract=dfcm_fleet_v1 --require-durable --repo-map seanchatmangpt/xaas=/Users/sac/wt/v26922/fri/xaas-int qualification/fixtures/durable/pos-git-blob.json && test -z \"$(python3 -c 'import rdflib,sys;g=rdflib.Graph();g.parse(\"ontology.ttl\");print(len(list(g.query(open(\"gates/01_no_actuation.rq\").read()))) or \"\")')\"", "task": "Required_23 (CE23-9 'imported receipt validation' at the exact-head root court; CE23-3 'all 13 gate receipts admitted'; PRD 28 'a named receipt without validated contents is not ALIVE'). Two verified defects: (a) no validator runs on a GitHub runner — ~/.claude/dfcm/validate_receipt.py loads its schema from Path.home() (:9) and imports jsonschema; chatman has none; (b) its identity check is dead for every slug receipt: :20-25 checks subject_sha only when Path(identity.repo).is_dir(), and since V23-S identity.repo is the GitHub slug (forged-slug receipts with subject_sha 000..0 are ADMITTED). Do NOT edit ~/.claude/dfcm/validate_receipt.py (unversioned; its sha256 is the verifier identity V23-S binds into every receipt). Extend the generator instead: packs/receipt-provenance-unification-pack (ggen.toml + ontology.ttl + templates/unified_receipt_validator.py.tmpl -> generated/unified_receipt_validator.py, stdlib json/re/sys/subprocess only). Lane off release/v26.9.23-int (independent pack). (1) Template extension: jsonType array with rp:minItems and rp:itemPattern; a CONDITIONAL-required table (rp:requiredWhenPath/rp:requiredWhenPattern); rp:ImplicationRule (rp:ifPath, rp:ifPattern, rp:thenPath, rp:thenEquals); accept `--contract KEY` and `--contract=KEY`; per-binding rp:brokenTerm so refusals print R_missing_identity / R_missing_replay; rp:resolution kinds (subject_commit, notes_object, blob_at_commit, ancestor_of) rendered into a read-only resolver (`git cat-file -e`, `git merge-base --is-ancestor`) behind `--require-durable [--repo-map owner/repo=path ...]`; with no flags every verdict is unchanged. (2) Ontology facts (data, each with rp:sourceFile/rp:sourceLine so gates/02_every_fact_cited.rq returns 0 rows): contract dfcm_fleet_v1 (schemaUri https://chatmangpt.com/schema/receipt/v1, citing /Users/sac/.claude/dfcm/receipt.schema.json sha256 c19451fa...); value forms sha256-hex-prefixed, authority-ceiling, standing-dfcm, chatman-broken-term, array-of-git-sha-abbrev, array-of-string, array-min1, owner/repo slug, durable-location (git-notes:refs/notes/<ref>@<sha> | git:<owner/repo>@<sha>:<path> where subject_sha is <sha> or its ancestor | https URL; absolute local paths /private/tmp, /tmp, /var/folders and non-git dirs refused); ~19 field bindings (identity.{subject,repo,subject_sha,base_sha,graph_hash?}, authority.{actor,ceiling,grant}, consequence.{commits,files_changed,remote_effects}, replay.commands minItems 1 with {cmd,cwd,exit,output_sha256?}, standing.{value,derived_from}, standing.broken_term required when standing.value ^(BLOCKED|BUILD_BROKEN|REFUSED)); implication standing.value ^ALIVE$ => every replay exit == 0 (validate_receipt.py:18); replace rp:val_none with a Validator individual citing validate_receipt.py. Do NOT add a chatman_root_v1 contract (ecosystem-core Receipt::verify owns it; O(N^2) drift). (3) qualification/fixtures/dfcm_fleet_v1/ mutants derived from xaas GC23-4.json with expected exits; qualification/fixtures/durable/{neg-forged-GC23-4.json (/private/tmp/claude-501/v23-scratch/SCAN-stale-evidence/forged-GC23-4.json), neg-forged-slug-notes-sha0.json, pos-git-blob.json}. (4) Update pack.toml description and PROVENANCE.md ('read-only git probes'); gates/01_no_actuation.rq stays 0 rows. Prototypes: SCAN-CE23-9-imported-receipt-validator/ontology.diff, SCAN-CE23-9-validator-durable-identity-profile/pack/ontology.ttl:332-350. Residue: ontology instance facts (data) + fixtures; zero hand-written code outside the pack's template. Falsifiers: the default-profile verdict differs from validate_receipt.py on any current receipt (the gate's DIVERGE loop); a forged receipt is ADMITTED under --require-durable; a refusal prints a traceback instead of a broken_term. Receipt receipts/v26.9.23/MP-RPV.json."}]}
const WAVE = A.wave || 'wave'
const REPO = A.repos || {}
const INT = A.ints || {}
const BASE = A.base_branch || 'friday/gc-fri-0800'
const WT = A.worktree_root || '/Users/sac/wt/v26922/v23'
const PREFIX = A.branch_prefix || 'v23'
const RDIR = A.receipts_dir || 'receipts/v26.9.23'
const MAXREP = typeof A.max_repairs === 'number' ? A.max_repairs : 2
const CONTEXT = A.context || ''
const LANES = A.lanes || []
const lockPath = (repo) => `${INT[repo]}.merge.lock`

const DOCTRINE = `Binding for this stage (the ~/.claude/rules files are already loaded; do not re-read them):
- Read /Users/sac/wt/v26922/v26923/DRIVER.md (driver, gate map, PVOCAB) and /Users/sac/wt/v26922/COORDINATION.md
  (merge lock, conservation rules, reserved files). The accepted product contract is
  /Users/sac/wt/v26922/v26923/prd-ard.md (PRD + ARD for v26.9.23); cite its section ids (PR-0xx, AR-0xx, §n) in commits.
- Work ONLY in your own worktree. Never edit ${Object.values(INT).join(' or ')} except in the Integrate stage, and never
  edit any other executor's worktree (/Users/sac/wt/v26922/<repo>/int, wo*, law-*, fri/FRI-*, v23/<other lane>).
- Generation-first: extend the ontology/pack/template/generator before hand-writing; hand-written residue gets a
  HANDWRITTEN.md ledger row (UNSUPPORTED(generator-capability) + reason). Chicago tests only: real git repos in tmp dirs,
  real processes, the repo's real DB test setup; no mocks, no monkeypatch.
- git: commit with -F <message file>; never rebase, force, reset --hard, or -X ours/theirs; fetch with --no-prune.
- Receipt: ${RDIR}/<LANE>.json in the fleet R schema, validated by python3 ~/.claude/dfcm/validate_receipt.py (must
  print ADMITTED). Standing words: ALIVE only for an observed run on the exact committed subject; otherwise
  PARTIAL_ALIVE/UNKNOWN/BLOCKED/UNSUPPORTED/REFUSED with a broken_term.
- No LLM, network model API, or zcode binary on any executed product path (the LLM edge is only candidate extraction
  from prose, and it is recorded as such).
- Disk: check df -g /Users/sac before every compile/test/clone. Below 10 GB free: run /Users/sac/.oclnr/bin/oclnr snapshot
  thin --bytes 20GB (receipted), then wait (sleep 60, up to 20 min) for space before continuing; an ENOSPC failure is an
  environment failure to report, never a code verdict. Never rm -rf outside your own scratch dirs. Prefer APFS clones
  (cp -c) of existing _build/deps over fresh builds. Load is shared with other executors: no -j over-subscription.
- Keep every single shell command under ~20 min: run long suites as separate commands with output to a scratch log,
  never one compound gate with a 40-minute timeout (two agents went silent for 60-90 min after such calls).
- Report only real command output (cmd => exit, one-line summary). Distinguish pre-existing failures from new ones.
${CONTEXT}`

const BUILD = { type: 'object', properties: {
  lane: { type: 'string' }, worktree: { type: 'string' }, branch: { type: 'string' }, base_sha: { type: 'string' },
  head_sha: { type: 'string' }, standing: { type: 'string' },
  files_changed: { type: 'array', items: { type: 'string' } },
  commands: { type: 'array', items: { type: 'string' }, description: 'cmd => exit, summary' },
  receipt_path: { type: 'string' }, receipt_validator_output: { type: 'string' },
  blocked_reason: { type: 'string', description: 'set only when the lane cannot proceed (with broken_term)' },
  notes: { type: 'string' },
}, required: ['lane', 'worktree', 'branch', 'head_sha', 'standing', 'commands'] }
const VERDICT = { type: 'object', properties: {
  lane: { type: 'string' }, lens: { type: 'string' }, verdict: { type: 'string', enum: ['pass', 'refuted'] },
  reasons: { type: 'array', items: { type: 'string' } }, commands: { type: 'array', items: { type: 'string' } },
  broken_term: { type: 'string' },
}, required: ['lane', 'lens', 'verdict', 'reasons', 'commands'] }
const INTEG = { type: 'object', properties: {
  lane: { type: 'string' }, merged: { type: 'boolean' }, int_head: { type: 'string' },
  conflicts: { type: 'array', items: { type: 'string' } }, post_merge: { type: 'array', items: { type: 'string' } },
  reason: { type: 'string' },
}, required: ['lane', 'merged', 'post_merge'] }

const wtOf = (L) => L.worktree || `${WT}/${L.id}`
const scratchOf = (L) => `/private/tmp/claude-501/v23-scratch/${WAVE}-${L.id}`
const build = (L) => agent(`Target repo: ${REPO[L.repo]}. Lane ${L.id} of wave ${WAVE}.
${L.worktree
  ? `Worktree: continue in the EXISTING lane worktree ${L.worktree} (branch ${L.branch}); it is yours for this lane (the
"never edit fri/FRI-*" rule does not apply to it). Do not create another worktree. cd ${L.worktree} && pwd && git branch --show-current && git rev-parse HEAD (record base_sha = merge-base with ${BASE}).`
  : `Worktree: if ${wtOf(L)} already exists, cd into it and continue from its committed state (a prior run of this lane);
otherwise: cd ${REPO[L.repo]} && git worktree add -b ${PREFIX}/${L.id} ${wtOf(L)} ${L.from || BASE}. Provision deps/_build by
APFS clone (cp -cR deps _build from ${INT[L.repo]} when mix.lock is identical) instead of a fresh fetch+compile. Then
cd ${wtOf(L)} && pwd && git branch --show-current && git rev-parse HEAD (record base_sha = merge-base with ${BASE}).`}
Scratch: use ONLY ${scratchOf(L)} (mkdir -p it) for temp files, logs and clones; never cite another lane's scratch output
as evidence (a receipt was refuted for quoting a shared scratch file from another tree). Remove your scratch clones when done.
${DOCTRINE}
Task (${L.id}): ${L.task}
Lane gate (run it on the committed head, paste exits): ${L.gate}
Write and validate ${RDIR}/${L.id}.json, commit with -F. If a real dependency is missing (e.g. a predecessor lane is not
merged into ${BASE}), stop, set blocked_reason with broken_term, and return. Return the structured result.`,
  { label: `${WAVE}:build:${L.id}`, phase: 'Build', schema: BUILD })

const court = (L, b, round) => parallel([
  () => agent(`Target: worktree ${b.worktree} (repo ${REPO[L.repo]}), head ${b.head_sha}. cd there && pwd && git rev-parse HEAD && git status --porcelain.
${DOCTRINE}
Lens GATE for ${L.id}: re-run the lane gate yourself (${L.gate}) and every command the builder claims
(${JSON.stringify(b.commands || []).slice(0, 3000)}); validate the receipt ${b.receipt_path || '(missing)'}.
Refute on any failing command, a claim that does not match real output, an unvalidated receipt, or a dirty tree. Do not edit or commit.`,
    { label: `${WAVE}:gate${round}:${L.id}`, phase: 'Court', schema: VERDICT }),
  () => agent(`Target: repo ${REPO[L.repo]}. cd ${REPO[L.repo]} && pwd.
${DOCTRINE}
Lens REVERT-MUTATION for ${L.id}: git worktree add --detach /tmp/v23-mut-${L.id}-r${round} ${b.head_sha}; in it restore every
NON-TEST source file changed since ${b.base_sha} to its ${b.base_sha} content (keep test files and fixtures); run the lane's
tests (${L.gate}). This lens passes only if the lane's new tests FAIL on the mutated subject for the reason the change
exists (not only UndefinedFunction noise: name which assertions fail). If they still pass -> refuted, broken_term
admission_vacuous. Finally remove your scratch worktree with git worktree remove --force (it is yours).`,
    { label: `${WAVE}:mut${round}:${L.id}`, phase: 'Court', schema: VERDICT }),
  () => agent(`Target: worktree ${b.worktree}. cd there && pwd. Read-only.
${DOCTRINE}
Lens DOCTRINE for ${L.id}: read git diff ${b.base_sha}..${b.head_sha}. Refute for: mocks or monkeypatching; weakened,
skipped or deleted tests; deviations from the vocabulary contracts in DRIVER.md (IRIs, field names, digest rules);
edits outside the lane's scope or to another lane's reserved files; hand-written code where a generator exists without a
HANDWRITTEN row; any LLM/model call on an executed product path; swallowed errors (rescue/catch without typed return,
rethrow or log); receipts that overclaim ALIVE; requirements of the task left unimplemented while claimed done.`,
    { label: `${WAVE}:doc${round}:${L.id}`, phase: 'Court', schema: VERDICT, agentType: 'Explore' }),
])
const bad = (vs) => vs.some(v => !v || v.verdict !== 'pass')

const chains = {}
const serial = (repo, fn) => {
  const prev = chains[repo] || Promise.resolve()
  const p = prev.then(fn, fn)
  chains[repo] = p.catch(() => null)
  return p
}

const integrate = (L, b) => serial(L.repo, () => agent(`Target: critical-path integration worktree ${INT[L.repo]} (branch ${BASE}).
${DOCTRINE}
Integrate ${b.branch} (${b.head_sha}) for lane ${L.id}:
1. Lock (shared with other executors): until mkdir ${lockPath(L.repo)} 2>/dev/null; do sleep 15; done;
   echo "claude:${WAVE}:${L.id}" > ${lockPath(L.repo)}/owner. ALWAYS release at the end (rm owner; rmdir), also on failure.
2. cd ${INT[L.repo]} && pwd && git branch --show-current && git status --porcelain (untracked files that belong to another
   lane's receipt dir are not yours: leave them; tracked modifications you did not make -> stop, release, merged=false).
3. git merge --no-ff ${b.branch} -F <msgfile>. Conflicts: read both sides and keep both contents (append-only ledgers keep
   every row); never take one side wholesale.
4. Post-merge: run the lane gate (${L.gate}) in ${INT[L.repo]}. If the merge breaks it and one small fix-forward commit
   cannot repair it, git revert -m 1 the merge and report merged=false with the failing output.
5. Append one JSON line to /Users/sac/wt/v26922/transitions.jsonl:
   {"wo":"${L.id}","repo":"${L.repo}","executor":"claude","to":"<standing>","subject_sha":"<int HEAD>","receipt":"${RDIR}/${L.id}.json","wave":"${WAVE}"}
6. Release the lock.`, { label: `${WAVE}:int:${L.id}`, phase: 'Integrate', schema: INTEG }))

const lane = async (L) => {
  let b = await build(L)
  if (!b) return { lane: L.id, status: 'build-null' }
  if (b.blocked_reason) return { lane: L.id, status: 'blocked', build: b }
  let q = await court(L, b, 1)
  let round = 1
  while (bad(q) && round <= MAXREP) {
    const r = await agent(`Target: worktree ${b.worktree}. cd there && pwd && git branch --show-current && git rev-parse HEAD.
${DOCTRINE}
Repair round ${round} for lane ${L.id}. Task: ${L.task.slice(0, 1500)}
Court verdicts to answer: ${JSON.stringify(q).slice(0, 9000)}
Fix with NEW commits (never rewrite). Rerun the lane gate (${L.gate}); refresh and validate ${RDIR}/${L.id}.json; commit -F.
If a refutation is wrong, include the disproving command output in notes instead of changing code.`,
      { label: `${WAVE}:repair${round}:${L.id}`, phase: 'Repair', schema: BUILD })
    if (r) b = r
    round += 1
    q = await court(L, b, round)
  }
  if (bad(q)) return { lane: L.id, status: 'refuted', build: b, court: q }
  const m = await integrate(L, b)
  return { lane: L.id, status: m && m.merged ? 'merged' : 'unmerged', build: b, court: q, integrate: m }
}

const byId = {}
LANES.forEach(L => { byId[L.id] = L })
const memo = {}
const run = (L) => {
  if (!memo[L.id]) {
    memo[L.id] = (async () => {
      const deps = await Promise.all((L.after || []).filter(d => byId[d]).map(d => run(byId[d])))
      const failed = deps.filter(d => !d || d.status !== 'merged').map(d => (d && d.lane) || '?')
      if (failed.length) {
        log(`${L.id}: not started, dependencies not merged: ${failed.join(', ')}`)
        return { lane: L.id, status: 'blocked-dep', deps: failed }
      }
      try { return await lane(L) } catch (e) { return { lane: L.id, status: 'error', error: String(e) } }
    })()
  }
  return memo[L.id]
}

log(`${WAVE}: ${LANES.length} lanes: ${LANES.map(L => L.id + (L.after && L.after.length ? '<-' + L.after.join('+') : '')).join(', ')}`)
const results = await Promise.all(LANES.map(run))
return {
  wave: WAVE,
  summary: results.map(r => ({ lane: r.lane, status: r.status, head: r.build && r.build.head_sha, int_head: r.integrate && r.integrate.int_head })),
  results,
}
