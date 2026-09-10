# BFCC

Status: **BFCC-CANDIDATE**. Canonical machine-readable constraints live in
`catalog/bfcc.toml`. This document is an explanatory projection of that manifest and
does not itself assert that any subject in the repo is BFCC-compatible.

BFCC stands for Buckminster Fuller Canon Compatibility: a ten-gate Boolean
compatibility check that projects Fuller's design-science principles onto engineering
evidence requirements, so that "this subject honors Fuller's canon" becomes a
falsifiable, re-runnable claim instead of a rhetorical one.

## Prime Directive

A subject may claim BFCC compatibility for a revision only when every mandatory,
applicable gate is evaluated against real evidence and every evaluated gate passes.
Compatibility is never a vibe, a summary judgment, or an average score across gates —
it is the conjunction of individually falsifiable gate outcomes, each backed by a
receipt field that a re-runnable command can check.

## The Ten Canon Gates

Each gate states a Fuller principle, its engineering projection into this ecosystem,
and the falsifier that would disprove a compatibility claim resting on that gate. Text
below is pulled verbatim from `catalog/bfcc.toml`'s `[[gate]]` entries.

### C — Comprehensive

- **Fuller principle:** Design must account for the total system of consequences, not
  an isolated part.
- **Engineering projection:** A change is reviewed against its full downstream
  dependency and consequence graph before merge, not just the diff's local scope.
- **Falsifier:** A subject is admitted with evidence covering only its local diff
  while a downstream dependency or consequence is left unexamined.

### A — Anticipatory

- **Fuller principle:** Design science must anticipate needs and consequences before
  crisis forces reactive, un-designed responses.
- **Engineering projection:** Failure modes and load conditions are enumerated and
  tested before production incidence, via falsifiers and pre-declared acceptance
  commands.
- **Falsifier:** A gate is evaluated with no pre-declared falsifier or acceptance
  command, so failure is discoverable only after the subject reaches production.

### D — Design

- **Fuller principle:** Solve humanity's problems through design and technology
  rather than through political or economic reform alone.
- **Engineering projection:** A subject ships as a testable, falsifiable artifact
  (code + tests + receipts), not an unverified prose proposal.
- **Falsifier:** The submitted evidence for a subject consists of prose description
  or a plan with no runnable test or receipt attached.

### S — Science

- **Fuller principle:** Derive practice from generalized, experimentally verifiable
  principles, not ad hoc convention or special-case rules.
- **Engineering projection:** Claims are backed by a re-runnable command whose real,
  pasted output is the evidence, not a description of expected output.
- **Falsifier:** A claim is admitted on a described or assumed result rather than the
  real captured output of a re-run command.

### G — Generalized Principles

- **Fuller principle:** Nature operates by a small set of generalized principles that
  hold across scales and special cases.
- **Engineering projection:** A public vocabulary term (earl:/prov:/pplan:/skos:) is
  reused before a new local term is minted; a new class exists only for a genuinely
  new concept.
- **Falsifier:** A new local class or property is minted that duplicates an existing
  public-ontology term's meaning instead of reusing it.

### Sigma — Synergy

- **Fuller principle:** The behavior of whole systems is unpredicted by the behavior
  of their parts taken separately.
- **Engineering projection:** Real cross-component integration is tested together,
  since parts behaving correctly in isolation does not establish whole-system
  correctness.
- **Falsifier:** A synergy or composed-behavior claim is asserted from isolated
  unit-test results with no composed-vs-isolated comparison actually run.

### E — Ephemeralization

- **Fuller principle:** Doing more and more with less and less — accelerating
  resource efficiency.
- **Engineering projection:** A `bfcc:ephemeralizationRatio` is measured and recorded
  per subject revision, not asserted qualitatively.
- **Falsifier:** An efficiency or resource-reduction claim is made with no measured
  ratio recorded for the subject revision.

### T — Trimtab

- **Fuller principle:** A small, well-placed intervention can leverage
  disproportionate systemic change.
- **Engineering projection:** The smallest change with the largest verified effect is
  preferred; a `bfcc:trimtabLeverage` quantity is recorded per gate evaluation.
- **Falsifier:** A large, broad-scope change is selected over an available smaller
  change with equivalent verified effect, with no leverage quantity recorded.

### W — World

- **Fuller principle:** Make a comprehensive, continuously updated inventory of world
  resources and needs the basis for allocation decisions.
- **Engineering projection:** Dependencies, costs, and consumed resources for a
  subject are explicitly inventoried and cited, never left implicit.
- **Falsifier:** A subject's evidence omits an explicit dependency/cost/resource
  inventory (the W gate is skipped entirely).

### I — Integrity

- **Fuller principle:** Integrity is the essence of everything successful —
  structural and ethical wholeness with no exploitable gap between claim and
  behavior.
- **Engineering projection:** No gap exists between a claimed standing and the
  evidence backing it; a receipt with an unbacked standing claim is malformed.
- **Falsifier:** A standing is asserted (e.g. BFCC-ALIVE) with a receipt field
  missing, empty, or contradicted by its own `evidence_per_gate` content.

## Regenerative Closure

A BFCC evaluation is not a one-time stamp. Each admitted or refused gate outcome
feeds back into the subject's own inventory and falsifier set: a passed gate becomes
reusable evidence for the next revision's evaluation, and a failed gate becomes a
permanent guard rather than a rediscovered failure. The canon closes on itself the
same way `docs/FORMAL-DISCOVERY-FACTORY.md`'s learning equation closes on ontology
state — admitted deltas and learned failures both return to the subject's standing
inventory, so the next evaluation starts from a strictly more informed base than the
last.

## Boolean Compatibility Definition

Compatibility is a strict Boolean conjunction over mandatory, applicable gates —
never an average, a weighted score, or a majority vote:

```text
BFCC(subject, revision) =
  AND over g in mandatory_applicable_gates(subject, revision) of gate_pass(g)
```

If any mandatory applicable gate lacks evidence, lacks a falsifier, or fails its
falsifier check, `BFCC(subject, revision)` is `false` for that revision — regardless
of how many other gates passed. `catalog/bfcc.toml`'s `[exclusions].terminal` list
names the specific failure patterns this definition exists to block, including
`AVERAGED_FAILED_GATE` and `FULLER_LAUNDERING` (claiming Fuller-canon alignment
without gate-level evidence).

## Receipt

A BFCC receipt for a subject/revision must carry every field below. This list matches
`catalog/bfcc.toml`'s `[receipt].required_fields` exactly, in the same order.

- `subject`
- `revision`
- `system_boundary`
- `canon_sources`
- `projection_table`
- `inventory_examined`
- `gates_evaluated`
- `evidence_per_gate`
- `falsifier_per_gate`
- `contradictions`
- `omitted_gates`
- `resource_vector`
- `eta_evidence`
- `lambda_evidence`
- `sigma_evidence`
- `unresolved_gaps`
- `standing`

A receipt missing, emptying, or contradicting any of these fields is malformed under
the I (Integrity) gate and cannot support a passing `BFCC(subject, revision)` claim.

## Ultracode Execution Doctrine

The doctrine's canonical execution order, one stage feeding the next:

```text
CANON -> INVENTORY -> MAP -> DFCM -> TRIMTAB -> IMPLEMENT -> FALSIFY
  -> EPHEMERALIZATION AUDIT -> RECEIPT
```

- **CANON** — load the ten gates and the Prime Directive as the fixed evaluation
  frame for this subject/revision; nothing downstream may redefine a gate.
- **INVENTORY** — enumerate the subject's real dependencies, resources, costs, and
  consequence graph (the W-gate input) before any design move is made.
- **MAP** — project the inventory onto the ten gates, identifying which gates are
  mandatory and applicable to this specific subject.
- **DFCM** — run the subject through the ecosystem's Design-for-Compatible-
  Manufacture option search (see `docs/architecture/dfcm-public-ontology-profile.md`)
  to surface admissible design alternatives before committing to one.
- **TRIMTAB** — select the smallest change with the largest verified effect among the
  admissible alternatives, recording a `bfcc:trimtabLeverage` quantity (the T gate).
- **IMPLEMENT** — build the selected change as a real, falsifiable artifact (code,
  tests, generated projections), never as prose alone (the D gate).
- **FALSIFY** — run each gate's falsifier against the real implementation, capturing
  actual command output, not a described or assumed result (the S gate).
- **EPHEMERALIZATION AUDIT** — measure and record the `bfcc:ephemeralizationRatio` for
  the revision (the E gate) before the subject is allowed to claim any standing.
- **RECEIPT** — emit the full receipt (see Receipt section above) recording every
  gate's evidence, falsifier outcome, and the resulting standing; a subject with no
  emitted receipt has no BFCC standing regardless of how many stages above it passed.

## See Also

- `docs/architecture/dfcm-public-ontology-profile.md` — the DfCM option-search
  machinery the Ultracode Execution Doctrine's DFCM stage invokes
- `docs/FORMAL-DISCOVERY-FACTORY.md` — the sibling doctrine document this file's
  markdown shape and tone follow, and whose Regenerative Closure model this file's
  own closure section mirrors
- `catalog/bfcc.toml` — the canonical machine-readable manifest this document
  transcribes; treat the manifest as source of truth on any future drift
