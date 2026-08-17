# 21. BRCE: Bounded Receipted Controlled Execution

BRCE is the exclusive DO path of the ecosystem.

Its constitutional statement is simple:

> **Zero unreceipted actuation.**

The difficulty is implementing that sentence without allowing side channels in which “helpful” automation bypasses the boundary.

## Bounded

Every actuation names an exact admitted subject and a bounded consequence.

A permission to update one deployment is not permission to update a namespace. Permission to write a branch is not permission to merge it. Permission to draft a message is not permission to send it.

Scope widening requires a new admission decision.

## Receipted

The actuation emits evidence sufficient to identify what was attempted, under which authority, against which subject, in which environment, with what result and postcondition.

The receipt is part of the operation, not optional observability added later.

## Controlled

The authority broker evaluates whether the requested transition is lawful. Capability possession, credentials, tool availability, or model confidence do not substitute for authority.

## Execution

BRCE is where proposed consequence becomes actual consequence.

That makes it intentionally narrower than SELECT and CONSTRUCT. A post-AGI system should be able to generate vast numbers of candidate worlds while forcing every real-world mutation through a small auditable kernel.

## The BRCE transition

A conceptual transition is:

\[
Intent + O^* + Authority + Policy \rightarrow Admit_{DO} \rightarrow Execute \rightarrow Verify \rightarrow Receipt
\]

Failure at any stage preserves the distinction between attempted and completed action.

## Postconditions matter

An API returning success is not enough. The operation's declared consequence must be observed when practical.

A deployment receipt may need to bind the resulting image digest and workload identity. A Git publication receipt may need the new exact head SHA. A message send may need the provider's message identity. A cloud mutation may need observed resource state.

## BRCE is substrate-independent

The same law applies to GitHub, Kubernetes, cloud APIs, email, financial systems, factory actuators, robots, or future interfaces.

The adapter changes. The authority and receipt semantics do not.

## Falsifier

Any consequential adapter capable of mutating external state outside the brokered BRCE path is a constitutional bypass, even if the bypass is used only for convenience.

## Operational exercise

Inventory every place a platform can cause external mutation. For each, identify the BRCE entrypoint, exact-subject binding, authority decision, postcondition, and receipt. Unbrokered paths are explicit defects, not undocumented features.