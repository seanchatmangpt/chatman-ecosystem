# Preface — From Platform Engineering to Marketplace Engineering

The first platform-engineering problem is internal coordination: turn fragmented infrastructure, delivery, security, observability, and developer workflows into a platform that people can consume as a product.

The next problem appears as soon as that platform leaves the organization.

An enterprise buyer does not purchase a Git repository, a Kubernetes manifest, or an architecture diagram. It purchases rights and obligations through a commercial system. That system may be AWS Marketplace, Microsoft commercial marketplace, Google Cloud Marketplace, Oracle Cloud Marketplace, SAP Store, Salesforce AppExchange, a data marketplace, a distributor-led private offer, a sovereign marketplace, or a direct contract routed through an enterprise procurement catalog.

Each of those systems uses different names and protocols. That difference tempts teams to build one bespoke integration per market. The result is predictable: duplicated entitlement state, duplicated pricing semantics, duplicated customer identity, marketplace-specific feature forks, untraceable billing discrepancies, and operational runbooks that become more expensive with every new route to market.

This book takes the opposite position.

## The commercial product precedes the listing

We define a canonical product graph before we define an AWS product code, Microsoft offer ID, Google entitlement, Oracle listing ID, Salesforce package, or SAP solution listing.

The graph contains product identity, capabilities, versions, plans, offers, agreements, entitlements, usage dimensions, deployment classes, support policies, security claims, lifecycle rules, provenance, and receipts.

Each marketplace is then a projection:

```text
C_m = π_m(G_c)
```

The projection may be richer or poorer than the core in a particular dimension. That is allowed. What is not allowed is an unrecorded change in customer meaning.

## Commercial portability is stronger than multi-cloud

Multi-cloud answers where software can execute.

Commercial portability answers whether the same product can preserve its identity and obligations while moving through different procurement, entitlement, fulfillment, metering, settlement, support, channel, and governance systems.

A product is not commercially portable because the same container runs in three clouds. It is commercially portable when an enterprise can buy the same admitted product through multiple markets and the resulting rights, runtime behavior, evidence, and economics remain explainably related.

## Why post-AGI changes the engineering method

A sufficiently capable model can read vendor documentation, generate adapters, draft listings, map schemas, construct deployment packages, and explore thousands of integration combinations. That increases the importance of boundaries rather than reducing it.

Model output is a candidate. Generated code is a candidate. A generated contract is a candidate. A proposed price is a candidate. None carries ambient authority.

The system therefore optimizes **reversible lawful construction** before irreversible selection. It generates many defensible candidates, falsifies them cheaply, admits the surviving subject, and routes consequential operations through explicit authority.

That is the practical meaning of the Chatman Equation here:

```text
A = μ(O*)
R = receipt(A)
```

The manufacture may be extraordinarily fast. The admission remains exact.

## External clocks remain external

Marketplace seller registration, tax verification, banking validation, partner enrollment, legal review, security review, customer procurement, and marketplace certification can be partially prepared by software. They cannot be truthfully described as completed until the external authority completes them.

This matters because an engineering organization can compress code-scaffolding time by orders of magnitude and still be blocked on a vendor review queue. The book uses `BLOCKED` for that topology rather than pretending the clock disappeared.

## How the book is organized

Parts I–III build the canonical commercial model and control plane. Part IV projects that model into concrete vendor ecosystems. Parts V–VI address Fortune 5 procurement and channel motion. Part VII manufactures integrations with `ggen`. Part VIII qualifies them through gyms, differential testing, and live execution. Parts IX–XI constrain actuation, operations, and agentic behavior. Part XII derives the universal commercial platform. Part XIII executes the complete build from canonical graph to an evidence-backed enterprise sale.

The appendices make the book operational: ontology, adapter contracts, state machines, readiness matrix, receipt schemas, gym specification, pack specification, reference architecture, and capability matrix.

The standard for every chapter is the same: preserve identity, fence authority, admit facts, construct maximally, actuate minimally, receipt consequences, replay evidence, and state standing exactly.
