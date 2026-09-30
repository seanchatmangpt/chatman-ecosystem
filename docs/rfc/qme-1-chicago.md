# Expanded Chicago qualification

QME-1 uses Chicago as a qualification algebra, not merely a preference for integration tests.

## Qualification equation

`Q+ = ExactSubject ∩ Provenance ∩ CanonicalSemantics ∩ AuthorityBound ∩ ConsequenceBound ∩ IndependentObservation ∩ Receipt ∩ ReplaySafe ∩ Falsifiers ∩ Migration`.

The algebra is conjunctive. A missing term cannot be compensated by a stronger score elsewhere.

## Anti-vacuity

A negative court requires two independent observations:

`AttemptObserved = true`

and

`ViolationObserved = false`.

If the intended attack never reaches the load-bearing boundary, the court returns `VACUOUS_COURT`; a dead or disconnected system cannot prove safety.

## Exact-subject standing

Courts qualify an exact subject, evidence horizon and boundary. Standing does not transfer by similarity, version label or repository name.

## Hardening

A discovered failure is not complete when one test turns green. The desired transition is:

`stress -> counterexample -> minimal invariant -> reusable falsifier -> inherited qualification`.

This is architectural work-hardening: future capabilities inherit constraints that make the same deformation class harder to express. Local patches that do not generalize are incomplete hardening.

## Independent observation and time

For consequential DO, the actor's success response is not the postcondition. Process evidence MAY include OCEL or equivalent durable traces, but the observer must remain independent of the actuator's claim.

Temporal laws are part of the subject: authority before DO, preparation before consequence, reconciliation before retry after UNKNOWN outcome, and replay without duplicate consequence.

## Composition

Profiles inherit courts. A FIBO finance profile adds financial identity and amount/currency/settlement falsifiers while inheriting the QME core; it does not rewrite exact-subject, authority, replay, postcondition or anti-vacuity laws.
