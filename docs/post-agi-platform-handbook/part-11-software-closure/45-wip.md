# 45. WIP as a Topological Defect

In a software factory capable of machine-scale construction, unfinished work is not merely a project-management inconvenience. It is a graph of transitions that have begun but have not reached a standing boundary.

## Little's Law still applies

For a stable system:

\[
WIP = Throughput \times CycleTime
\]

Increasing generation throughput without closing work can increase WIP dramatically. A post-AGI system therefore needs a completion discipline at the portfolio level.

## WIP is observable topology

Repository activity, open branches, draft PRs, failing checks, TODO markers, partial release manifests, stale generated projections, incomplete migrations, and unsupported edges are evidence of unfinished transitions.

The WIP scanner should classify, not merely count.

A branch waiting for external authority is different from a branch with broken tests. A proof-of-concept deliberately preserved for future class discovery is different from an abandoned duplicate implementation.

## Finish before expanding when closure is cheap

DfCM preserves reversible possibilities, but Combinatorial Maximalism is bounded by cost and evidence. Keeping every incomplete branch forever is not maximalism; it is unpriced state accumulation.

The factory should close cheap, high-information work before spawning equivalent new paths.

## WIP can become a ggen class

Repeated unfinished patterns are themselves discoveries.

If repositories repeatedly lack the same CI, docs projection, ontology, release receipt, or interface surface, the fix should become a ggen pack rather than another manual repair.

\[
Repeated\ WIP \rightarrow Pattern \rightarrow Pack \rightarrow Class\ Closure
\]

## Commit count is not closure

High commit throughput can be evidence of manufacturing capacity, but it is not a crown metric by itself. Ten thousand commits that leave ten thousand unresolved transitions increase inventory.

The stronger metric is the rate at which admitted classes move to evidence-backed standing with lower cycle time and less repeated work.

## Falsifier

A WIP scanner is inadequate if it equates inactivity with completion or activity with progress without examining the standing transition each repository is attempting.

## Operational exercise

For a portfolio, classify open work by failed transition: observe, admit, construct, verify, publish, execute, receipt, replay, or class closure. Attack the dominant transition type rather than prioritizing by repository age alone.