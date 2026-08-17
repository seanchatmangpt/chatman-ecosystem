# 11. SELECT, CONSTRUCT, and DO

The most important execution distinction in the ecosystem is not “human versus AI.” It is:

\[
SELECT \neq CONSTRUCT \neq DO
\]

A post-AGI intelligence may dominate humans at selection and construction while still possessing no ambient authority to cause consequence.

## SELECT

SELECT chooses a candidate, objective, route, tool, target, or plan from an admissible possibility space.

Examples:

- choose a database topology;
- choose a repository migration sequence;
- choose a test set;
- choose a cloud region;
- choose a remediation candidate.

Selection changes the plan, not necessarily the world.

## CONSTRUCT

CONSTRUCT manufactures reversible artifacts that make a selected possibility concrete enough to inspect, prove, simulate, or execute later.

Examples include plans, code, manifests, proofs, synthetic worlds, receipts-in-waiting, API projections, migration bundles, and workflow intents.

Construction should be broad because it is where intelligence creates information without yet imposing consequence.

## DO

DO crosses the side-effect boundary.

It may push a ref, merge a PR, deploy a workload, alter cloud state, send a message, spend money, change access, delete data, approve a transaction, move a physical actuator, or alter any external state with consequences.

DO is narrow by design.

## Hooks manufacture intents

A hook observes an event and can construct a proposed next action. It does not receive authority merely because it was triggered automatically.

\[
Hook(event) \rightarrow Intent
\]

not:

\[
Hook(event) \rightarrow DO
\]

The intent still crosses operational admission and the authority broker.

## No ambient execution authority

The following objects have no inherent DO authority:

- raw input;
- model output;
- planner output;
- a graph query;
- generated code;
- a theorem;
- a proof artifact;
- an MCP tool call request;
- an A2A message;
- a CI workflow definition;
- a semantic derivation;
- a credential merely present in the environment.

Authority is an explicit relationship, not a side effect of capability.

## Why this scales

A common fear about post-AGI systems is that increasing intelligence necessarily increases uncontrolled power. This architecture decouples them.

Intelligence can expand the CONSTRUCT surface dramatically. The DO surface can remain smaller, typed, rate-bounded, subject-bounded, and receipted.

The design target is therefore:

> **Maximum reversible intelligence; minimum ambient consequence.**

## Falsifier

If any path allows a constructed artifact or generated intent to produce external consequence without passing the declared DO admission boundary, the system violates the separation.

## Operational exercise

Draw the path for one automated deployment. Mark every SELECT, CONSTRUCT, and DO transition. Any step that is both “construct” and “actuate” without an explicit boundary is a candidate for factorization.