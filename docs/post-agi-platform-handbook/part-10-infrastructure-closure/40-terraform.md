# 40. Terraform Is a Target

Terraform and compatible infrastructure-as-code ecosystems are valuable because they provide a large provider graph and a plan/apply separation that already approximates part of the ecosystem's constitutional factorization.

The mapping is instructive:

\[
Plan \approx CONSTRUCT
\]

\[
Apply \approx DO
\]

The approximation is not identity. The Chatman calculus adds exact-subject admission, independent authority, receipts, and broader semantic projections.

## Provider graphs are implementation knowledge

Terraform providers expose resource schemas and actions across a large range of services. That makes them useful capability donors for ggen and AutoFDE.

The provider schema should not become the canonical ontology by default. It is evidence about what the substrate can do.

## Plan as reversible construction

A plan allows the system to inspect intended differences before consequence. This fits DfCM well.

Post-AGI systems can manufacture many plans, evaluate policy and cost, run synthetic experiments, and select among them before any apply.

## Apply requires BRCE

A valid plan does not grant permission to apply it.

The DO transition must bind the exact plan identity, target state, authority, policy, and expected postconditions. After apply, observed provider state closes the loop.

## State files are not world truth

Terraform state is useful implementation state. It is not automatically the complete operational world.

External changes, provider behavior, and objects outside Terraform remain possible. The state becomes one admitted observation source among others.

## Reconstitution beyond HCL

A ggen-native system should be able to regenerate HCL or another Terraform-compatible projection from semantic sources. Handwritten HCL that contains irrecoverable business meaning is reconstitution debt.

## Falsifier

A Terraform-centered platform violates the target principle if changing the infrastructure engine requires redefining the business capability rather than changing its projection.

## Operational exercise

Take one Terraform module and identify which fields are provider mechanics and which are organization semantics. Lift the latter into ontology, then construct the module as a target projection.