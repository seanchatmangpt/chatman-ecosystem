# 50. Goal-First Cyber Defense

Defensive engineering often organizes work around known vulnerabilities and signatures. Those remain useful observations, but they are downstream of a more general question:

> What forbidden goals must remain unreachable?

## Model prohibited states

A defender can express security objectives as non-reachability constraints over the system graph.

Examples include states in which an untrusted principal gains unauthorized authority, sensitive data crosses a prohibited boundary, evidence can be erased without receipt, or a critical control plane can be changed outside the broker.

\[
Reach(untrusted, forbidden)=false
\]

This is a defensive property, not an exploit recipe.

## Vulnerabilities become paths

A vulnerability matters because it can create or shorten a path to an unacceptable state.

Thinking in paths lets the system reason about classes of failures rather than only named exploits.

A single control can block many paths. Conversely, patching one implementation detail may leave the forbidden goal reachable through another edge.

## Machine-speed defense needs machine-speed reconstruction

Human patch cycles are poorly matched to environments in which automated systems can discover and exercise new paths rapidly.

The stronger architecture removes ambient authority, keeps projections reconstitutable, and makes defensive topology machine-queryable.

When a boundary changes, ggen can manufacture corrected projections across interfaces and substrates while receipts preserve what changed.

## GymAct for defensive experimentation

Synthetic worlds allow the system to test whether forbidden goals remain unreachable under varied configurations and fault conditions.

The gym can expose complete modeled state for upper-bound reasoning and restricted state for realistic observation tests.

## Defense before patch

The fastest lawful response may be to remove reachability by narrowing authority, isolating a component, disabling a capability, or changing routing before the underlying implementation defect is fully repaired.

This separates immediate containment from durable class closure.

## Falsifier

A goal-first defense is incomplete if the prohibited state is defined so vaguely that the system cannot determine whether a candidate topology permits reachability.

## Operational exercise

Choose one critical asset and define three forbidden states using identities and authority relationships. Then identify multiple independent controls that make those states unreachable, rather than beginning with a list of exploits.