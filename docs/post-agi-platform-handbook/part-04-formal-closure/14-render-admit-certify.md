# 14. ggen Renders, Lean Admits, mfact Certifies

Post-AGI systems are especially vulnerable to category collapse because one intelligence may generate code, proofs, tests, explanations, and deployment plans in the same session.

The ecosystem therefore assigns different jobs to different mechanisms:

\[
\boxed{ggen\ renders}
\]

\[
\boxed{Lean\ admits}
\]

\[
\boxed{mfact\ certifies}
\]

These statements describe roles, not brands.

## Rendering is construction

ggen transforms semantic inputs into concrete projections. The result may be deterministic and still be wrong with respect to a higher-level invariant.

Generation establishes provenance of manufacture, not truth.

## Formal admission is proof under a model

Lean can establish that formal propositions follow from encoded assumptions and definitions. This is stronger than prose review, but its scope remains explicit.

A theorem about a model is not automatically a theorem about the deployed world. The correspondence between model and exact runtime subject must itself be evidenced.

## Certification binds evidence

mfact occupies the evidentiary layer: certification should identify what proposition, artifact, subject, verifier, and evidence are being asserted.

A certificate is valuable because it makes a standing claim machine-checkable and transferable without requiring every consumer to repeat the original narrative reasoning.

## Separation prevents self-certification

A generative system should not be able to produce a candidate, produce a persuasive proof-like statement, label the result certified, and then grant itself authority.

The constitutional path requires independent type boundaries:

\[
Generate \rightarrow Admit \rightarrow Execute \rightarrow Certify \rightarrow Standing
\]

Depending on the domain, some steps may be composed mechanically, but their meanings do not collapse.

## Formal methods become more valuable after AGI

When source generation is cheap, the bottleneck shifts toward knowing whether generated artifacts preserve required invariants.

Formalization is therefore not a reaction against AI generation. It is a complement to abundance. The more candidates intelligence can construct, the more valuable mechanical exclusion becomes.

## The limit of proof

No proof system eliminates observation. Hardware fails, credentials expire, cloud APIs change, network partitions occur, and exact deployment subjects diverge from models.

Formal closure therefore composes with experimental and operational closure rather than replacing them.

## Falsifier

A pipeline violates this chapter if the same untrusted model output can define the invariant, produce the candidate, declare the proof successful, and actuate the result without independent admission boundaries.

## Operational exercise

Take one important invariant currently expressed only in a test or review checklist. Decide whether it belongs in ontology constraints, a Lean theorem, runtime verification, or all three. Record exactly what each layer proves and what it does not prove.