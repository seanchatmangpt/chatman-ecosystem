# 4. Formal Definition of the Chatman Equation

> **Program relation.** This chapter is part of the Chateco doctoral program. It preserves the native research object before mapping it into the constitutional manufacturing calculus. The preserved source anchor for this chapter is **3. Formal Definition of the Chatman Equation** from the doctoral thesis corpus. It is evidence-bearing source material for the chapter, not an assertion that the chapter title and source heading are definitionally equivalent.

## Research claim

**Formal Definition of the Chatman Equation** is treated here as a law-state problem rather than a slogan. The chapter asks which observations are admissible, which transformations are lawful, what authority is required for consequence, which receipts establish standing, and what replay or transfer would be required to keep that standing over time. The Chateco position is deliberately bounded: adjacency is not equivalence, execution is not proof, and absence of evidence does not become refusal by narration.

## Preserved source development

### 3.1 Core objects

Let \\(\\mathcal O\\) be a space of observations, \\(\\mathcal B\\) a family of declared boundaries, \\(\\mathcal A\\) a space of artifacts or consequences, and \\(\\mathcal R\\) a space of receipts. Raw observation \\(O\\in\\mathcal O\\) is partial, possibly stale, agent-relative, and not yet authorized for use.

An admission operator is a partial map or relation

\\\[ \\alpha_b : \\mathcal O \\rightharpoonup \\mathcal O\^\*\_b + \\mathcal F, \\\]

where \\(b\\in\\mathcal B\\), \\(\\mathcal O\^\*\_b\\) is observation admitted within boundary \\(b\\), and \\(\\mathcal F\\) is a typed refusal space. Admission may refuse, classify the operation as unsupported, preserve the result as unknown, or return a repairable defect.

A manufacturing morphism is

\\\[ \\mu\_{b,l} : \\mathcal O\^\*\_b \\rightharpoonup \\mathcal A + \\mathcal F, \\\]

parameterized by boundary \\(b\\) and law \\(l\\). It may denote a function, relation, planner, proof constructor, concurrent semantics, supervised process, organizational procedure, or physical action.

The core equation is

\\\[ A=\\mu(O\^\*). \\\]

The equation asserts neither totality nor determinism. It states that a consequence with standing is manufactured from admitted observation under recoverable law.

### 3.2 Receipt

A receipt law is

\\\[ \\rho : (O\^\*, l, A, e) \\mapsto R, \\\]

where \\(e\\) contains the relevant execution, authority, provenance, identity, and boundary evidence. The short form is

\\\[ R=\\operatorname{receipt}(A). \\\]

A receipt is adequate relative to a verifier \\(V\\) when \\(V(R,A,b)\\) can distinguish the claimed artifact and boundary from relevant alternatives. Cryptographic integrity is one implementation; institutional testimony, kernel admission, validation reports, event traces, and physical reconciliation are others.

### 3.3 Replay

Replay is a relation

\\\[ \\operatorname{replay}(O\^\*,l,R) \\Downarrow \\widehat A. \\\]

The verification condition is not always byte equality. It is the equivalence appropriate to the domain:

\\\[ \\widehat A \\equiv_b A. \\\]

For a generated file, this may be byte equality. For a concurrent workflow, it may be trace-language equivalence. For a theorem, it is kernel acceptance. For an organization, it may be satisfaction of declared capabilities and evidence predicates.

### 3.4 Expanded law-state chain

The operational calculus is:

\\\[ O \\xrightarrow{parse} O_p \\xrightarrow{route} O_r \\xrightarrow{admit/refuse} O\^\* \\xrightarrow{diagnose/repair} C \\xrightarrow{plan} I \\xrightarrow{authorize} I_a \\xrightarrow{actuate} A \\xrightarrow{receipt} R \\xrightarrow{replay} \\widehat A. \\\]

The chain is not a mandatory microservice architecture. It is a set of distinctions. Adjacent stages may share an implementation, but a system must not collapse a distinction that changes semantics, authority, or recognition.

### 3.5 Composition

If \\(A_n\\) has a receipt adequate for the next boundary, it may enter the next observation:

\\\[ A_n,R_n \\subseteq O\_{n+1}. \\\]

This yields Gall-style recursion:

\\\[ (O_n\^\*,\\mu_n)\\mapsto(A_n,R_n)\\mapsto O\_{n+1}\^\*. \\\]

Composition requires preservation of identity, boundary, and receipt. An artifact cannot silently change meaning when projected into the next slice.

### 3.6 Universal-completeness criterion

A candidate counterexample must provide a consequence recognized by the native domain while preserving the domain's objects and recognition conditions, yet demonstrate that no equivalent observation, admission, transformation, artifact, or receipt relation exists. Hiding admission inside the transformation, naming a transformation emergence, or removing the receipt and therefore removing standing does not satisfy the criterion.

## Chateco operationalization

For this research object, the relevant Chateco surfaces are **mfact/procint, Lean 4 admission, proof-carrying projection**. They are not interchangeable. The composition root names identity and relationships; owning repositories provide implementation behavior; formal rails prove only propositions encoded inside their own logic; runtime rails establish only behavior actually executed; and receipts bind those observations to the exact subject. A defensible implementation therefore preserves the correspondence

\[
\text{graph} \rightarrow \text{query} \rightarrow \text{ggen} \rightarrow \text{formal admission} \rightarrow \text{runtime} \rightarrow \text{BRCE} \rightarrow \text{receipt} \rightarrow \text{replay}.
\]

Any skipped edge must be reported as `UNKNOWN`, `BLOCKED`, `UNSUPPORTED`, or a typed refusal rather than silently inferred. The operational target is not maximal execution. It is maximal *reversible lawful construction* followed by the narrowest authorized consequential transition.

## Exclusions

This chapter does **not** infer universal truth from one implementation, formal correctness from compilation, production authority from credentials, successful execution from workflow existence, or class closure from one solved instance. It does not treat a public ontology as automatically legitimate, a proof kernel as a sensor of external reality, or a receipt-shaped record as sufficient when exact identity and consequence are missing.

## Falsifier

A refutation must preserve the same native objects and recognition boundary. The chapter is falsified if a competing system can obtain the same recognized standing while no equivalent admission boundary, lawful transformation, authority condition, consequential actuation boundary, or receipt/replay relation can be recovered. A merely adjacent mechanism, renamed vocabulary, or different definition of success is evidence of another design, not yet a refutation.

## Research receipt

Advancement beyond conceptual standing requires an exact subject SHA or digest, admitted inputs, the verifier and toolchain identity, the command or protocol actually executed, exit/result evidence, negative fixtures where applicable, persisted receipt material, and deterministic or semantically equivalent replay. Until those obligations are satisfied for the exact subject, the correct status remains bounded rather than crowned.
