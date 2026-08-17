# 12. ggen as the Manufacturing Compiler

In the post-AGI architecture, ggen is not merely a code generator. It occupies the manufacturing boundary between semantic state and concrete projections.

The canonical correspondence is:

\[
Graph \rightarrow Query \rightarrow ggen \rightarrow Projection
\]

The projection may be source code, configuration, documentation, test fixtures, interfaces, policies, infrastructure, or another executable representation.

## ggen renders

The phrase **ggen renders** is deliberately modest.

Rendering means that admitted semantic inputs and deterministic manufacturing rules produce a concrete artifact. Rendering does not prove the artifact is true, safe, authorized, or operationally successful.

That separation keeps ggen powerful without making it sovereign.

## Templates are functions, not authority

A template should be understood as a projection function over typed semantic data.

\[
p_i : G^* \rightarrow A_i
\]

Its quality depends on whether it preserves the semantics required by the target representation.

A template that smuggles new business meaning into the generated artifact is not merely formatting. It has become an undeclared semantic authority.

## One semantic capability, many projections

Consider a capability to provision a bounded relational datastore. From one semantic definition, ggen may manufacture:

- a CLI subcommand;
- OpenAPI or protobuf definitions;
- an MCP tool schema;
- an A2A capability descriptor;
- Terraform resources;
- Kubernetes operators or CRDs;
- policy rules;
- documentation;
- validation fixtures;
- an OCEL event vocabulary.

The projections are allowed to differ syntactically. Their semantics must commute.

## ggen and post-AGI abundance

A post-AGI system can write equivalent artifacts directly. Why retain ggen?

Because repeatable manufacture is more valuable than repeated invention.

Once a construction class is understood, a deterministic compiler turns the class from reasoning work into inherited machinery. The model can then spend intelligence on new classes, anomalies, or changing constraints rather than regenerating solved boilerplate.

## Generated artifacts are projections

A generated file should generally be changed at its semantic source, not edited as an independent truth surface.

This is essential for large-scale reconstitution. If the projections contain hand-authored meaning that cannot be recovered from the graph and manufacturing rules, the system still contains artisanal knowledge.

## ggen is not the platform

Even in a ggen-centric ecosystem, the compiler is not the constitutional root. Ontology, admission, authority, evidence, receipts, and replay remain separate concerns.

The tool can be replaced while the semantics survive.

## Falsifier

If deleting all generated projections prevents the system from reconstructing their required semantics, the manufacturing source is incomplete.

## Operational exercise

Choose one manually maintained multi-surface capability. Identify a minimal semantic graph from which ggen could render at least three current representations. Treat any remaining hand-maintained semantic difference as explicit representational WIP.