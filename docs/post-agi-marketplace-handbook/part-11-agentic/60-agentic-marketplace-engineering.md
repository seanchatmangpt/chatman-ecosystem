# 60. Agentic Marketplace Engineering

## Agents increase construction bandwidth

Marketplace engineering contains large volumes of read-heavy, comparison-heavy, generation-heavy work: monitor vendor changes, map ontology, produce adapters, create listing projections, diagnose failed qualification, prepare evidence, compare pricing models, and construct support or revenue-operations intents.

Agents are ideal for this work when their outputs remain typed by authority.

```text
AgentCapability != AgentAuthority
```

## Useful agent roles

### Discovery agent

Observes official marketplace documentation and proposes graph/pack deltas. It cannot mark the new contract admitted simply because it found a page.

### Projection agent

Constructs vendor mappings, schemas, adapters, package candidates, and listing metadata from admitted graph state.

### Qualification agent

Runs structural tests, gym episodes, differential tests, and sandbox reads. It proposes standing based on receipts; the standing calculator enforces policy.

### Pricing analyst

Simulates price/unit economics and constructs candidate plan/private-offer changes. It cannot alter accepted agreements or publish prices.

### Support agent

Correlates entitlement, fulfillment, telemetry, and receipts; constructs diagnosis/repair intents. Customer-impacting DO still requires the appropriate authority.

### Revenue-operations agent

Reconciles opportunity, agreement, usage, settlement, and channel attribution; constructs exceptions and follow-ups without inventing money movements.

## Information partitions remain real

Do not give an agent every secret merely because it is convenient. Each role receives the minimum admitted observation set: vendor docs, product graph, support telemetry, or finance evidence as appropriate.

This makes agent behavior auditable and reduces accidental cross-tenant or cross-function data disclosure.

## Hooks manufacture intents

A documentation change, GitHub event, marketplace notification, monitoring alert, or CRM update can wake an agent. The hook does not grant DO. The agent constructs a bounded intent which is independently admitted.

## Falsification before escalation

Agents should aggressively explore reversible possibilities: alternate mappings, packaging paths, failure hypotheses, pricing scenarios, and repair plans. Only surviving candidates approach an irreversible boundary.

This is combinatorial maximalism under evidence and cost bounds.

## Refusals

- `REFUSED:AGENT_PUBLISHES_FROM_WEB_RESEARCH`
- `REFUSED:PRICING_AGENT_CHANGES_ACCEPTED_AGREEMENT`
- `REFUSED:SUPPORT_AGENT_ISSUES_CREDIT_WITHOUT_AUTHORITY`
- `REFUSED:AGENT_SELF_ATTESTS_EVIDENCE`
- `REFUSED:HOOK_AS_AUTHORITY_GRANT`

## Operational exercise

Define discovery, projection, qualification, pricing, support, and revops agents. Assign each observation, SELECT, CONSTRUCT, and DO capabilities. Every DO must name the external authority object and required receipt; most agent work should terminate before DO.
