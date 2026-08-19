# 5.6 Solar Wind

**Parent:** [5. Stellar Observation](05-stellar-observation.md)

## Claim

`Solar Wind` is not accepted as a label-only capability. In this book it denotes a bounded object, relation, constraint, measurement, or control concern whose role must be explicit in the larger stellar observation system. The objective is to preserve useful design freedom while refusing transformations that hide physics, authority, or evidence.

Stellar power is the dominant external input. For an approximately isotropic star of luminosity L, irradiance at radius r is F=L/(4πr²). This inverse-square relation turns orbital radius into an energy-density and thermal-design parameter. For the Sun, total luminosity is about 3.8×10^26 W; a civilization need not capture all of it for the industrial consequences to be enormous.

Observation becomes operational only after it is bounded. O* records exact subject identity, source provenance, units, uncertainty, validity interval, contradictions, and exclusions. UNKNOWN is preserved as a value rather than coerced into a guess. This makes later manufacture falsifiable: a design can be traced back to the measurements and assumptions it actually consumed.

## Model

\[F(r)=\frac{L}{4\pi r^2}\]

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

For `Solar Wind`, **inspection is not execution** and **simulation is not deployment**. A claim advances only as far as the strongest evidence actually observed. A stale ephemeris, synthetic telemetry stream, generated file, theorem about a simplified model, or successful API response cannot be silently promoted into evidence for the physical subject.

## Falsifier

The working claim for `Solar Wind` is falsified when the admitted subject violates a required physical invariant, the postcondition cannot be observed, the authority chain cannot be reconstructed, or replay produces a materially different result under the same subject and configuration identity.
