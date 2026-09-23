<!-- Provenance: operator-authored prose pasted into Claude Code session 1fecd79a on 2026-09-23 ~11:00 PT ("ultracode").
     Status: operator testimony (O* by fiat). Adds CE23-12 (DfLSS Non-LLM Operational Benchmark Crown) to the Chatman
     Ecosystem v26.9.23 contract (chatman-ce23.md); GC23-0..12 stay unchanged. Compiled through the first-mile pipeline. -->

Yes. The existing no-LLM episode is necessary but not sufficient. `fmt-1` demonstrates one executed KNOWN path end to end; it does **not** establish that non-LLM feature completion is operational as a class. 

I would add a dedicated **DfLSS Non-LLM Operational Benchmark Crown** to v26.9.23.

## Benchmark objective

Define:

$$
Operational_{NoLLM}
\neq
\exists e:\ Success(e)
$$

Instead:

$$
Operational_{NoLLM}
\iff
Capability
\land Repeatability
\land Reproducibility
\land Robustness
\land Closure
\land ZeroLLM
\land Receiptability
$$

The question is not “can one deterministic worker complete one task?”

It is:

> For a bounded class of work that the system claims is KNOWN, can the ecosystem repeatedly recognize, route, execute, verify, receipt, replay, and retire that work without semantic reasoning being repurchased from an LLM?

---

# DfLSS structure

Use **DMADV** rather than ordinary DMAIC because this is qualification of a designed capability.

| DfLSS phase | v26.9.23 interpretation                                                     |
| ----------- | --------------------------------------------------------------------------- |
| **Define**  | Define exactly which work classes are claimed KNOWN/non-LLM                 |
| **Measure** | Instrument every transition using OCEL + receipts                           |
| **Analyze** | Determine variation, failure modes, bottlenecks and hidden LLM dependencies |
| **Design**  | Manufacture deterministic worker/generator/planner/verifier paths           |
| **Verify**  | Statistical + adversarial qualification of the entire class                 |

The release should therefore add something like:

$$
GC23\text{-}13 := NonLLMOperationalQualification
$$

I would probably keep the current `GC23-0..12` contract stable and make this a **Chatman CE23 crown gate**, rather than mutating the already-admitted Semantic Manufacturing checkpoint.

---

# CTQ tree

The DfLSS **Critical-to-Quality** characteristics should be:

| CTQ                        |                            Operational measure |          Required result |
| -------------------------- | ---------------------------------------------: | -----------------------: |
| Classification correctness |              KNOWN vs UNKNOWN confusion matrix | bounded false-KNOWN rate |
| Deterministic routing      |     same admitted input → same provider/recipe |                     100% |
| LLM isolation              |      reachable LLM calls/credentials/providers |                        0 |
| Semantic conservation      |             tuple digest preserved across hops |                     100% |
| Execution success          |                completed admitted KNOWN orders |             target ≥ 99% |
| Verification sensitivity   |                   injected bad result rejected |                     100% |
| Receipt completeness       |     successful consequences with valid receipt |                     100% |
| Replay equivalence         |        replay reproduces admitted result/state |                     100% |
| Cold reconstructability    |               no transcript/session dependence |                     100% |
| Idempotence                |  repeated order does not duplicate consequence |                     100% |
| Fault containment          | typed failure instead of uncontrolled fallback |                     100% |
| Frontier closure           |         completed work leaves current frontier |                     100% |
| Class transfer             |          unseen member of known class succeeds |  statistically qualified |
| Human dependence           |   exceptional-human intervention on KNOWN path |                        0 |
| LLM dependence             |                   LLM invocation on KNOWN path |                        0 |

The critical point is **class transfer**. Otherwise we have memorized a fixture.

---

# Benchmark families

I would create **six benchmark courts**.

### B1 — Golden known-class corpus

Build a corpus of genuinely known transformations, not one fixture.

Example classes:

| Class                       | Examples                                         |
| --------------------------- | ------------------------------------------------ |
| formatting drift            | Elixir, Python, Rust, JSON, YAML                 |
| generated artifact drift    | ontology → generated projection mismatch         |
| dependency metadata drift   | lockfile/version/checksum mismatch               |
| schema repair               | missing required deterministic field             |
| release metadata            | version/tag/generated manifest updates           |
| documentation projection    | graph → deterministic docs                       |
| configuration normalization | canonical ordering/default projection            |
| known CI repair             | previously diagnosed deterministic failure class |

Each class should have:

$$
N \ge 30
$$

distinct subjects if feasible.

Thirty is useful here because it gets us out of anecdotal “worked once” territory and gives a reasonable first distribution for process capability analysis.

---

### B2 — Negative-control court

Every worker gets paired with deliberately invalid work.

Examples:

* change requested outcome while preserving same descriptor;
* malformed tuple digest;
* missing capability;
* authority escalation;
* unverifiable consequence;
* intentionally wrong generated file;
* corrupted receipt;
* stale subject SHA;
* hidden LLM provider availability.

Required:

$$
FalseAccept = 0
$$

A deterministic worker that “always succeeds” is worse than UNKNOWN.

---

### B3 — Variation / robustness court

Use controlled factors:

$$
X =
\{
OS,\ toolchain,\ repo\ size,\ path,\ concurrency,\ cold/warm,\ ordering,\ environment
\}
$$

Run a designed experiment rather than random chaos.

A simple fractional factorial design would work initially.

For example:

$$
2^{7-3}=16
$$

runs per class could cover seven binary factors without requiring all 128 combinations.

This tells us whether the no-LLM path is accidentally dependent on:

* warm caches;
* one machine path;
* environment leakage;
* execution order;
* repository size;
* concurrency;
* one specific toolchain.

That directly addresses several failures already discovered overnight.

---

### B4 — Fault-injection court

Inject failures at each morphism:

$$
Observe
\rightarrow Admit
\rightarrow Select
\rightarrow Construct
\rightarrow Authorize
\rightarrow DO
\rightarrow Receipt
\rightarrow Replay
$$

For every edge, test:

$$
EdgeFailure
\Rightarrow TypedState
$$

not uncontrolled continuation.

Examples:

```text
missing receipt      → REFUSED / non-ALIVE
worker crash         → BLOCKED or typed execution failure
verifier crash       → no standing promotion
lease loss           → no duplicate DO
stale identity       → REFUSED(subject_mismatch)
provider unavailable → BLOCKED(provider_unavailable)
LLM fallback present → benchmark failure
```

This is where BRCE becomes empirically demonstrated rather than architectural prose.

---

### B5 — Novel-member transfer benchmark

This is probably the **most important benchmark**.

For every claimed known class:

1. Build class machinery from training/known examples.
2. Freeze the implementation.
3. Generate or select **unseen instances**.
4. Execute with:

   * no LLM credentials;
   * no Claude/ZCode;
   * no transcript;
   * fresh HOME;
   * clean checkout.
5. Measure success.

Formally:

$$
Train(C) \cap Test(C)=\varnothing
$$

and:

$$
P(Success\mid x\in C,\ x\notin Train)
$$

must exceed the release threshold.

That differentiates:

> “we automated these five fixtures”

from:

> “we retired intelligence for this class.”

---

### B6 — Unknown-boundary benchmark

A non-LLM system is only safe if it knows when **not** to apply the known machinery.

Construct near-neighbor cases:

$$
x' \approx C
\quad\text{but}\quad
x'\notin C
$$

Examples:

* formatter failure caused by syntax corruption rather than formatting;
* lockfile drift caused by incompatible ABI;
* generated drift caused by ontology semantic conflict;
* CI failure with same error text but different causal path.

Expected:

$$
x' \notin C
\Rightarrow UNKNOWN
$$

not forced deterministic repair.

This benchmark measures the quality of the **admission boundary**.

---

# Statistical qualification

DfLSS should give us more than pass/fail.

For every benchmark class \(C_i\), maintain:

$$
Y_i =
\{
success,
latency,
cost,
rework,
intervention,
replay,
falseAccept,
falseReject
\}
$$

Then calculate:

$$
FTY =
\frac{FirstPassSuccess}{Total}
$$

$$
RTY =
\prod_j Yield_j
$$

across the complete process.

For example:

$$
RTY =
Y_{Observe}
Y_{Admit}
Y_{Route}
Y_{Execute}
Y_{Verify}
Y_{Receipt}
Y_{Replay}
$$

This is much stronger than reporting “97% successful executions.”

If each of seven stages is 99% reliable:

$$
0.99^7 \approx 93.2\%
$$

So the end-to-end capability is substantially weaker than the individual components appear.

---

# Process capability

For measurable continuous characteristics such as latency:

$$
C_p = \frac{USL-LSL}{6\sigma}
$$

$$
C_{pk}
=
\min
\left(
\frac{USL-\mu}{3\sigma},
\frac{\mu-LSL}{3\sigma}
\right)
$$

For v26.9.23 I would avoid pretending every attribute naturally fits Six Sigma continuous assumptions. Use \(C_{pk}\) where meaningful, and binomial defect measures for discrete correctness.

More useful discrete metrics include:

$$
DPMO =
\frac{Defects}
{Units \times Opportunities}
\times 10^6
$$

and:

$$
P_{false-known}
=
\frac{UNKNOWN\ cases\ wrongly\ admitted\ as\ KNOWN}
{actual\ UNKNOWN}
$$

The latter should be treated as a safety-critical CTQ.

---

# SPC after release

Qualification is not enough. Once ALIVE, monitor drift.

Use OCEL events to derive control charts for:

* first-pass yield;
* deterministic-worker failure rate;
* median/p95 execution latency;
* verifier rejection rate;
* replay divergence;
* UNKNOWN rate;
* human escalation rate;
* LLM invocation count;
* receipt defects.

For binary outcomes use **p-charts**.

For counts use **c/u-charts**.

For continuous latency use **I-MR** unless sampling structure justifies \(\bar X/R\).

Then:

$$
SpecialCause
\Rightarrow
StandingRequalification
$$

rather than silently assuming ALIVE forever.

---

# The benchmark crown

I would define the release predicate as:

$$
BENCH_{NoLLM}=true
$$

iff:

$$
\begin{aligned}
&N_{classes}\ge k \\
&N_{unseen/class}\ge n \\
&FalseKnown = 0 \\
&UnreceiptedActuation = 0 \\
&LLMInvocation = 0 \\
&HumanIntervention_{KNOWN}=0 \\
&TupleConservation = 1 \\
&VerifierMutationSensitivity = 1 \\
&ReplaySuccess = 1 \\
&ColdBootstrapSuccess = 1 \\
&RTY \ge T_{RTY} \\
&NoSpecialCauseDrift
\end{aligned}
$$

For the first crown, I would use something like:

```text
KNOWN classes qualified             >= 5
unseen benchmark subjects/class     >= 30
total KNOWN executions              >= 150
false-KNOWN admissions              = 0
LLM invocations on KNOWN path       = 0
human interventions                 = 0
unreceipted consequences            = 0
tuple conservation failures         = 0
mutation tests escaped              = 0
cold replay divergence              = 0
first-pass yield                    >= 95%
rolled throughput yield             >= 90%
```

Those are **initial engineering thresholds**, not timeless laws. After sufficient operational observations, the control limits should come from the actual process distribution.

---

# Benchmark artifact model

Do not make this another hand-written benchmark suite.

Canonical RDF should represent:

```text
BenchmarkSuite
BenchmarkClass
BenchmarkCase
Factor
Level
KnownBoundary
ExpectedStanding
WorkerCapability
Verifier
Falsifier
Execution
Observation
Defect
Receipt
Replay
ControlLimit
CapabilityResult
```

Then:

$$
Ontology
\rightarrow ggen
\rightarrow BenchmarkCases
\rightarrow Executor
\rightarrow OCEL
\rightarrow Statistics
\rightarrow Receipt
$$

The benchmark definitions, case generators, reports, and CI matrix should be projections.

This gives us a durable transition:

$$
UNKNOWN
\rightarrow KNOWN
\rightarrow BenchmarkQualified
\rightarrow GeneratedWorker
\rightarrow SPCControlled
$$

Once a class reaches that state, **the LLM should no longer be used to solve members of that class**.

## New CE23 requirement

I would therefore add:

$$
\boxed{CE23\text{-}12:
NonLLMClassClosureBenchmark}
$$

with the acceptance rule:

> Chatman Ecosystem v26.9.23 may claim **operational non-LLM feature completion** only when multiple known classes, including unseen members, execute through the full deterministic path under controlled variation and fault injection with zero LLM reachability, zero unreceipted actuation, bounded false-KNOWN admission, independent verification, cold replay, and statistically qualified process performance.

That is the point where “no LLM” becomes an **operational property of the system**, rather than a property of one successful demo.
