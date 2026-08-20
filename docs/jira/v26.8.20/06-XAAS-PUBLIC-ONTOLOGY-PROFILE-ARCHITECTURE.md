# v26.8.20 — XaaS: Public-Ontology-Profile Architecture (Reframe)

> Reframes `03-XAAS-ASH-ECOSYSTEM-MAP.md`'s implicit premise. Not started as an implementation
> ticket beyond the ontology-fetch step recorded below.

## The reframe

Prior docs in this series (03, 04) treated `ontology/platform-console-capabilities.ttl` as the
XaaS vocabulary to extend. The corrected architecture, stated precisely:

```text
O_public --profile+align+constrain--> O*_xaas --SPARQL/ggen--> projections (Terraform, Ash, K8s, ...)
```

**not** `invent xaas.ttl → write templates`. Terraform, Erlang, Kubernetes, Crossplane, Phoenix,
Backstage are late-stage projections from ggen's perspective — the first XaaS engineering task is
determining how much of the semantic universe already exists publicly, and manufacturing new
`xaas:` terms only where a competency question proves a genuine gap. The Platform Engineer's
Handbook (`04`) is a **competency-question corpus**, not the ontology source.

Composition operators are distinguished deliberately: `owl:imports` (include into reasoning
closure), `prof:isProfileOf` (constrain/combine/extend), `skos:exactMatch`/`closeMatch` (vocabulary
relation without OWL identity), SPARQL CONSTRUCT (projection/alignment). `owl:equivalentClass`/
`equivalentProperty` are refused unless equivalence is actually demonstrated — e.g.
`tosca:Capability ≈ fno:Function` is a hypothesis, not yet an equivalence; `odrl:Permission ≠
XaaS execution authority` until proven otherwise.

## What's been done this session: batch 1 of the public-ontology fetch

`~/ggen-marketplace/ontologies/public/` already held CORE candidates from prior work: PROV-O,
DCAT, ORG, SOSA, OWL-Time, SPDX, SKOS, FOAF, GoodRelations, Schema.org, Dublin Core — confirmed by
directory listing before fetching anything new (no duplicate fetches).

**9 new, real, hash-pinned ontologies fetched and committed** to
`ggen-marketplace/ontologies/public/xaas-profile-batch-1/` (commit `135d9ec`, full provenance —
source URL, SHA-256, publisher/status — in that directory's `MANIFEST.md`): ODRL 2.2, PROF (W3C
Profiles Vocabulary — the vocabulary that lets XaaS itself be declared as a `prof:Profile`), QUDT
2.1, the TOGAF 9.2 Content Metamodel Ontology, three OSLC vocabularies (Automation, Configuration
Management, Requirements Management), P-PLAN (extends PROV-O for plan/step/execution — the
plan≠execution distinction `autofde-lab`/`gymact` already enforce in code), and FnO (Function
Ontology — abstract function vs. implementation vs. execution, the closest public match to a
`ce:Capability`-shaped concept found yet).

**Explicitly not obtained, disclosed not dropped**: GeoSPARQL 1.1 (every candidate URL 404'd this
pass — the real file path needs re-locating), CoCoOn (cloud computing ontology — only a PDF paper
found, no stable OWL download URL), NML/INDL/OMN (infrastructure-topology/federation ontologies,
not yet searched for stable URLs this pass).

## What has not been done yet

No qualification: no logical-consistency check, no SHACL conformance check, no namespace-collision
check, no competency-question coverage test against the 44 `ce:Capability` individuals in
`ontology/platform-console-capabilities.ttl`. This was retrieval + hash-pinning only. The next real
artifact is `packs/xaas-public-ontology-profile/` in `ggen-marketplace` (`pack.toml`, `profile.ttl`,
`locks/*.lock.toml` per-ontology, `mappings/` for NIST-cloud/TOSCA/FOCUS/OpenTelemetry/K8s/
Terraform, `shapes/*.shacl.ttl`, `queries/competency/`, `gates/*.rq`) — not built.

## See Also

- `~/ggen-marketplace/ontologies/public/xaas-profile-batch-1/MANIFEST.md` — full fetch provenance
- [`03-XAAS-ASH-ECOSYSTEM-MAP.md`](03-XAAS-ASH-ECOSYSTEM-MAP.md),
  [`04-XAAS-BEAMOPS-2E-MDBOOK-PLAN.md`](04-XAAS-BEAMOPS-2E-MDBOOK-PLAN.md) — prior docs this
  reframes without retracting; the Handbook chapter list in `04` is repositioned as a competency-
  question source, not an ontology source
- [`05-PORTFOLIO-SURVEY-RESTARTED-FROM-ZERO.md`](05-PORTFOLIO-SURVEY-RESTARTED-FROM-ZERO.md) —
  the fresh-verification discipline this doc's fetch-provenance table follows
