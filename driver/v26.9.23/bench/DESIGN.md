# CE23-12 Non-LLM Benchmark Design (v26.9.23)

Substrate design capital for CE23-12 of the Chatman Ecosystem v26.9.23 contract. It is not repo code.
Standing of this document: **candidate**. BENCHMARK_DESIGN_ALIVE is **UNKNOWN**. It becomes ALIVE only
when orders CE23-12-BD-01..09 (`orders.json`) land and the CE23-12 design court passes.
NON_LLM_OPERATIONAL_ALIVE is **UNKNOWN for every class**: executed unseen members n = 0.

| item | value |
|---|---|
| operator prose (O* by testimony) | `chatman-ce23-12-bench.md` sha256:4146d688…b485; `chatman-ce23-12-standings.md` sha256:80091c45…b2d2 |
| binding refinement | CE23-12 for v26.9.23 = BenchmarkDesign ∧ MSAContract ∧ GeneratedQualificationPlan = BENCHMARK_DESIGN_ALIVE |
| frozen release subjects (read only) | xaas-int `e999e62` (release/FREEZE.json; REL-A2 may re-freeze), ggen_igniter-int `3937a4f` |
| trace targets | `candidates/chatman-ce23-12-{bench,standings}.ttl`: 19 + 30 `sj:Proposition`, 46 `sj:requiredBy ce23:CE23-12`, emitted and re-checked by xaas `scripts/sjira/prose_spans.py` (sha256 86a0e9b3, commit 2244d8e1), `CHECK OK`, refusals 0 |
| vocabulary + instance draft | `ontology-draft.ttl` (sha256 3a176989…), 1,795 triples; 2,380 with candidates |
| draft qualification | `BENCH-design/tools/verify_draft.py`: 20 PASS / 0 FAIL, byte-identical over 3 runs (log sha256 6347a8ca…) |
| inputs | 7 scan reports + 7 skeptic re-runs of workflow wf_a0af447e-5fa (extracted to `/private/tmp/claude-501/v23-scratch/BENCH-design/reports/`) |
| executor | macOS 26.2 arm64 (Darwin 25.2.0) only; OS factor UNSUPPORTED |

## 1. The two standings

Namespaces: `nlb:` = `https://ggen.dev/nonllm-bench#` (vocabulary; target
`ggen-marketplace/packs/nonllm-class-qualification-pack`), `ce23:` = `https://chatman.dev/release/v26.9.23#`
(instances; target `chatman-ecosystem release/v26.9.23/bench/design.ttl`). Both standings exist as
individuals: `nlb:BENCHMARK_DESIGN_ALIVE` and `nlb:NON_LLM_OPERATIONAL_ALIVE`, with the intermediate record
`nlb:BENCHMARK_QUALIFIED`. Each carries `nlb:acceptancePredicate` nodes and `nlb:doesNotImply`.

### 1.1 BENCHMARK_DESIGN_ALIVE = D ∧ M ∧ A (part of v26.9.23)

Each predicate traces to the operator line it implements (the `ce23:P-*` IRI). "Draft" is the value
observed on `ontology-draft.ttl`. It shows the predicate is evaluable and not vacuous. It does not admit
anything: admission needs the owning order.

| id | conjunct: operator line | exact predicate | witness | anti-vacuity mutation (must refuse) | draft |
|---|---|---|---|---|---|
| BD-D1 | D: "benchmark ontology admitted" (P-b29a6e57) | nlb vocabulary, shapes and gates are merged in `nonllm-class-qualification-pack` at an exact ggen-marketplace SHA. The qualification consumer syncs in ggen strict mode. Every gate/shape admits the clean fixture and refuses each registered mutation on rdflib, pyoxigraph and pyshacl | `ggen sync run && python3 scripts/verify.py` | the 16 draft mutations (§12) | not admitted (UNKNOWN) |
| BD-D2 | D: "candidate classes enumerated" (P-0bf49a6a) | ≥ 5 `nlb:BenchmarkClass` with claimStatus `KNOWN_CANDIDATE` and a bound `nlb:classToolchain`. Preserved, blocked and refused classes are enumerated too | ASK in `ce23:BD-D2` | demote json to PRESERVED (M12) | true |
| BD-D3 | D: "membership tests identified" (P-8bc683ae) | every KNOWN_CANDIDATE has a membership predicate with a `TYPED_OUTPUT` clause and a `TRIAL_REPAIR` or `INDEPENDENT_SEMANTIC` clause. A declared label alone is refused | ASK `ce23:BD-D3` + `nlbsh:KnownClassShape` | drop the ggen class's typed-output clause (M11) | true |
| BD-D4 | D: "independent verifiers identified" (P-a233ad30) | every KNOWN_CANDIDATE has an independent verifier whose `nlb:implementationFamily` differs from its repair tool's | ASK `ce23:BD-D4` + shape | CPython-ast verifier relabelled `ruff-rust` (M8) | true |
| BD-D5 | D: "near-miss/UNKNOWN falsifiers identified" (P-e86f34ae) | every KNOWN_CANDIDATE has ≥ 3 `nlb:NearMissCase` expecting `es:UNKNOWN` with a typed reason, and none is `nlb:inClass` | ASK `ce23:BD-D5` + `nlbsh:NearMissShape` | near-miss expecting ALIVE (M1); rust near-misses cut to 2 (M16) | true |
| BD-D6 | D: CTQ tree (P-631296cc) | 15 `dflss:CTQ`, each with the 5 `req:AdmittedCtq` fields: trace, measure, verification method, negative case, control chart | ASK `ce23:BD-D6` | untraced CTQ (M9) | true |
| BD-M1 | M: "measurement/receipt/OCEL model defined" (P-e3fad592) | 7 RTY stages, each with an OCEL event type, covered morphisms and an `instrumentedToday` flag. The receipt field set names `uname_sm`, `actuator_toolchain` and `factor_levels` | ASK `ce23:BD-M1` | Admit stage loses its event type (M14) | true |
| BD-M2 | MSA contract (P-22dff21d + 7 MSA questions) | every `nlb:MSAProperty` is covered by an `nlb:MSACourt` with a command and a status for today | ASK `ce23:BD-M2` | delete court M2 (M15) | true |
| BD-A1 | A: "DOE support matrix generated" (P-2d647d6e) | factor-standing, design-matrix and ci-matrix are ggen projections of the factor graph. Computed resolution = declared resolution ≥ IV. UNSUPPORTED factors appear only in `not_varied`. Regeneration is byte-identical | `ggen sync run`, then the resolution gate | generator E = AB (I = ABE, resolution 3); OS given a column (M7) | shape part true; projection not generated |
| BD-A2 | A: "statistical acceptance rules generated" (P-9224895d) | tiers and exact `nlb:BoundRow`s come from the kernel and agree with a second implementation to 1e-9. The overclaim shape compares against the exact (n, x) row, covers x > 0, and checks n against distinct receipts | `evidence_tiers.py --check` + shapes | M2–M6 | shapes true; rows hand-entered in the draft |
| BD-A3 | A: corpus + split (P-87719c71, P-f3bf6d9e) | every KNOWN_CANDIDATE declares Dev(C), reachable tier with and without synthetic members, and cluster count. Train and Test are disjoint by subject digest AND patch-id | ASK `ce23:BD-A3` | a Train/Test patch-id collision (M13) | true |
| BD-A4 | PLAN: "benchmark work orders generated" (P-eb6bf51d) | the qualification-plan CONSTRUCT emits one tuple-complete `sj:WorkOrder` per (class × B1..B6 × next tier) and per MSA court. `compile_prose --check` is byte-identical | commands in `ce23:BD-A4` | delete one B5 order (then `--check` exits 1) | not generated (`orders.json` is the hand-assembled reference) |
| BD-A5 | A: "all generated artifacts trace to operator prose" (P-354dcc1e) | every design node is `prov:wasDerivedFrom` an `sj:Proposition` whose span re-verifies against the committed prose bytes | `prose_spans.py check` ×2 + `nlbsh:TraceShape` | untraced node (M9); one byte changed in a span | true on the draft (0 dangling targets) |
| BD-A6 | no hand-written suite (P-d5b3bfcf, P-d357273c) | definitions, case manifests, reports and CI matrix carry a GENERATED header and regenerate byte-identically over `out/`. The `.ggen-v2` chain hash is excluded because it advances by design | double `ggen sync run` + sha256 | hand-edit a manifest | not generated |
| BD-X1 | non-implication (P-e4d899e1, P-dc3d8f62) | no ClassStanding of kind NON_LLM_OPERATIONAL_ALIVE or BENCHMARK_QUALIFIED is in state `es:ALIVE` without unseen-execution receipts | ASK `ce23:BD-X1` + `nlbsh:OperationalStandingShape` | set a class standing ALIVE (M10) | true |

BENCHMARK_DESIGN_ALIVE holds iff all 15 rows hold on the exact chatman-ecosystem SHA that carries the
design, with the admitted pack SHAs as inputs. The court is order CE23-12-BD-09. It emits a receipt with
`non_llm_operational: UNKNOWN` for each class.

### 1.2 NON_LLM_OPERATIONAL_ALIVE(C) (successor; never promoted by design)

NonLLMOperational(C) = BenchmarkDesign ∧ MSA_ALIVE ∧ UnseenExecution(C) ∧ StatisticalQualification(C)
∧ ZeroLLM(C) ∧ Replay(C). It is always stated with its tuple (§2) and tier. It is never a bare ALIVE.

| id | conjunct | exact predicate |
|---|---|---|
| OP-1 | Design | BENCHMARK_DESIGN_ALIVE holds on the design-graph digest from which the executor artifacts were generated. A new digest invalidates the standing (validity scope) |
| OP-2 | MSA_ALIVE | every MSACourt M0–M11 is ALIVE on its own receipts, with ≥ 30 independent units each and 0 defects on miss, false-accept and stale-accept. Cohen's kappa is defined: both verifiers judged good and bad items. Every verifier disagreement is routed UNKNOWN |
| OP-3 | UnseenExecution(C) | n = COUNT(DISTINCT subject digest) of Test-split members of C. Test members are outside Dev(C) and deduped by digest and patch-id. Each needs a receipt from the generated executor run under `env -i`, fresh HOME, clean exact-SHA checkout, no transcript and no LLM credential. DISCOVERY needs n ≥ 30 |
| OP-4 | StatisticalQualification(C) | claimed bound ≥ exact Clopper-Pearson(n, x). Tier = the highest tier with n ≥ tierN and exact bound ≤ tier bound. FTY, RTY and P(false-KNOWN) are reported with 95% bounds. P(false-KNOWN) is measured on ≥ 30 B6 near-misses with 0 false admissions for DISCOVERY |
| OP-5 | ZeroLLM(C) | LLM invocations on the KNOWN path = 0 (c-chart, zero tolerance). The generated provider guard refuses every B2 hidden-provider control. No LLM binary is on the court PATH |
| OP-6 | Replay(C) | every unseen receipt replays: the recipe re-executed on the base gives the same path-normalized `git write-tree` digest, and evidence replay is identical. Divergence = 0. An unobserved replay counts as a defect |

### 1.3 The non-implication, mechanically

BENCHMARK_DESIGN_ALIVE ⇏ NON_LLM_OPERATIONAL_ALIVE (ce23:P-0da102e0: "cannot be established until the
generated executor actually runs the test corpus"). It is enforced three ways:

1. `nlb:BENCHMARK_DESIGN_ALIVE nlb:doesNotImply nlb:NON_LLM_OPERATIONAL_ALIVE , nlb:BENCHMARK_QUALIFIED`.
2. OP-3 needs receipts, and the design graph contains none. Every class tuple is at n = 0 in state UNKNOWN,
   with upper bound 1.0 and tier BELOW_DISCOVERY.
3. `nlbsh:OperationalStandingShape` and `nlbsh:ClassStandingShape` refuse an ALIVE operational tuple that
   lacks: DISCOVERY-tier evidence; ≥ n distinct receipt digests; MSA ALIVE; 0 LLM invocations; 0 replay
   divergence. They also refuse such a tuple if it lists an UNSUPPORTED factor as varied. Mutation M10 is
   refused by both the shape and ASK BD-X1.

## 2. Evidence-volume standing tuple and tiers

Standing(C) = (C, kind, tier, n, n_real, n_synthetic, clusters, operators, defects, confidence,
upper failure bound, bound method, environment scope, varied factors, unsupported factors, receipts).
The draft encodes this as `nlb:ClassStanding`. Counting rules:

- **n** counts distinct subject digests of executed Test members (`nlb:unseenExecutionReceipt`), never
  executions. Repeated runs on one subject feed MSA repeatability, not n. Mutation M4 refuses 30
  observations on 1 case. That is the pseudo-replication that the prior-art skeptic found the candidate
  report admitting.
- **n_real and n_synthetic** are reported separately. So are clusters (repositories) and mutation
  operators. Independence is only partial: python's 65 unseen members come from one repo, and generated
  drift's 13 come from one repo.
- **Bound**: exact one-sided Clopper-Pearson at 0.95: p_U = BetaInv(0.95; x+1, n−x). For x = 0 this is
  1 − 0.05^(1/n); for n = 0 it is 1. A claim below the exact (n, x) row is refused, including x > 0 and
  n between tiers (M2, M3, M6).
- **Environment scope** is written from receipts (`uname_sm`, actuator toolchain), not from the host.
  Today no receipt carries an OS/arch identity, so scope = "macOS arm64, unreceipted; OS=UNSUPPORTED".

Tier table. Values were recomputed in this lane: scipy 1.17.1 `beta.ppf` equals `1-0.05**(1/n)`. They
match the stats lane's three evaluators and the prior-art `evidence_tiers.py` to 1e-9.

| tier | N | 0-defect p_U (95%) | rule of three | 1-defect p_U | yield lower bound | min n at 0 defects for the nominal bound |
|---|---|---|---|---|---|---|
| BELOW_DISCOVERY | < 30 | n=9: 0.283; n=20: 0.139 | — | — | — | — |
| DISCOVERY | 30 | 0.095034 | 0.100 | 0.148596 | 0.904966 | 29 (≤ 10%) |
| QUALIFICATION | 100 | 0.029513 | 0.030 | 0.046560 | 0.970487 | 99 (≤ 3%) |
| OPERATIONAL | 300 | 0.009936 | 0.010 | 0.015715 | 0.990064 | 299 (≤ 1%) |
| SCALE_3000 | 3000 | 0.000998 | 0.001 | 0.001580 | 0.999002 | 2995 (≤ 0.1%) |

Consequences for the first crown thresholds, which are point estimates:

- FTY ≥ 95% with a 95% lower bound needs n ≥ 59 at 0 defects.
- RTY ≥ 90% with a lower bound needs n ≥ 29.
- ">= 30 unseen/class" certifies failure rate < 9.5%. It does not certify 99%.

## 3. KNOWN classes

The discovery probes ran under `env -i` with a fresh HOME. The definitions below apply the skeptic
corrections, most importantly: **the verifier toolchain is part of class identity**. On the full
ggen_igniter@3937a4f tree, Elixir 1.16.0 and 1.18.4 flag files while 1.19.5 and 1.20.2 pass. On gymact,
ruff 0.14.0 and 0.16.7 flag different file sets. So `nlb:classToolchain` is bound into membership and into
the receipt. It is not a DOE factor. The DOE factor is the executor-node toolchain (§5).

### 3.1 The five KNOWN_CANDIDATE classes (first-crown set)

| class | repair (identity) | verifier | independent verifier (basis) | membership (observed) | UNKNOWN near-neighbours | define-lane evidence |
|---|---|---|---|---|---|---|
| format_drift/elixir, plain `.formatter.exs` | `mix format`, Elixir 1.18.4/OTP 27.2.4 (target pin; court pin target_suites.ex:484; recipe:mix-format config.exs:293-299) | `mix format --check-formatted`, stdin closed | Elixir 1.20.2 `Code.string_to_quoted` AST equality (different mechanism) | stderr token `mix format failed due to --check-formatted`; no parse or deps error; `.formatter.exs` equal to base; no GENERATED header; trial repair passes; delta ⊆ inputs; AST equal | missing `end`; syntax + drift; GENERATED file; import_deps without deps; line_length change; formatted semantic change | 5/5 MEMBER, 7/7 near-neighbours, 5/5 injected bad rejected; real CI member bootstrap.ex:245 (run 35895255818) |
| format_drift/python | `ruff format` 0.16.7 (gymact/uv.lock:4367-4368) | `ruff format --check --output-format json` | CPython 3.14 `ast.dump` (different implementation) | JSON violations non-empty; no GENERATED header in the first 6 lines; pyproject equal to base; trial repair; delta ⊆ scope; AST equal; exit 2 → UNKNOWN | missing paren; GENERATED file (admission.py, registry.py); config change; lint-only F401 (different causal class) | 9/9, 5/5, 9/9 |
| format_drift/rust | rustfmt 1.9.0 (toolchain 1.97.1) | `rustfmt --check --edition <Cargo.toml>` | rustc nightly-2026-09-14 `-Zunpretty=ast-tree` (different mechanism; too strict: 4/11 false-UNKNOWN; order OP-23) | `Diff in` token, no stderr error; edition read from Cargo.toml; no rustfmt.toml change; no @generated; trial repair; AST digest equal | missing brace; @generated; `max_width` added; wrong edition (E0670) | 7/11 admitted, 4/4 near-neighbours |
| json_canonical_drift, declared scope | jq 1.8.1 `-S --indent 2` | `canon_json_check.py` (CPython json) | CPython json vs jq (different implementation) | NOT_CANONICAL lines only; path in the declared scope; no INVALID or DUPLICATE_KEYS; trial jq repair satisfies python; values equal; numeric literal multiset unchanged | duplicate key; `1e3` (jq writes `1E+3`); trailing comma; writer-owned indent-4 file | 9/9, 6/6; scope must be declared (§4) |
| ggen_generated_projection_drift | ggen 26.9.18 `sync run` | dry-run JSON `decisions` not all `skipped: unchanged` (dry-run exits 0 on drift) | ggen 26.8.24 byte identity (different generator identity, C20) | typed decisions; trial sync then clean dry-run; delta ⊆ declared outputs (.ggen/, .ggen-v2/, ggen.lock excluded); second identity reproduces bytes | template syntax error; Turtle error; FM-CONFIG-003 old schema; FM-PACK-008/010 pack fetch or hash | 5/5, 3/3; 5/5 agreement between the two generators |

Exit codes alone are ambiguous in four places, and each membership rule keys on typed output:

- `mix format --check-formatted` exits 1 for drift, for a parse error and for missing deps.
- `project.py --check` exits 1 for drift and for a Turtle error.
- `ggen sync --dry-run` exits 0 on drift.
- `cargo update --locked --dry-run` exits 0 on a drifted lock.

### 3.2 Preserved, blocked and refused classes

These options are kept and not deleted:

- **PRESERVED:** cargo_lock_workspace_member_drift (15 real unseen; verifier `cargo metadata --locked --offline`),
  gitlink fast-forward roll (21 real unseen), uv_lock_project_drift, mix_lock_unused_entries (warm-only),
  doc_projection_drift (dfcm catalog), and format_drift/elixir with import_deps (xaas; 14 surrogate-measured).
- **BLOCKED:** release_version CalVer. Its repair tool is defective: `fix_version_policy!` drops the final
  newline, leaves `source_ref` stale and allows downgrades (OP-21).
- **NOT_KNOWN (B6 neighbours):** ruff lint autofix (not semantics-conserving), yaml normalization (no
  fleet form), schema repair (no deterministic repair), semver and prose-bearing release (a decision),
  registry relock (network), clippy/credo lint repair (no offline oracle).
- **OUTSIDE_BOUNDARY:** toml (taplo absent) and gofmt (only remo, which is REFUSED).

## 4. Corpus plan

Real members are historical single-parent repair commits F with P = F^ as the drifted subject. They were
mined read-only from 20 fleet repos (35,412 commits → 1,741 candidates → 698 (class, commit) entries →
340 verified). Synthetic members come from declared mutation operators. The two are always counted
separately.

**Split rule** (skeptic-corrected; order OP-14 implements it):

| rule | text |
|---|---|
| R1 content identity | dedupe by subject digest (sha256 of sorted `path:P-blob-oid`) AND by patch-id. `split.py` deduped only on (class, stratum, id), which let xaas patch-id b6fbdc21 count twice |
| R2 leave-repo-out | Dev(C) = the repos whose subjects built, tuned or admitted C's machinery; they are never Test. Elixir: ggen_igniter (fmt-1, me-1, me-2 and the me-1 predicate). For classes without machinery: the repo with the fewest verified members, designated now and frozen |
| R3 | drop any Test member whose digest or patch-id equals a Dev member's |
| R4 temporal | non-Dev members after T_freeze(C) are Test. R2 takes precedence, so the episode subjects stay Train. Elixir T_freeze = xaas 1db4eb16, 2026-09-22T22:23:17-07:00. R4 is unimplemented today |
| splits | {Train, Validation, Test}. Validation is for MSA only and is never counted. The candidate vocabulary collapsed Validation into Train |
| operator holdout (synthetic) | at least one Test operator is not used in Train. Otherwise synthetic n measures subject variety, not class transfer |
| base gate | refuse a case whose base fails the class court under the class pin: BUILD_BROKEN(base_not_clean). ggen_igniter@3937a4f fails its own format court under 1.18.4, so every synthetic case based there starts broken |

**Reachable tier per class.** "Real" counts real unseen members that are membership-verified but not yet
executed.

| class | real unseen (clusters) | Dev(C) | tier, real only | synthetic capacity (generator) | tier with synthetic | worker today |
|---|---|---|---|---|---|---|
| elixir (plain) | 26: ash_a2a 15, ash_surface 10, ggen-marketplace 1 (3) | ggen_igniter | BELOW_DISCOVERY | ≥ 645 clean sites outside Dev (Episode.drift/1 EXISTS, 1 operator) | OPERATIONAL (single-operator caveat) | EXISTS, bound to ggen_igniter |
| python | 65: autofde-lab (1) | gymact | DISCOVERY | ≤ 3,095 (def-spacing generator UNSUPPORTED) | OPERATIONAL | UNSUPPORTED |
| rust | 63: ggen 43, ferroplan 17, frozen-duckdb 3 (3) | open-ontologies (designated) | DISCOVERY | ≤ 1,467 (fn-spacing UNSUPPORTED) | OPERATIONAL | UNSUPPORTED |
| json canonical | 22 data members (6) | ferroplan | BELOW_DISCOVERY | re-serialization under the declared form (UNSUPPORTED) | QUALIFICATION (corpus-size dependent) | UNSUPPORTED |
| ggen projection | 13: beam4pm (1) | ggen | BELOW_DISCOVERY | ≤ 1,397 marked files, an upper bound (perturbation UNSUPPORTED) | OPERATIONAL | UNSUPPORTED |
| cargo ws (preserved) | 15 (3) | ash_a2a | BELOW_DISCOVERY | 86 packages (desync UNSUPPORTED) | QUALIFICATION | UNSUPPORTED |
| gitlink ff (preserved) | 21 (2) | ggen | BELOW_DISCOVERY | 83 gitlinks × depth (rewind UNSUPPORTED) | OPERATIONAL | UNSUPPORTED |

With real members only, no class reaches QUALIFICATION. Only python and rust reach DISCOVERY. Pooled
format drift (189) is not a qualification unit, because its four strata need four different recipes.
Reaching the crown's "≥ 5 classes × ≥ 30 unseen" needs the synthetic generators (OP-15) for elixir, json
and ggen projection. The tuple must state the synthetic share.

JSON canonical scope must be declared per path in RDF before the class can run. Of xaas
docs/sjira/v26.9.23: 74 files are canonical; 3 are Elixir-written receipts that differ only by uppercase
`\u001B` escapes; 1 is indent-4; 1 is indent-1 and unsorted; 4 are unsorted; 1 is compact. The draft
declares sorted keys, indent 2, LF and lowercase escapes, and excludes writer-owned episode receipts.

## 5. DOE (B3 variation court)

The factor support matrix is `ce23:factor-*` in the draft. It absorbs the B3 lane's `b3-factors.ttl`,
which was generated and replayed byte-identically by ggen 26.9.18.

| factor | support | levels (low / high) | reason |
|---|---|---|---|
| A cold/warm | VARIED | warm / cold-A (fresh HOME seeded offline, pinned ASDF/RUSTUP/CARGO homes, HEX_OFFLINE) | cold-A end-to-end is UNVERIFIED: 178 deps built in 1,231 s, then cargo enoent from PATH. Cold-B needs network and is excluded |
| B concurrency | VARIED | 1 / 4 (distinct MIX_TEST_PARTITION) | expected defects: `System.unique_integer` temp dirs collide across OS processes; worktree provisioning is check-then-create |
| C path | VARIED | ≤ 80 B / 228 B with spaces (subject clone + `--work-root`) | executor checkout held FIXED (cold × spaced executor path is BUILD_BROKEN); replay needs a path-normalized digest |
| D environment | VARIED | `env -i` allowlist / sanitized ambient | raw ambient is not a level: it is the B2 hidden-provider control (guard REFUSED with 12 vars, 2 binaries) |
| E toolchain (executor node) = ABC | VARIED | as-built 1.19.5/OTP 28.3.1 / pinned 1.20.2-otp-28 | verifier toolchain is bound in the class (§3), not varied |
| F ordering = BCD | VARIED | canonical / seeded permutation within the member DAG | me-2 reads me-1's experience, so order is only free among independent members |
| repo size | PARTIAL | shallow / full history | weak contrast (26 MB vs 29 MB .git); tree size UNSUPPORTED (one registered court suite). Reserved G = ACD → 2^(7-3) resolution IV, still 16 runs |
| OS | UNSUPPORTED | macOS only | see below |

**OS statement:**

- Only macOS 26.2 arm64 executes the BEAM executor.
- Docker Desktop and colima provide an aarch64 Linux kernel, but every cached image lacks
  Erlang/Elixir/Rust. There are no aarch64-linux NIFs.
- A Linux level needs an operator-approved image pull (OP-24).
- Until then **cross-OS robustness remains outside the demonstrated evidence ceiling**. No OS level
  appears in any run (gate: `nlbsh:FactorShape`, mutation M7).
- Every receipt and report states this.

**Design:**

- Type: 2^(6-2), 16 runs, resolution IV. Generators E = ABC and F = BCD, so I = ABCE = ADEF = BCDF.
  It is balanced and orthogonal; recomputed in this lane.
- The column assignment was solved, not hand-picked: 96 of 720 assignments put every evidence-cited
  suspected interaction in its own alias chain, and the lexicographic first was chosen.
- Two-factor alias chains: AB=CE, AC=BE, AD=EF, AE=BC=DF, AF=DE, BD=CF, BF=CD.

**Sizing:**

- The B3 robustness bound counts executions: m members per run, and the same m in every run, so each
  member acts as a block.
  - m = 4 → 64 executions, DISCOVERY-grade bound 0.0457.
  - m = 8 → 128, bound 0.0231.
  - m = 20 → 320, bound 0.0093.
- DOE executions count toward class-transfer n only when every run uses fresh unseen members:
  r = 2 → 32, r = 7 → 112, r = 19 → 304.
- With zero defects everywhere, the DOE falsifies and attributes; it does not estimate effects.
  Factor effects use Fisher's exact test on p(+) − p(−).

**Execution rules:** a seeded run order (`runOrderSeed` in the receipt); host load average recorded as an
uncontrolled covariate (observed 32–137); 8 cold runs at ≥ 20 min each.

## 6. MSA contract

This lists the properties that hold today per the MSA scanner and skeptic (scratch O), and the courts that
must be generated. Each court records (n, defects, 95% bound, scope = macOS). Today every row is below
N_discovery except where noted.

| court | property (operator question) | status today | evidence | needs |
|---|---|---|---|---|
| M0 | repeatability ("same artifact, same verdict?") | HOLDS on the observed domain | format check 20/20; court suite 20/20 (argv_sha256 26fd0160); validate_receipt 10/10; route/hops/conserve 10/10; GC23-10 cold replay 4/4 (e24bff79). All n < 30. Define-lane rerun 97/98: one timeout from inherited stdin and a Hex prompt, and there is no rerun script | generated trial plan with r ≥ 30, stdin closed |
| M1 | classification agreement of digest encoders | FAILS | Python vs xaas 161/210. Jason writes uppercase hex for U+000B, U+000E, U+000F, U+001A..1F; Python writes lowercase. This falsifies semantic_drive.ex:195-196. Recorded fmt-1 values 10/10 agree | one RFC 8785 kernel + differential corpus (OP-11) |
| M2 | stale receipt detection | FAILS (validator); HOLDS (episode replay 2/2) | validate_receipt.py:19-24 checks existence only; a stale fmt-1 receipt was ADMITTED (n_eff 1) | currency court (OP-12) |
| M3 | mutation sensitivity of R projections | FAILS | 13/13 schema-owned mutants refused. 4/7 court-owned mutants escape every court: acceptance false with ALIVE, commit ≠ subject, files outside scope, replay cmd `true` | field-binding court (OP-12) |
| M4 | membership boundary | FAILS | membership = declared label (machine_experience.ex:103-108, 222-248; episode.ex:57; effective n = 1). A near-miss routes KNOWN, claims a lease, and is refused only after DO | pre-resolve probe (OP-04) |
| M5 | typed verifier output | FAILS | `exit_status` format (court_receipt.ex:66-75) conflates drift and syntax; output text separates them 34/34 | typed output classes (OP-04) |
| M6 | sensitivity to formatted semantic corruption | FAILS | 3/5 behaviour-changing formatted mutants pass the format court (2/5 were doc edits: generator bug) | AST-equivalence court + doc-only rule (OP-13) |
| M7 | cached state / cold reproducibility | FAILS_CLOSED | cold graph side BUILD_BROKEN → UNKNOWN exit 75, never a false verdict. Format verifier warm vs cold 100/100 identical; cold vs warm Elixir outputs identical once built | hermetic cold rebuild court (OP-13) |
| M8 | independent labels | UNMEASURED | case generator mislabelled SYN-unclosed_paren; the observed-membership prototype only agreed with the generator's own labels | label oracle (OP-13) |
| M9 | ordering invariance | HOLDS on the observed domain | 0/250 verdict diffs over 5 orders (unit of independence = 5 permutations); conserve 5/5; route 5/5 | keep in the trial plan |
| M10 | LLM-isolation instrument | FAILS | guard accepted GEMINI_/GOOGLE_/OLLAMA_/MISTRAL_/CODEX_ variables and codex/gemini/ollama/openai binaries; court PATH includes /usr/local/bin/claude (target_suites.ex:636) | generated denylist + network fence (OP-05) |
| M11 | toolchain binding | FAILS | 3937a4f verdict changes with the Elixir version; int `_build`s compiled by 1.19.5/OTP 28 against pins 1.18.4-otp-27 and 1.20.2-otp-28; ERTS from ~/.erlmcp | binding court (OP-13) |

Units at or above N_discovery exist only for the 30 distinct formatting mutants (bound 0.095), the 160 hop
mutants (0.019) and the 105 xaas-vs-ggen_igniter digest pairs. MSA_ALIVE = all of M0–M11 ALIVE. It is
false today, and nothing in v26.9.23 requires it. It is conjunct OP-2 of the successor.

## 7. B2 negative controls and B4 fault-injection points

The B2 controls come from the operator list. Required: FalseAccept = 0.

| control | expected | today |
|---|---|---|
| changed requested outcome, same descriptor | REFUSED(tuple_digest_mismatch) | typed (semantic_drive.ex:343-380) |
| malformed tuple digest | REFUSED(tuple_digest_mismatch) | 160/160 single-hop mutants refused; all-hop forgery caught only by the GC23-4 carrier |
| missing capability | REFUSED(unregistered_capability) | typed (semantic_drive.ex:1691) |
| authority escalation (`authority_ceiling=DO`) | REFUSED(authority) | UNVERIFIED on the drive path |
| unverifiable consequence | REFUSED(postcondition_unverified) | typed |
| intentionally wrong generated file | verifier rejects | 49/49 injected bad rejected (define lane) |
| corrupted receipt | REFUSED | 4/7 court-owned escape (M3) |
| stale subject SHA | DIVERGED(subject_changed) | episode replay yes; validator no (M2) |
| hidden LLM provider | REFUSED(llm_credential_present) | false-accepts (M10) |

The B4 points are the `ce23:fi-*` nodes. Morphisms: Observe → Admit → Select → Construct → Authorize →
DO → Receipt → Replay.

| morphism | fault | expected typed state | existing typing | seam |
|---|---|---|---|---|
| Observe | not on frontier / invalid graph | BLOCKED:not_on_frontier, REFUSED(order_not_in_work_graph) | semantic_drive.ex:664-693, 2018 | PARTIAL |
| Admit | malformed digest / descriptor | REFUSED(tuple_digest_mismatch), descriptor_refused, materialize_refused | :343-380, 868, 937 | PARTIAL |
| Select | missing capability / provider down / near-miss | REFUSED(unregistered_capability), BLOCKED(provider_unavailable), UNKNOWN(not_member) with no lease | :1691; provider_unavailable 0 hits; not_member absent | UNKNOWN |
| Construct | recipe step fails / dirty tree / toolchain | REFUSED(recipe_step_failed, dirty_worktree, toolchain_unresolved) | RecipeWorker; :1316-1326 | PARTIAL |
| Authorize | escalation / lease loss | REFUSED(authority), REFUSED(lease_lost) with no duplicate DO | lease tests recipe_worker_test.exs:276-423 | UNKNOWN |
| DO | worker crash / verifier crash / crash-after-DO re-drive | typed failure; verifier_crashed with no promotion; one consequence | in-process worker (:962); MatchError → drive_step_crashed (:1398, 404-420); non-unique work_order_iri | UNKNOWN |
| Receipt | missing / corrupted between seal and project | REFUSED / non-ALIVE | :1041, 1094, 1932 | PARTIAL |
| Replay | stale identity | DIVERGED(subject_changed), R_missing_identity | semantic_replay.ex:38, 496-503 | PARTIAL |
| (any) | LLM fallback present | REFUSED + benchmark failure | guard false-accepts | PARTIAL |

## 8. Statistics definitions

Unit = one admitted KNOWN work-order execution. k = 7 stages: Observe, Admit, Route, Execute, Verify,
Receipt, Replay. α = 0.05.

| metric | definition |
|---|---|
| FTY | units passing all k stages with exactly one ActuationStarted / N |
| stage yield Y_j | pass_j / n_j, from StageCompleted events (success and refusal paths both emit) |
| RTY | ∏_j Y_j. Also report RTY_unit = pass_all / N, which equals the product only under independence |
| RTY lower bounds | Bonferroni: 1 − Σ_j p_U(d_j, n_j; α/k). Unit: 1 − p_U(N − pass_all, N; α) |
| DPMO | D / (N · k) · 10^6, observed count (not the normal-approximation prediction in wasm4pm spc.rs) |
| P(false-KNOWN) | FP / (FP + TN) over expected-UNKNOWN B6 near-misses, with CP bound. Safety CTQ. A cold-start member routed UNKNOWN is not a B6 negative (me-1 is x ∈ C) |
| CP bound | p_U = BetaInv(1−α; x+1, n−x); x = 0: 1 − α^(1/n); min n = ⌈ln α / ln(1−p*)⌉ |
| latency (one-sided USL) | σ_w = MR̄ / d2, d2 = 1.128. CPU = (USL − x̄)/(3σ_w). PPU uses s. Bissell 95% lower bound CPU − z₀.₉₅ √(1/(9n) + CPU²/(2(n−1))). USL = recipe timeout (300 s, config.exs:297) until an operator USL exists |
| Cp / Cpk | only for two-sided continuous specs; discrete correctness uses binomial measures |
| I-MR | x̄ ± 3·MR̄/1.128 (= 2.6596·MR̄; the stats lane stated 2.66 while its kernel used 3/1.128); MR UCL = 3.267·MR̄ |
| p-chart | p̄ ± 3√(p̄(1−p̄)/n_i). LCL > 0 needs n_i > 9(1−p̄)/p̄ (891 at p̄ = 0.01) |
| c / u | c̄ + 3√c̄; ū + 3√(ū/n_i) |
| g-chart | UCL = ḡ + 3√(ḡ(ḡ+1)), conforming units between defects. Used when p̄ ≈ 0: a p̄ = 0 p-chart has UCL = 0 and carries no rate information |
| MSA attribute agreement | effectiveness = correct / total; miss = bad accepted / bad (safety, CP-bounded); false alarm = good rejected / good; repeatability = identical verdicts over r; Cohen's κ = (p_o − p_e)/(1 − p_e) (STATO_0000630), defined only when both verifiers judged good and bad items |

**Where these are computed.** SPARQL 1.1 cannot: ggen refuses `math:pow` with FM-GRAPH-003. Tera can,
with bounded loops (the skeptic's probe matched scipy to 6 decimals), so this is not a generator-capability
limit. The design keeps one μ: the kernel (`evidence_tiers.py` for bounds, the BENCH-stats `stats_kernel.py`
for yields and limits) writes RDF literals, and templates only render them. This is a declared design
choice (OP-16), not UNSUPPORTED residue.

## 9. SPC plan (after qualification)

| CTQ | chart | rule |
|---|---|---|
| FTY, verifier rejection rate, UNKNOWN rate | p (subgroup = one batch run) | Phase I ≥ 20–25 subgroups before limits are more than TRIAL_LIMITS_ONLY |
| deterministic-worker failure rate, false-KNOWN, verifier miss | g | p̄ ≈ 0, so the p-chart is degenerate |
| LLM invocations, human interventions, unreceipted consequences, replay divergence, receipt defects | c with c̄ = 0 | zero tolerance: any point is a special cause |
| median / p95 latency | I-MR (d2 = 1.128) | converge with wasm4pm (lib.rs:1276-1286 uses population σ; spc.rs ProcessCapability is Pp/Ppk) |

- Special-cause detection uses Western Electric rules 1–4, via `wasm4pm spc.rs:128`
  `check_western_electric_rules` through wasmex.
- A special cause triggers a generated requalification order and sets the class standing to
  UNKNOWN(requalify). ALIVE is never assumed to last (ce23:P-e9625dff).
- Standing validity also ends when a commit touches the class's worker, verifier or pack path scope.

## 10. Generation paths (projection map)

No benchmark artifact is hand-written. The canonical sources are the pack ontology and shapes, the
design graph and the prose candidates. Everything below is a projection of them, by an existing path.

| artifact | canonical source | generator (existing path) | order |
|---|---|---|---|
| DfLSS DOE/MSA/SPC vocabulary | dflss-pack ontology.ttl | ggen-marketplace/packs/dflss-pack + `ggen sync run` | BD-01 |
| nlb vocabulary, shapes, gates | nonllm pack ontology.ttl (from this draft + candidate ec29547) | ggen sync strict + pack verify.py | BD-02 |
| evidence tiers, BoundRows, acceptance rules | kernel output | `evidence_tiers.py` → `.tera` rules | BD-03 |
| design matrix, CI matrix, factor standing, workflow yml | factor graph | `.tera` rules (precedent BENCH-B3/doe-gen/ggen.toml, byte-identical) | BD-04 |
| prose candidates | operator prose bytes | xaas `scripts/sjira/prose_spans.py` emit/check | BD-05 |
| class catalog, CTQ tracker, MSA plan, case manifests, report, SPC chart data | design.ttl | ggen per-row `output_file` with `{{` (generation_rules.rs:563); `dflss-ctq-tracker.py.tmpl`; pack-candidate templates | BD-07 |
| benchmark work orders | CE23 candidates + design.ttl | `mix semantic_jira.compile_prose` (semantic-jira-pack) + pack `qualification_plan.construct.rq` | BD-08 |
| CE23-12 court | goal node courtCommand | semantic-jira-pack projection templates (precedent GC23-*.sh) | BD-09 |
| executor recipes, verifier suites, membership probe, LLM denylist, stage registry, receipt keys, fault tests, case JSON | nlb rows | new ggen_igniter nonllm-benchmark-pack (composes beam4pm-bench-pack, chicago-fault-injection-pack) via `mix ggen_igniter.sync --for-each` | OP-02..10 |
| corpus rows | fleet git history | admitted observe pack retiring the scratch miners | OP-14 |
| statistics results + reports | OCEL + receipts | single-μ kernel → results.ttl → `.tera` (precedent BENCH-stats/proj) | OP-16 |

Declared hand-written residue:

- the pack `verify.py` driver
- `evidence_tiers.py` and the stats kernel (single μ)
- `assign_search.py` (column solver)
- the batch runner (it consumes generated plans only)
- python/rust toolchain resolvers, the `:fault` seam, and the Ash identity migration
- the court shell bodies
- the extraction JSON, which is the one permitted LLM edge

## 11. Vocabulary crosswalk (scratch → nlb)

| scratch term | nlb term |
|---|---|
| `dflssx:support` SUPPORTED/PARTIAL/UNSUPPORTED; candidate `nlb:support` VARIED/FIXED/UNSUPPORTED | `nlb:support` VARIED/FIXED/PARTIAL/UNSUPPORTED |
| `dflssx:column`, `baseBit`, `generatorBase`, `lowLevel/highLevel` | `nlb:column`, `nlb:bitWeight`, `nlb:generatedBy`, `nlb:lowRealization/highRealization` |
| `dflssx:SuspectedInteraction` | kept in the B3 solver input (7 records, 6 distinct pairs) |
| `cb:CapabilityResult`, `StageYield`, `LatencyResult`, `ConfusionResult` | `nlb:CapabilityResult` (subclasses in OP-16) |
| `cb:` standing tuple, `cb:msaStanding` | `nlb:ClassStanding`, `nlb:msaStanding` |
| `corpus:repository`, `stratum`, `membership`, `synthetic` | `nlb:cluster`, class node per stratum, `nlb:MembershipClause`, `nlb:memberOrigin` |
| candidate `nlb:standingKind` (string) | `nlb:standingKind` → `nlb:StandingKind` individual |
| candidate gate 010 (next-tier comparison, x = 0 only) | `nlbsh:ClassStandingShape` (exact (n, x) row, tier check, pseudo-replication) |

## 12. Qualification of this draft

Commands were run in this lane. The scratch instruments are hand-written observation code (O) and are
retired into the pack `verify.py` by BD-02.

```text
python3 tools/mk_extract.py                      -> chatman-ce23-12-bench 19, chatman-ce23-12-standings 30
prose_spans.py emit/check (both files)           -> CHECK OK: 19 / 30 candidates bound; required 17 / 29 (CE23-12); refusals 0
python3 tools/verify_draft.py                    -> exit 0 (3 runs, identical log sha256 6347a8ca...)
  parsed: 2380 triples (draft + candidates); clean draft conforms (pyshacl 0.31.0)
  ASK BD-A3/D2/D3/D4/D5/D6/M1/M2/X1: True
  every prov:wasDerivedFrom target is an emitted sj:Proposition
  lawful DISCOVERY tuple (n=30, 30 distinct receipts, u=0.095034) conforms
  refused: M1 near-miss expects ALIVE, M2 n=31 u=0.05, M3 x=1 u=0.01, M4 pseudo-replication,
           M5 n=20 at DISCOVERY, M6 no BoundRow, M7 OS column, M8 same-family verifier, M9 untraced CTQ,
           M10 operational ALIVE without evidence, M11 label-only membership, M12 4 classes,
           M13 patch-id leak, M14 Admit untyped, M15 MSA court deleted, M16 2 near-misses
  RESULT: ALL CHECKS PASS
```

The files are in `/private/tmp/claude-501/v23-scratch/BENCH-design/`:
`tools/{mk_extract.py,prose_spans.py,verify_draft.py}` and `verify_draft.run{1,2,3}.log`.
Scratch is not durable (R_missing_replay) until BD-02 and BD-05 commit these checks.

## 13. Orders (`orders.json`)

The orders are sorted with generators first and topologically by `depends_on`. External dependencies:
CE23-0 (root identity), CE23-1 (release subject), V23-Q (release merge).

- **CE23-12 design, v26.9.23 (9 orders).** None of them touches xaas or ggen_igniter, so S23 stays
  unmoved.
  - BD-01: dflss-pack 0.3.0.
  - BD-02: nonllm-class-qualification-pack.
  - BD-03: tiers, bounds and acceptance rules.
  - BD-04: DOE and CI matrix projection.
  - BD-05: prose candidates in chatman-ecosystem.
  - BD-06: design graph.
  - BD-07: projections.
  - BD-08: generated qualification plan.
  - BD-09: CE23-12 design court and root-crown import.
- **NON_LLM_OPERATIONAL successor (24 orders).** They land on branches off post-merge mains.
  - Generators: OP-01 (xme promotion) and OP-02 (executor templates).
  - Executor gaps: OP-03..10.
  - MSA courts: OP-11..13.
  - Corpus and synthetic generators: OP-14, OP-15.
  - Stats kernel: OP-16.
  - DOE runner: OP-17.
  - Execution and tuples: OP-18.
  - Operational crown: OP-19.
  - SPC: OP-20.
  - Defects found by the scans: OP-21 (DoctorFixes), OP-22 (vacuous cargo-lock gate), OP-23 (rust verifier).
  - OS factor operator edge: OP-24.

## 14. Observations for the release lane (driver input, not CE23-12 orders)

- ggen_igniter@3937a4f fails `mix format --check-formatted` under its own pin 1.18.4-otp-27. The failure
  is at bootstrap.ex:245, CI run 35895255818, and was introduced by V23-B commits 9958cfc, 4165160 and
  974b31d. REL-A already tracks this as F3/F4 (ticks 2026-09-23T19-30Z). It is a KNOWN-class member, and
  its lawful repair is recipe:mix-format.
- gymact@5141f88e is not ruff-clean under its pin 0.16.7. The files are gyms/codebase.py and
  gyms/tau2_bench.py; registry.py is GENERATED. CI run 35821722894 masked this, because the format step
  was skipped. gymact is a successor repo, so this is recorded only.
- ggen/scripts/verify-cargo-lock.sh:33-34 is a vacuous gate: it passes a drifted lock (OP-22).

## 15. Falsifiers of this design and preserved alternatives

- The design is falsified if a KNOWN_CANDIDATE's near-miss acquires a lease under the generated probe
  (OP-04). It is also falsified if the executor-node toolchain factor changes a verdict: that would mean
  the class toolchain binding is incomplete.
- DOE: if cold-A cannot build end to end (OP-17), factor A becomes BUILD_BROKEN at its high level. The
  design then regenerates over five VARIED factors, as a 2^(5-1) design.
- Tier claims with synthetic members are falsified if the operator holdout is violated or a synthetic
  member is a verifier no-op.
- **Preserved alternatives:**
  - Pack home. Chosen: ggen-marketplace, which leaves S23 unmoved. Alternative: ggen_igniter
    priv/ggen/nonllm-benchmark-pack, vendored into xaas; it is used for the successor EEx twins.
  - First-crown class set. Cargo-ws or gitlink-ff can replace json or ggen projection if their generators
    land first.
  - Kernel placement. Chosen: a single μ. Alternative: Tera loops, shown capable.
