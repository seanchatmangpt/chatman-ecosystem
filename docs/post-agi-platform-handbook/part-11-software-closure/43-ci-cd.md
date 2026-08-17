# 43. CI/CD as Derived Execution

CI/CD is one of the clearest examples of human-era semantic duplication. Build rules, test obligations, release policy, environment promotion, provenance, and deployment permissions are frequently encoded directly in workflow YAML.

The post-AGI architecture moves those semantics upward and derives the workflow.

## CI is not truth

A green status is evidence about a particular workflow execution. It is not a universal proof that the subject is ALIVE.

The workflow may test the wrong SHA, omit a required integration, rely on stale caches, or validate a neighboring artifact.

Exact-subject identity remains mandatory.

## Derive the supply chain

If the graph knows artifact types, validators, dependencies, release policy, provenance requirements, and environments, ggen can manufacture CI projections for GitHub Actions or another runner.

\[
SupplyChain_{semantic} \rightarrow Workflow_{GitHub}
\]

A local execution mode can run the same validation pack without the hosted workflow being the only embodiment of the process.

## Local ALIVE first when possible

The fastest defensible evidence is often local: deterministic tests, compilers, theorem checkers, integration environments, or capsules already available to the system.

Hosted CI then supplies publication-context evidence: exact remote head, clean checkout assumptions, platform integration, protected secrets, or multi-environment checks.

This reverses the habit of treating a remote spinner as epistemic authority.

## Exact-head law

After publication, verify the exact commit now at the PR head. CI results attached to a previous head are historical evidence.

\[
CI(head_{old}) \not\Rightarrow CI(head_{new})
\]

unless the relevant equivalence is proven.

## CD remains BRCE

A deployment workflow can construct an actuation intent, but the consequential transition still belongs to BRCE. Workflow existence and credential possession do not create ambient permission.

## Falsifier

CI/CD remains an independent semantic source if changing release policy requires editing several workflow implementations rather than changing a canonical policy or supply-chain model and regenerating projections.

## Operational exercise

Choose one workflow file. Extract every semantic rule from its runner syntax. Represent those rules above the CI provider, then identify which steps can run locally and which truly require hosted execution.