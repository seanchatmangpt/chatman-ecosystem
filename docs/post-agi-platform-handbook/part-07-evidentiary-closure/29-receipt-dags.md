# 29. Receipt DAGs and Evidence Graphs

A linear log answers “what messages were emitted in sequence?” A receipt DAG answers a richer question: “what evidence dependencies give this exact standing claim support?”

## Evidence composition

Let each receipt be a node whose identity is content-addressed and whose edges reference prerequisite receipts or exact artifacts.

\[
G_R = (R,E_R)
\]

A release receipt may depend on source, validation, formal admission, integration, publication, and exact-head CI receipts. A deployment receipt may add authority, actuation, and postcondition receipts.

The DAG makes the support structure explicit.

## Reuse without overclaiming

Evidence reuse is lawful when the identity assumptions match.

A validator receipt may be reusable across subjects if the validator, toolchain, configuration, and relevant environment identities are equivalent. The new subject still needs its own evidence where subject identity matters.

This is the distinction between `VERIFIER_ALIVE` and `SUBJECT_ALIVE`.

## Falsification becomes local

When a dependency changes or is invalidated, the DAG shows which standing claims depend on it.

A compromised toolchain receipt should not force the system to distrust unrelated branches of evidence. The invalidation propagates only through reachable claims.

That makes failure topology explicit.

## Evidence graph and semantic graph

The semantic graph says what objects and relationships mean. The evidence graph says what observations and verifications support claims about those objects.

They should be linked but not collapsed.

A semantic relation such as `service depends_on database` can have one or more evidence paths that justify its current admission.

## Civilization-scale evidence

Once evidence is machine-composable, solved classes can carry transferable standing. A future intelligence can inspect not just a template but the evidence history that established why the template belongs to a closed class.

This is a prerequisite for trustworthy civilization memory.

## Falsifier

A receipt DAG fails if a parent can change without changing the child's verifiable dependency identity, or if the graph cannot distinguish reused verifier evidence from subject-specific execution evidence.

## Operational exercise

Represent one release as a receipt DAG. Start with the crown claim and walk backward until every leaf is either a directly observed fact, a trusted root, or an explicit unresolved assumption.