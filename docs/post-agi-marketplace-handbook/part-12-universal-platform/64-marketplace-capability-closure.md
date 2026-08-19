# 64. Marketplace Capability Closure

## Closure is bounded, not infinite

Marketplace capability closure asks: for a bounded set of markets, what commercial, packaging, governance, channel, and operational capabilities exist, overlap, or remain unique?

```text
Closure(B) = ⋃ Capabilities(m), m ∈ B
Core(B) = ⋂ Capabilities(m), m ∈ B
```

Those equations describe the observed market set. They do not mean the product should implement every feature in the union.

## Bound the universe

For this edition the useful market family includes at least:

- AWS Marketplace;
- Microsoft commercial marketplace;
- Google Cloud Marketplace;
- Oracle Cloud Marketplace;
- IBM catalogs/partner surfaces;
- SAP Store/partner ecosystem;
- Salesforce AppExchange;
- ServiceNow Store;
- Red Hat/Kubernetes ecosystem;
- Snowflake Marketplace;
- Databricks Marketplace;
- Alibaba Cloud Marketplace;
- direct/channel/private procurement;
- future regional/sovereign markets.

New markets extend `B`; they do not invalidate the method.

## Normalize before union

Capability names are not sufficient. `private offer`, `subscription`, `license`, `entitlement`, `package`, and `certification` can mean different things. Closure is calculated over admitted canonical semantics plus explicit vendor extensions.

A matrix cell therefore carries mapping type, standing, evidence, and exclusion—not a check mark.

## Product selection

After the market union is known, the product selects capabilities under ontology, buyer need, authority, cost, security, operational burden, and evidence.

```text
AdmittedProductCapabilities =
  select(Closure(B), ProductIntent, EnterpriseNeed,
         Cost, Authority, Evidence, Risk)
```

This is combinatorial maximalism: preserve reversible lawful options before irreversible selection, but do not implement meaningless edges merely to make a matrix look full.

## One failed edge is topology

Suppose one marketplace cannot represent a canonical usage model. That capability is UNSUPPORTED for that projection. The product may still sell there with a subscription plan or a different admitted offer. The graph records the edge rather than declaring the entire marketplace failed.

## Future closure

A new marketplace pack should start from a capability descriptor and ontology mapping. The first result can contain many UNKNOWN cells. Knowledge grows by admission and execution, not by filling blanks optimistically.

## Refusals

- `REFUSED:BIG_THREE_AS_UNIVERSE`
- `REFUSED:CAPABILITY_UNION_AS_PRODUCT_REQUIREMENT`
- `REFUSED:NAME_SIMILARITY_AS_SEMANTIC_NORMALIZATION`
- `REFUSED:ONE_UNSUPPORTED_EDGE_AS_MARKET_FAILURE`
- `REFUSED:UNKNOWN_CELL_FILLED_BY_ANALOGY`

## Operational exercise

Build the capability matrix for the bounded vendor set above across seller admission, public/private offer, entitlement, metering, settlement, SaaS, container/Kubernetes, data/AI, certification, support, and co-sell. Compute core, extensions, gaps, and UNKNOWNs, then select the product's actual target set with explicit rationale.
