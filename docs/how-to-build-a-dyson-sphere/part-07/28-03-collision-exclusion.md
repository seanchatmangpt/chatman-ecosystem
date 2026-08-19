# 28.3 Collision Exclusion

**Parent:** [28. Orbital Invariants](28-orbital-invariants.md)

## Claim

`Collision Exclusion` is not accepted as a label-only capability. In this book it denotes a bounded object, relation, constraint, measurement, or control concern whose role must be explicit in the larger orbital invariants system. The objective is to preserve useful design freedom while refusing transformations that hide physics, authority, or evidence.

Orbital state is not a location label; it is a dynamical state with uncertainty. In the two-body approximation, orbital period satisfies T²=4π²a³/μ, where a is semimajor axis and μ is the standard gravitational parameter. Operational designs must then add perturbations, multi-body effects, solar radiation pressure, station-keeping budgets, conjunction probability, and covariance growth.

Observation becomes operational only after it is bounded. O* records exact subject identity, source provenance, units, uncertainty, validity interval, contradictions, and exclusions. UNKNOWN is preserved as a value rather than coerced into a guess. This makes later manufacture falsifiable: a design can be traced back to the measurements and assumptions it actually consumed.

Formal admission is used only where a machine-checkable invariant can be stated precisely. The critical separation is that rendering, proving, and certifying are different operations: ggen can render a candidate, Lean can discharge a theorem obligation, and mfact can bind evidence to a subject. None of those steps grants DO authority by itself.

## Model

\[T^2 = \frac{4\pi^2 a^3}{\mu}\]

Any numeric use of this relation is admitted only after units, parameter source, uncertainty, epoch, and approximation regime are recorded. Model validity is part of the subject, not metadata that may be discarded after calculation.

## Operationalization

The implementation path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. The decisive rule is that the semantic or analytical result produced in this subchapter has **no ambient execution authority**. It may change the candidate set, create a proof obligation, generate a simulation, or manufacture an intent. A consequential action still requires explicit subject identity, authority, preconditions, execution, postcondition verification, and a receipt.

A practical record for this topic should contain:

- exact subject and revision/epoch;
- observed inputs with units and provenance;
- admitted assumptions and explicit UNKNOWNs;
- candidate construction or policy;
- constraints and refusal conditions;
- required authority class: SELECT, CONSTRUCT, or DO;
- verifier and postcondition;
- receipt identity and replay method when consequence occurs;

## Evidence boundary

For `Collision Exclusion`, **inspection is not execution** and **simulation is not deployment**. A claim advances only as far as the strongest evidence actually observed. A stale ephemeris, synthetic telemetry stream, generated file, theorem about a simplified model, or successful API response cannot be silently promoted into evidence for the physical subject.

## Falsifier

The working claim for `Collision Exclusion` is falsified when the admitted subject violates a required physical invariant, the postcondition cannot be observed, the authority chain cannot be reconstructed, or replay produces a materially different result under the same subject and configuration identity.
