# From Operator Push to Pull System

The software factory is not complete while a human must remember which repository to inspect next, infer which branch contains the useful work, decide which failure matters most, and manually push the next task into the system.

The next architectural transition is from **operator-pushed work** to **graph-pulled work**.

## Push scheduling

A push system looks like this:

```text
human remembers problem
    -> chooses repository
    -> opens branch/PR
    -> discovers dependency
    -> context-switches
    -> starts more work
    -> periodically returns to old WIP
```

This can achieve enormous local throughput while increasing global WIP. The danger is that generated work arrives faster than closure capacity.

## Pull scheduling

A pull system begins from admitted state:

```text
release graph + WIP graph + dependency graph + evidence graph
    -> identify enabled closure frontiers
    -> rank reversible work by impact
    -> admit bounded WIP
    -> execute narrow closure
    -> receipt consequence
    -> update graph
    -> pull next enabled work
```

The difference is not merely automation. **Demand and dependency state select the next lawful work.**

## Little’s Law as a control surface

The classical relationship is:

\[
L=\lambda W
\]

where \(L\) is work in process, \(\lambda\) is closure throughput, and \(W\) is average cycle time under steady-state assumptions.

A real repository portfolio is often not steady state, so the system should not manufacture false precision. It can still measure observed WIP, observed closure events, completed cycle times, and the projection \(L/\lambda\) while labeling the assumptions explicitly.

The management implication remains strong: if work arrival grows faster than closure throughput, cycle time expands. More agents can make this worse when they open more fronts than the system can close.

## Logical WIP, not UI-object WIP

One piece of real work can appear simultaneously as a branch, PR, issue, CI run, source TODO, dependency blocker, documentation gap, and release obligation. Counting each independently inflates WIP and obscures causality.

The control plane should therefore collapse projections into **logical WIP objects** with relationships such as:

- blocks / blocked-by;
- implements / implemented-by;
- duplicates;
- supersedes;
- generated projection of;
- evidence for;
- required by release role;
- consumer dependency;
- closure intent.

This is why graph storage and object-centric process evidence fit the problem naturally.

## ERRC as executable WIP policy

ERRC becomes useful when it is applied to the closure frontier rather than used as a brainstorming acronym.

### ELIMINATE

Remove WIP that has no remaining lawful value: orphaned branches, duplicate implementations, obsolete experiments, dead generated projections, stale copied artifacts, or work superseded by a canonical mechanism.

### REDUCE

Shrink the effort required to close valid WIP: delete unnecessary code, narrow the verifier, reduce duplicated tests, compress repeated configuration into a pack, or replace manual review steps with mechanical admission.

### RAISE

Increase the quality of closure-enabling infrastructure where it is the bottleneck: dependency closure, CI determinism, receipt integrity, cross-repo identity, replay, observability, or semantic admission.

### CREATE

Creation is lawful only when it closes an admitted gap. Examples include a missing integration court, receipt schema, transition adapter, generator, release evidence artifact, or automation that retires recurring manual work.

That restriction is essential. Otherwise “CREATE” becomes permission to generate infinite speculative scope.

## WIP limits for generated systems

An LLM or generator can create code much faster than an organization can verify, integrate, deploy, observe, and retire it. Therefore the important WIP limit is not “how many tokens can run concurrently?” It is the number of **open consequential or verification obligations** the downstream system can close safely.

A mature factory should enforce WIP ceilings at multiple layers:

- per logical worker;
- per repository;
- per release role;
- per dependency component;
- per actuation boundary;
- per human review/authority boundary when one remains necessary.

Exceeding a WIP limit should produce a typed refusal, not a hidden queue.

## Pull-system algorithm

A defensible local scheduler can be written as:

1. observe exact repository/ref/SHA and workflow state;
2. admit logical WIP objects and collapse duplicates;
3. construct the full reversible closure frontier;
4. compute downstream dependency impact;
5. exclude work that lacks authority, exact identity, or an admissible verifier;
6. respect WIP ceilings;
7. select the highest-impact enabled closure intent;
8. execute through the owning boundary;
9. verify the consequence independently;
10. record receipt and replay handle;
11. update standing and dependency graph;
12. repeat until the admitted frontier is empty.

The scheduler itself must remain powerless with respect to consequential DO. It can manufacture intents; the owner of the DO boundary still admits or refuses execution.

## The metric transition

A human-operated coding system tends to optimize visible activity: commits, changed files, open PRs, tokens, or tasks completed. Those can be useful diagnostics, but a pull system should prioritize measures of **flow and closure**:

\[
\boxed{
\begin{aligned}
&\text{closure throughput} \uparrow \\
&\text{cycle time} \downarrow \\
&\text{logical WIP} \downarrow \\
&\text{escaped defect classes} \downarrow \\
&\text{operator touches per closure} \downarrow \\
&\text{replayable receipts per consequential transition} \rightarrow 1
\end{aligned}}
\]

The phase transition occurs when the operator no longer has to schedule normal work. The operator becomes a source of genuinely new observation, constitutional change, or explicitly reserved authority—not the dispatcher for every routine closure.
