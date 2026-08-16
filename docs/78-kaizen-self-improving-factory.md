# 78. Kaizen and the Self-Improving Factory

A self-improving software factory should improve the mechanism that produces software, not merely regenerate more artifacts with a stronger model. Kaizen supplies the continuous-improvement discipline; the Chatman constitution supplies the non-self-certification boundary that keeps recursive improvement from becoming recursive authority.

## 78.1 Two orders of production

First-order production manufactures product artifacts:

\[
\mu_1:O^*\rightarrow A.
\]

Second-order production modifies the manufacturer:

\[
\mu_2:Evidence(\mu_1)\rightarrow \Delta\mu_1.
\]

A genuine software factory must eventually operate at both orders.

## 78.2 Evidence source for improvement

Second-order proposals should derive from process evidence:

- recurring andon classes;
- WIP age;
- repeated human interventions;
- semantic-drift defects;
- slow verifiers;
- low-yield generation paths;
- high-cost dependency seams;
- dormant POC blockers;
- repeated release/manual coordination.

Improvement demand is therefore pulled from observed production loss.

## 78.3 Improvement candidate graph

DfCM applies to factory modifications too. For abnormality class \(e\), construct reversible candidate improvements

\[
C(e)=\{c_1,\ldots,c_n\}
\]

before selecting an irreversible architecture change.

Candidates may include elimination, standard-work extraction, policy change, additional verifier, dependency replacement, caching, parallelization, or authority refactoring.

## 78.4 Non-self-certification

A manufacturer may propose changes to itself, but cannot promote those changes solely because its own evaluation says they are better.

Require an independent court

\[
V_{independent}(\mu_1')
\]

before new standing is granted.

This is the recursive form of

\[
\boxed{\text{Generated}\neq\text{Authorized}}.
\]

## 78.5 Improvement objective

Define factory loss

\[
J=\alpha W+\beta H+\gamma D+\delta T+\epsilon C_w
\]

where \(W\) is WIP burden, \(H\) human interventions, \(D\) defect escape, \(T\) lead time, and \(C_w\) avoidable compute/coordination cost.

Kaizen seeks changes \(\Delta\mu\) such that

\[
J(\mu+\Delta\mu)<J(\mu)
\]

while constitutional invariants remain preserved.

## 78.6 Structural learning

The strongest learning loop is

\[
\text{abnormality}
\rightarrow
\text{root cause}
\rightarrow
\text{standard work/poka-yoke}
\rightarrow
\text{qualification}
\rightarrow
\text{fleet rollout}
\rightarrow
\text{new evidence}.
\]

This turns one defect into portfolio-wide prevention.

## 78.7 Autonomic control

The ecosystem can treat production health as a viability problem. Let \(K\) be the set of states satisfying constitutional and flow constraints. The controller seeks actions keeping

\[
x_t\in K
\]

under changing demand and capability.

When the system leaves the preferred operating region but remains constitutionally safe, ultrastable adaptation changes control policy rather than violating the constitution.

## 78.8 Improvement rate

Define kaizen leverage

\[
\kappa=\frac{\text{future human/defect work prevented}}{\text{improvement intervention}}.
\]

High \(\kappa\) means the factory is improving multiplicatively rather than merely consuming backlog.

## 78.9 Recursive improvement falsifier

If second-order automation increases unexplained standing changes, defect escape, or authority ambiguity, then recursive improvement is making the system less trustworthy. The correct response is to reduce the authority of \(\mu_2\), not to hide failures behind stronger generation.

The target is a factory that modifies itself quickly **because** its modification path is bounded and independently admitted, not despite those constraints.