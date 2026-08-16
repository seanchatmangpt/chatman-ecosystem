# 75. Jidoka, Andon, and Poka-Yoke for Autonomous Software Manufacture

Autonomy without abnormality handling is merely unattended execution. TPS makes the opposite move: automation becomes trustworthy when the machine can detect abnormal conditions, stop, expose them, and prevent defective continuation.

## 75.1 Jidoka state machine

For production transition \(x\), define

\[
EXECUTE(x)
\rightarrow
VERIFY(x)
\rightarrow
\begin{cases}
RECEIPT(x), & postconditions\ hold\\
STOP(x,e), & abnormality\ e
\end{cases}
\]

No later stage may reinterpret \(STOP\) as success without new evidence.

## 75.2 Andon as typed abnormality

An andon event is not a red dashboard light. It is a machine-readable abnormality object:

\[
E=(subject,stage,type,evidence,impact,next\_safe\_actions).
\]

Examples include:

- exact-head drift;
- dependency identity missing;
- verifier contradiction;
- generated projection mismatch;
- provider timeout after uncertain consequence;
- missing receipt;
- authority refusal;
- replay divergence.

The event must preserve enough evidence to reproduce the stop.

## 75.3 Stop-the-line semantics

“Stop the line” should be scoped. If a failure affects only one independent morphism, DfCM forbids collapsing the entire possibility graph unnecessarily.

Let \(Impact(e)\subseteq G\) be the transitive set whose standing depends on the failed edge. Then

\[
STOP(e)=freeze(Impact(e)),
\]

not

\[
freeze(G)
\]

unless the failure invalidates a constitutional root.

## 75.4 Automatic local repair

Jidoka does not imply that every abnormality immediately pages a human. The system should first attempt bounded repairs whose reversibility and authority are already admitted:

\[
E
\rightarrow
Candidates(E)
\rightarrow
admit
\rightarrow
repair
\rightarrow
reverify.
\]

Human escalation occurs when the local closure frontier is empty or when policy requires human authority.

## 75.5 Poka-yoke

Poka-yoke makes the wrong operation impossible or immediately detectable. In software manufacture this includes:

- schemas that cannot express ambiguous authority;
- generators that require exact subjects;
- CI that verifies generated outputs against canonical sources;
- branch protections;
- typed refusal enums rather than free-text failure;
- action workflows pinned to exact immutable identities;
- receipt requirements at consequential boundaries;
- ggen packs that encode a solved configuration seam.

The strongest repair is the one that removes the defect class from the reachable state space.

## 75.6 Defect escape rate

Define

\[
\delta=\frac{\text{defects discovered after standing promotion}}{\text{promoted transitions}}.
\]

A maturing jidoka system should reduce \(\delta\) even as throughput rises.

Also track detection latency

\[
T_d=t_{detect}-t_{introduction}
\]

and containment radius

\[
R_c=|Impact(e)|.
\]

Better architecture drives both downward.

## 75.7 Uncertain consequence

The hardest case is an actuator exception after the external world may already have changed. Blind retry can duplicate a consequence.

Therefore

\[
exception\ after\ DO
\not\Rightarrow
retry.
\]

Instead the system enters an uncertainty state, independently observes postconditions, reconciles receipts, and only then selects the next lawful action.

## 75.8 Learning from andon history

Andon events are process data. Aggregate them by defect class, production stage, dependency, root cause, and repair pattern. The next improvement target is often the class with highest product

\[
frequency\times impact\times human\ intervention\ cost.
\]

Then encode the repair as standard work or poka-yoke.

## 75.9 Autonomy criterion

An autonomous factory is not one that never stops. It is one in which stops are precise, local, reproducible, and increasingly self-closing.

The desired trajectory is

\[
\text{throughput}\uparrow,
\quad
\delta\downarrow,
\quad
T_d\downarrow,
\quad
R_c\downarrow,
\quad
human\ escalations\downarrow.
\]

That is software jidoka at machine scale.