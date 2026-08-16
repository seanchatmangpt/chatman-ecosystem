# 77. Standard Work Extraction: From Repeated Human Fix to ggen Pack

The most expensive repeated software task is often not computationally difficult. It is a solved local pattern that has not yet been converted into manufacturing law.

## 77.1 Repetition is evidence

Suppose similar repair \(a\) appears in repositories \(r_1,\ldots,r_k\). Repetition suggests a latent invariant:

\[
\exists P\;\forall r_i:\;P(r_i)\Rightarrow a(r_i).
\]

The objective is to discover \(P\), not become faster at manually applying \(a\).

## 77.2 Standard-work extraction pipeline

The canonical pipeline is

\[
\text{observe repetitions}
\rightarrow
\text{infer common semantic precondition}
\rightarrow
\text{encode ontology/policy}
\rightarrow
\text{manufacture pack}
\rightarrow
\text{qualify}
\rightarrow
\text{deploy across eligible subjects}.
\]

Each stage preserves the distinction between description and authority.

## 77.3 What belongs in a pack

A mature ggen pack can carry:

- canonical RDF or ontology requirements;
- SPARQL/query logic;
- templates/projections;
- schemas;
- SHACL or equivalent gates;
- fixtures;
- refusal cases;
- qualification commands;
- provenance;
- version constraints;
- consumer-side scaffold rules;
- generated-output verification.

The pack is therefore closer to a manufacturing cell definition than a snippet library.

## 77.4 Standard work must be executable

Documentation saying “all repositories should configure X this way” is weak standardization. Strong standard work has an executable admission test:

\[
subject\models P
\Rightarrow
manufacture(subject,pack)
\Rightarrow
verify(subject').
\]

If a consumer deviates, the deviation becomes a typed failure rather than tribal knowledge.

## 77.5 Poka-yoke through generation

Once a defect class is represented in the pack, future consumers should find the invalid configuration unreachable or immediately refused.

This converts

\[
\text{knowledge in operator memory}
\]

into

\[
\text{law in the production system}.
\]

## 77.6 Pack economics

Let manual repair cost per occurrence be \(h\), pack extraction cost be \(g\), and expected future occurrences \(n\). Extraction is economically justified when

\[
g<n\cdot h
\]

before accounting for defect prevention and lead-time reduction. In a large portfolio, \(n\) can be large, so the break-even point arrives quickly.

## 77.7 Standard work is versioned, not eternal

A pack encodes the best admitted method under current evidence. It can be superseded. The ecosystem therefore preserves pack identity and qualification receipts rather than pretending the current implementation is timeless.

## 77.8 Detecting extraction candidates

Process intelligence can mine repeated event traces. Define pattern frequency \(f(p)\), human touch cost \(h(p)\), defect association \(d(p)\), and portfolio applicability \(a(p)\). Rank extraction candidates by

\[
Score(p)=f(p)\cdot h(p)\cdot d(p)\cdot a(p).
\]

The highest-scoring patterns are where kaizen should attack first.

## 77.9 Definition of done

A repeated human task is not eliminated when a script exists. It is eliminated when:

1. the semantic precondition is explicit;
2. eligible subjects can be discovered;
3. manufacture is deterministic;
4. invalid subjects are refused;
5. outputs are independently verified;
6. provenance is receipted;
7. consumers no longer require the operator to remember the rule.

That is standard work at ecosystem scale.