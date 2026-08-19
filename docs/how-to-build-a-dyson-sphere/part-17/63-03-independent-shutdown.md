# 63.3 Independent Shutdown

**Parent:** [63. No Single Point of Existential Failure](63-no-single-point-of-existential-failure.md)

## Claim

`Independent Shutdown` is not accepted as a label-only capability. In this book it denotes a bounded object, relation, constraint, measurement, or control concern whose role must be explicit in the larger no single point of existential failure system. The objective is to preserve useful design freedom while refusing transformations that hide physics, authority, or evidence.

SELECT, CONSTRUCT, and DO are separate authority classes. A planner may rank candidates; a constructor may render them; only a brokered authority path may cause consequence. BRCE enforces zero unreceipted actuation by binding intent, subject, authority, preconditions, execution result, postconditions, and replay metadata into a receipt.

Failure is modeled as topology rather than surprise. The design objective is to keep a local defect from becoming a global loss: isolate failure domains, preserve safe trajectories, maintain independent shutdown, keep repair paths, and record enough event history for reconstruction. A failed collector should reduce capacity, not invalidate the entire swarm.

Governance is treated as executable constraint, not ornamental prose. Rights, duties, jurisdictions, delegation, amendment, and appeals must be represented so that machines can determine what authority exists without manufacturing policy from ambiguity. Polycentric governance is favored because solar-system latency and heterogeneous communities make one synchronous sovereign control loop both brittle and unnecessary.

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

For `Independent Shutdown`, **inspection is not execution** and **simulation is not deployment**. A claim advances only as far as the strongest evidence actually observed. A stale ephemeris, synthetic telemetry stream, generated file, theorem about a simplified model, or successful API response cannot be silently promoted into evidence for the physical subject.

## Falsifier

The working claim for `Independent Shutdown` is falsified when the admitted subject violates a required physical invariant, the postcondition cannot be observed, the authority chain cannot be reconstructed, or replay produces a materially different result under the same subject and configuration identity.
