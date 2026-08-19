# 32. Data Governance and Residency

## Geography is product topology

Data governance determines which marketplace and deployment paths are lawful. Data class, controller/processor role, storage region, replication, logs, support access, subprocessors, backups, model use, retention, deletion, and cross-border transfer are architectural inputs.

```text
AllowedTargets =
  RuntimeCapabilities
  ∩ MarketplaceCapabilities
  ∩ DataResidency
  ∩ Sovereignty
  ∩ Contract
  ∩ SecurityPolicy
```

If that intersection is empty, the result is `UNSUPPORTED` or `BLOCKED`. A global-region selector does not make a forbidden topology legal.

## Classify data flows, not just databases

A platform can keep primary customer records in-region while exporting logs, traces, support bundles, backups, model prompts, telemetry, or billing metadata elsewhere. Residency claims must cover the actual flow graph.

Typical classes include:

```text
customer content
credentials/secrets
identity attributes
operational telemetry
security logs
support artifacts
billing/usage facts
model prompts/outputs
backups
```

Each can have different retention and regional rules.

## Residency versus sovereignty

Residency says where data is stored or processed. Sovereignty can add control over operator jurisdiction, support personnel, cryptographic keys, software supply chain, network routes, and legal access. They are related but not equivalent.

A sovereign marketplace may therefore require a different fulfillment class even when the same application image runs in the same geographic region.

## Subprocessors are versioned topology

A vendor's subprocessor list changes the data graph. New observability, AI, support, payment, or communications services can create new transfers. The canonical product should represent subprocessors and the data classes/regions they touch so a projection can determine whether an enterprise agreement remains admissible.

## Deletion is a lifecycle, not one API call

Deletion obligations must address active storage, replicas, backups, caches, analytics stores, support artifacts, and vendor systems. Cancellation does not automatically mean immediate deletion; the effective policy comes from admitted contract, legal hold, and retention facts.

## AI data boundaries

If AI capabilities consume customer content, the product must state whether prompts/outputs are retained, used for model training, processed by subprocessors, or cross regions. “AI enabled” does not waive the existing data governance graph.

## Refusals

- `REFUSED:REGION_SELECTION_AS_SOVEREIGNTY`
- `REFUSED:TELEMETRY_OUTSIDE_ADMITTED_RESIDENCY`
- `REFUSED:AI_TRAINING_WITHOUT_ADMITTED_DATA_POLICY`
- `REFUSED:DELETION_PROMISE_WITH_UNDEFINED_BACKUP_RETENTION`
- `REFUSED:UNMAPPED_SUBPROCESSOR`

## Operational exercise

Define a regulated customer whose application data, telemetry, support artifacts, billing facts, and AI prompts have different rules. Compute admitted marketplace/deployment targets and show every data flow that must remain in-region or under customer control.
