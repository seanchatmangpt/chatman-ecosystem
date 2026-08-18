# 35. MCP as a Capability Surface

MCP is useful because it gives model-driven systems a structured way to discover and invoke tools and resources. Its importance should not be inflated into ontology.

MCP is a capability surface.

## Protocol is not semantics

An MCP tool schema can describe arguments and result shapes. The canonical meaning of the capability should live above the protocol.

\[
G_{capability} \xrightarrow{ggen} MCP_{projection}
\]

This lets the same capability appear in CLI, API, and A2A forms without redefining its law.

## Discovery without authority

A post-AGI system may be allowed to discover many capabilities. Discovery should not imply permission to actuate them.

The safest default is that MCP requests construct typed intents. Consequential intents cross BRCE.

This architecture reduces pressure to encode security through hidden tools or prompt-level restrictions.

## Typed inputs reduce semantic ambiguity

Machine consumers benefit when inputs carry exact identities, units, scopes, and refusal semantics.

For example, a tool should prefer an exact repository coordinate and commit SHA to an ambiguous string like “latest code.” QUDT-aligned units should be preferred to unitless numerics when measurement semantics matter.

## MCP servers are replaceable

The ecosystem should be able to regenerate or replace an MCP server without changing the capability's identity or authority policy.

That makes protocol evolution a projection concern.

## Tool output is observation candidate

An MCP response from an external tool becomes evidence only according to the trust policy for that source. The model should not convert tool text directly into standing without admission.

This applies even when the tool itself is trusted; staleness and exact-subject mismatch remain possible.

## Falsifier

The MCP boundary is unsound if a tool implementation can bypass the authority broker simply because it possesses credentials or is invoked from a trusted server process.

## Operational exercise

Model an MCP tool for a consequential capability as two stages: request-to-intent and intent-to-BRCE. Verify that the first can run with no production credential at all.