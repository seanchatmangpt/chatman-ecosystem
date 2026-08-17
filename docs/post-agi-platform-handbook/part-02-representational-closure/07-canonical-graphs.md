# 7. Canonical Graphs and Generated Projections

Human software organizations routinely create five or ten independent representations of the same capability: source schema, API spec, CLI parser, portal form, Terraform module, Kubernetes YAML, policy rules, dashboard metadata, MCP tool schema, and documentation.

The failure is not duplication of bytes. It is duplication of meaning.

## Source of meaning versus source of bytes

A canonical semantic graph is the source of meaning. Generated artifacts are sources of bytes for their target runtimes.

\[
G_{canonical} \xrightarrow{projection_i} A_i
\]

A projection can be regenerated. Its hand-edited divergence should not outrank the canonical graph.

This is why generated files are not lawful editing surfaces unless the reverse semantic morphism is explicitly defined and admitted.

## Commutation is the quality criterion

Suppose the same capability is projected to CLI and MCP. If the two interfaces accept different semantic constraints, one projection has drifted.

The desired property is semantic commutation: different projection paths preserve the same admitted meaning.

\[
G \rightarrow CLI
\]

\[
G \rightarrow MCP
\]

The concrete syntax differs; the capability identity, policy, authority class, inputs, outputs, and refusal semantics should remain equivalent.

## Reverse mutation is a separate operation

Humans often edit generated YAML because it is convenient. In a post-AGI system this must be typed explicitly.

A reverse operation is not “save the file.” It is:

\[
A_i \xrightarrow{reverse?} \Delta G
\]

The reverse mapping may be ambiguous or lossy. If so, the system must refuse or construct candidate graph patches for review rather than silently mutating semantic authority.

## Why this matters at machine speed

At human throughput, representational drift is expensive. At post-AGI throughput, it becomes explosive. An intelligence can generate millions of consistent-looking artifacts faster than humans can notice that two interfaces encode different policy.

The defense is not more review. It is to remove unnecessary independent semantic sources.

## Projection inventory

Common projections include:

- source code and types;
- JSON Schema, OpenAPI, AsyncAPI, protobuf, GraphQL;
- CLI commands;
- REST/gRPC APIs;
- MCP and A2A surfaces;
- Terraform and Kubernetes artifacts;
- CI workflows;
- developer portal entities;
- tests, fixtures, docs, and runbooks.

The number of projections can increase without increasing the number of semantic authorities.

## Falsifier

If two generated surfaces can disagree about the same capability without a failing semantic gate, representational closure has not been achieved.

## Operational exercise

Select one capability exposed in three interfaces. Trace each field back to its semantic source. Any field whose meaning exists only in generated projection is a candidate for lifting into the canonical graph.