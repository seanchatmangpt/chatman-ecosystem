# 64. Epistemic Standing, Evidence, and Non-Self-Certification

Autonomous systems fail epistemically when they confuse availability with truth, confidence with authority, or repeated assertion with evidence. The Chatman Ecosystem addresses this through typed admission and scoped standing.

## 64.1 Observation is not fact

Let \(o\in O\) be any observation: model output, API response, human statement, test log, repository metadata, sensor reading, or generated report. The constitutional rule is

\[
o\in O \not\Rightarrow o\in O^*.
\]

Admission is a judgment

\[
\alpha_e(o;K,\tau)\in O^*\sqcup F,
\]

parameterized by an evidence policy \(K\) and temporal context \(\tau\).

The same proposition may be admitted in one context and refused in another because its evidence is stale, insufficiently scoped, or derived from the wrong subject.

## 64.2 Standing is indexed

A statement such as “the build is green” is incomplete. The properly typed proposition is closer to

\[
Green(repo,sha,workflow,run,job,t).
\]

Similarly,

\[
ALIVE(subject,boundary,verifier,context,t).
\]

This indexed form prevents evidence laundering across revisions or boundaries.

## 64.3 Evidence lattice

Evidence need not be binary before admission. Let \(\mathcal E\) be a partially ordered set where

\[
e_1\preceq e_2
\]

means \(e_2\) satisfies at least the obligations satisfied by \(e_1\). A Definition of Done can then be represented as a required upper set or meet of obligations:

\[
DoD = e_{identity}\wedge e_{build}\wedge e_{tests}\wedge e_{replay}\wedge e_{policy}\wedge e_{transfer}.
\]

Different artifact classes induce different lattices. A documentation projection need not satisfy the same operational obligations as a production actuator.

## 64.4 Independent admission

A subsystem must not be allowed to generate both the claim and the only evidence that certifies that claim when stronger independent evidence is available.

This gives the non-self-certification principle:

\[
Producer(x)=Verifier(x)\quad\text{is insufficient for crown standing unless independently bounded.}
\]

The principle is not an absolute ban on self-tests. It is a requirement to distinguish local consistency from independent admission.

Examples:

- a compiler may type-check its output, but release standing may require a separate integration court;
- a planner may report success, but the environment receipt determines whether the state transition occurred;
- an LLM may explain a theorem, but a proof checker determines whether the proof term is admitted;
- a workflow may declare completion, but OCEL/replay evidence may determine whether required events actually occurred.

## 64.5 Evidence decay

Evidence has a validity domain. Let

\[
valid(e,s,b,[t_0,t_1])
\]

mean evidence \(e\) supports subject \(s\), boundary \(b\), during an interval. Evidence outside that domain cannot be silently reused.

This yields a simple anti-staleness law:

\[
sha_1\neq sha_2 \Rightarrow Green(sha_1)\not\Rightarrow Green(sha_2).
\]

Exact-head verification is therefore epistemic discipline, not CI ceremony.

## 64.6 Bayesian uncertainty versus constitutional admission

Probabilistic belief and operational admission answer different questions. A system may assign

\[
P(H\mid E)=0.999
\]

to a hypothesis while still refusing actuation because authority or evidence policy requires a deterministic gate. Conversely, a low-risk reversible construction may be admitted with weaker epistemic confidence because it has no consequential authority.

Thus probability does not collapse into permission:

\[
P(H\mid E)\not\Rightarrow Authorized(H).
\]

This separation is essential for AGI-scale systems, where sophisticated uncertainty estimation cannot substitute for governance.

## 64.7 Epistemic crown experiment

For any important claim, construct an evidence table containing:

| Field | Requirement |
|---|---|
| Subject | immutable identity |
| Claim | typed proposition |
| Evidence | source and digest |
| Verifier | independent court |
| Context | policy/capability/environment |
| Time | observation interval |
| Refusal | typed failure mode |
| Replay | reproduction procedure |
| Transfer | distinct-instance test when applicable |

A claim that cannot populate this table is not necessarily false. It is **not yet admitted at the requested standing**.