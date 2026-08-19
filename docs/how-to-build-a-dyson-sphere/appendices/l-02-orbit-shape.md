# Appendix L.2 — Orbit Shape

**Parent:** [Appendix L — Example SHACL Shapes](l-example-shacl-shapes.md)

Orbital state is not a location label; it is a dynamical state with uncertainty. In the two-body approximation, orbital period satisfies T²=4π²a³/μ, where a is semimajor axis and μ is the standard gravitational parameter. Operational designs must then add perturbations, multi-body effects, solar radiation pressure, station-keeping budgets, conjunction probability, and covariance growth.

The semantic layer exists to prevent identical reality from fragmenting into incompatible local names. Public vocabularies are preferred where they already express provenance, units, sensors, organizations, policy, preservation, and events. Custom terms are admitted only for genuinely new stellar-industrial meaning. Generated APIs, documents, schemas, simulations, and dashboards are projections over that graph rather than rival semantic authorities.

## Reference relation

\[T^2 = \frac{4\pi^2 a^3}{\mu}\]

## SHACL pattern

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <https://example.invalid/dyson/> .

ex:ExampleShape a sh:NodeShape ;
  sh:targetClass ex:Example ;
  sh:closed false .
```

The example is intentionally incomplete. Production shapes must bind to the canonical ontology and include the actual constraints required by the subject.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.
