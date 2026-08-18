# 34. One Capability, Many Projections

A mature capability should not be redesigned every time a new consumer appears.

The semantic capability is one object. Interfaces are projections.

\[
Capability \rightarrow \{CLI, API, MCP, A2A, Web, SDK, Docs\}
\]

## Interface closure

Interface closure means that the major interaction surfaces preserve the same capability identity, input semantics, output semantics, authority class, refusal behavior, and evidence expectations.

The syntax can differ. The meaning should commute.

A CLI may use flags. An API may use JSON. MCP may expose a tool schema. A2A may advertise a machine capability. A portal may render a form. All should converge on the same admitted operation rather than implement neighboring versions independently.

## Projection eliminates coordination work

Human organizations commonly assign each surface to a different team. The REST API evolves, then the CLI catches up, documentation drifts, and the portal exposes an older set of fields.

At post-AGI throughput, that lag becomes unnecessary representational WIP.

If the capability graph is canonical, ggen can manufacture interface-specific artifacts together and semantic CI can verify correspondence.

## Consumer-specific affordances remain lawful

Projection does not mean every interface is identical.

Humans may need explanations and progressive disclosure. Machines may need precise schemas and compact capability discovery. Batch systems may need idempotency keys. Interactive CLIs may need completion and local validation.

Those are interface affordances, not new capability semantics.

## Authority remains downstream

An interface can expose the ability to request a consequential transition without granting the caller permission to perform it.

The interface constructs an intent. BRCE decides whether the exact request can advance to DO.

This makes it safe to expose broad discovery surfaces to intelligent systems while keeping actuation narrow.

## Versioning becomes semantic

A breaking interface change matters when capability semantics change, not merely when bytes change. Projections can evolve independently when they preserve the semantic contract.

This encourages compatibility analysis at the graph level.

## Falsifier

Interface closure fails if the same capability can be invoked through two surfaces with materially different policy or refusal semantics that are not represented in the canonical graph.

## Operational exercise

Take one operation currently exposed through API and CLI. Add an MCP projection from the same semantic source. Then verify that all three resolve to the same capability identity and BRCE intent type.