# 25.8 Radiator Factory

**Parent:** [25. Factory Templates](25-factory-templates.md)

## Claim

`Radiator Factory` is not accepted as a label-only capability. In this book it denotes a bounded object, relation, constraint, measurement, or control concern whose role must be explicit in the larger factory templates system. The objective is to preserve useful design freedom while refusing transformations that hide physics, authority, or evidence.

Every useful energy conversion ends as heat. A collector that absorbs stellar power must either radiate comparable power, export energy, store it temporarily, or fail thermally. Radiative disposal scales as P=εσAT⁴, making radiator area and operating temperature architectural variables. The T⁴ dependence rewards hotter radiators with compact area, but material limits, conversion efficiency, computation density, and component lifetime constrain that choice.

ggen is treated as a semantic manufacturing compiler: graph and query select meaning, templates render projections, validators reject malformed output, and receipts bind the generated artifact to the admitted subject. Generation is not evidence of correctness. The value of the generator is reproducibility and class closure—once a construction pattern is admitted, it can be regenerated for new subjects without rediscovering the pattern manually.

Factory design is a closure problem: feedstock, energy, tooling, calibration, control, spares, maintenance, waste, and output quality must all be represented. Self-replication is especially dangerous to leave implicit. Reproduction therefore consumes explicit material and energy budgets, generation limits, geographic or orbital fences, shutdown semantics, and receipts for each authorized replication transition.

## Model

\[P_{rad}=\varepsilon\sigma A T^4\]

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

For `Radiator Factory`, **inspection is not execution** and **simulation is not deployment**. A claim advances only as far as the strongest evidence actually observed. A stale ephemeris, synthetic telemetry stream, generated file, theorem about a simplified model, or successful API response cannot be silently promoted into evidence for the physical subject.

## Falsifier

The working claim for `Radiator Factory` is falsified when the admitted subject violates a required physical invariant, the postcondition cannot be observed, the authority chain cannot be reconstructed, or replay produces a materially different result under the same subject and configuration identity.
