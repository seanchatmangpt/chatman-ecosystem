# 23. One Semantic Source, Many Enterprise Surfaces

**Executive thesis:** Manual synchronization is manufactured complexity: work created only because the same decision was represented independently in several places.

## The synchronization tax

A capability may appear in API schemas, CLI help, SDKs, IAM policy, Terraform, Kubernetes, service catalogs, documentation, dashboards, tests, marketplace metadata, and audit controls. If each surface is hand-maintained, a single business change creates a fan-out of coordination tasks.

## Projection changes the economics

With a canonical semantic source, that fan-out becomes one admitted mutation followed by deterministic projections. Human attention moves from synchronizing copies to improving the invariant and the projector. The number of files may remain large while the number of independent decisions collapses.

## Projection ownership matters

Every generated path should have an unambiguous owner. Hand-written escape hatches reintroduce hidden semantics and drift. Where manual regions are necessary, they should be explicitly bounded and preserved by the generator rather than silently mixed with generated authority.

## Operating practice

Take one change that historically required multiple repository edits. Draw a correspondence map from the shared decision to every artifact. Move as many edges as possible behind deterministic projection, then add a drift gate that fails when a projection no longer matches its source.

## Diagnostic question

How many manual edits does one semantic change trigger across your enterprise?
