# 45. Generating Deployment Artifacts

## Deployment artifacts are fulfillment projections

Containers, Helm charts, Operators, IaC modules, managed applications, SaaS registration payloads, and configuration schemas express how an admitted product version can be fulfilled in a target environment. They are not the canonical product identity.

```text
DeploymentArtifact_m = π_m(AdmittedDeploymentModel)
```

The projection must preserve operational invariants: security controls, identity, network policy, resource requirements, observability, upgrade semantics, and supported configuration.

## Deterministic build

Artifact manufacture should pin source, dependencies, generator/toolchain, configuration, and target assumptions. The result is content-addressed wherever the format permits.

For a container:

```text
source SHA
→ deterministic build inputs
→ image digest
→ SBOM/provenance
→ scan/signature
→ marketplace/package projection
```

For Helm or IaC, rendered output should be replayable from exact source and values/schema.

## Configuration is part of the contract

Marketplace packages often expose customer configuration. An unbounded free-form values surface can let customers disable security controls or construct unsupported topology.

Classify options:

- supported and customer-selectable;
- supported but constrained;
- internal/generated;
- marketplace-specific;
- prohibited.

Schema and admission should reject invalid combinations before actuation.

## Cross-market packaging

The same deployment model can generate:

- Helm for generic Kubernetes;
- Operator bundle for OpenShift/Red Hat;
- cloud-specific managed-app wrapper;
- Google Marketplace Kubernetes application metadata;
- customer-hosted IaC;
- vendor-hosted SaaS registration metadata.

The package formats differ while canonical runtime requirements stay aligned.

## Security preservation

If a marketplace validator rejects an implementation detail, first identify the invariant that detail protects. Replacing a resource is legitimate if the alternate architecture preserves the invariant and is admitted. Deleting the control to pass validation is not.

## Upgrade artifacts

Deployment generation includes migrations, version compatibility, rollback/forward-fix strategy, and lifecycle metadata. Publishing a new image under an old listing without updating product-version mapping breaks evidence correspondence.

## Execution proof

`helm template`, schema validation, or a successful package build proves structure. Target support requires execution in the exact bounded target and verification of customer-visible postconditions.

## Refusals

- `REFUSED:LATEST_TAG_AS_ARTIFACT_IDENTITY`
- `REFUSED:UNBOUNDED_CONFIGURATION_ESCAPE_HATCH`
- `REFUSED:SECURITY_INVARIANT_DROPPED_FOR_PACKAGING`
- `REFUSED:GENERATED_ARTIFACT_HAND_EDIT`
- `REFUSED:PACKAGE_BUILD_AS_RUNTIME_ALIVE`

## Operational exercise

Take one canonical Kubernetes deployment model and generate generic Helm, Red Hat Operator, and one cloud-managed-application projection. Document which invariants must survive all three and what exact execution proves each target independently.
