# Appendix D — O*.toml Reference

`O*.toml` denotes the admitted-subject carrier pattern. A concrete implementation should use the owning repository's actual schema.

```toml
[subject]
id = "service:example"
kind = "service"
repository = "owner/repo"
commit = "0123456789abcdef0123456789abcdef01234567"

[observation]
observed_at = "2026-08-16T00:00:00Z"
sources = ["git", "runtime"]

[semantics]
ontology = "platform:v3"
policy = "release:v9"

[authority]
class = "CONSTRUCT"
allow_do = false

[verification]
required = ["semantic", "unit", "integration"]

[replay]
toolchain = "toolchain:example-v1"
```

## Required properties

The carrier should make subject ambiguity visible, preserve source freshness, name semantic policy, distinguish authority class, and state the evidence expected before standing can advance.

## Anti-patterns

Avoid `branch = "main"` as the only source identity for a crown claim, `environment = "prod"` without an exact target coordinate, or `approved = true` without the authority identity and policy that made the decision.