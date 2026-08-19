# 75.3 Graceful Degradation

**Parent:** [75. Design for Failure](75-design-for-failure.md)

## Claim

`Graceful Degradation` is not accepted as a label-only capability. In this book it denotes a bounded object, relation, constraint, measurement, or control concern whose role must be explicit in the larger design for failure system. The objective is to preserve useful design freedom while refusing transformations that hide physics, authority, or evidence.

Failure is modeled as topology rather than surprise. The design objective is to keep a local defect from becoming a global loss: isolate failure domains, preserve safe trajectories, maintain independent shutdown, keep repair paths, and record enough event history for reconstruction. A failed collector should reduce capacity, not invalidate the entire swarm.

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

For `Graceful Degradation`, **inspection is not execution** and **simulation is not deployment**. A claim advances only as far as the strongest evidence actually observed. A stale ephemeris, synthetic telemetry stream, generated file, theorem about a simplified model, or successful API response cannot be silently promoted into evidence for the physical subject.

## Falsifier

The working claim for `Graceful Degradation` is falsified when the admitted subject violates a required physical invariant, the postcondition cannot be observed, the authority chain cannot be reconstructed, or replay produces a materially different result under the same subject and configuration identity.
