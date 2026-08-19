# 34.2 Partitioned Authority

**Parent:** [34. Byzantine Failure](34-byzantine-failure.md)

## Claim

`Partitioned Authority` is not accepted as a label-only capability. In this book it denotes a bounded object, relation, constraint, measurement, or control concern whose role must be explicit in the larger byzantine failure system. The objective is to preserve useful design freedom while refusing transformations that hide physics, authority, or evidence.

Stellar power is the dominant external input. For an approximately isotropic star of luminosity L, irradiance at radius r is F=L/(4πr²). This inverse-square relation turns orbital radius into an energy-density and thermal-design parameter. For the Sun, total luminosity is about 3.8×10^26 W; a civilization need not capture all of it for the industrial consequences to be enormous.

Stellar scale eliminates the plausibility of a trusted interior. Identity, software provenance, key state, policy, and telemetry can all be stale or compromised. CASTLE therefore treats authority as explicit reachability under least privilege, uses content identity and signed evidence where appropriate, partitions failure domains, and never infers permission from network position or possession of a credential.

SELECT, CONSTRUCT, and DO are separate authority classes. A planner may rank candidates; a constructor may render them; only a brokered authority path may cause consequence. BRCE enforces zero unreceipted actuation by binding intent, subject, authority, preconditions, execution result, postconditions, and replay metadata into a receipt.

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

For `Partitioned Authority`, **inspection is not execution** and **simulation is not deployment**. A claim advances only as far as the strongest evidence actually observed. A stale ephemeris, synthetic telemetry stream, generated file, theorem about a simplified model, or successful API response cannot be silently promoted into evidence for the physical subject.

## Falsifier

The working claim for `Partitioned Authority` is falsified when the admitted subject violates a required physical invariant, the postcondition cannot be observed, the authority chain cannot be reconstructed, or replay produces a materially different result under the same subject and configuration identity.
