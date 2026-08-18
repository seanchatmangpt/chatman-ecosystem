# Appendix B — Public Ontology Registry

The default rule is to reuse stable public semantics before inventing custom terms.

| Vocabulary | Primary use in the ecosystem |
|---|---|
| PROV-O | entities, activities, agents, derivation, provenance |
| DCAT | catalogs, datasets, distributions, data services |
| DCTERMS | titles, identifiers, temporal and resource metadata |
| SKOS | controlled concepts, schemes, broader/narrower relationships |
| SHACL | semantic graph constraints and validation |
| ODRL | permissions, prohibitions, duties, policy expressions |
| FOAF | basic people/agent relationships where adequate |
| QUDT | quantities, units, dimensions, numeric semantics |
| SOSA/SSN | observations, sensors, actuators, samples, features of interest |
| FIBO | financial semantics where the domain requires them |
| OCEL 2.0 | object-centric event/process history |

## Extension rule

A custom term is justified when:

1. no public term has the required semantics;
2. the distinction materially affects admission, manufacture, authority, evidence, or class identity; and
3. the custom term is linked to related public semantics where possible.

A custom namespace should not reproduce a public ontology merely to make local naming more convenient.

## Public does not mean automatically trusted

Public ontology provides shared meaning. It does not grant standing to observations or authority to operations. Version identity and local admission policy still apply.