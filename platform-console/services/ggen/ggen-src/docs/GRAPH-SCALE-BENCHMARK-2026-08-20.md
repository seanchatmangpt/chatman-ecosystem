# Graph Scale Benchmark — 2026-08-20

## What this establishes

The "receipt/ontology graph queryable at volume" audit/provenance claim was
aspirational, not benchmarked. This document reports one real, repeatable
measurement of the actual current ceiling on the live default graph backend
used by `ggen sync`.

## Backend confirmed by reading the code

`crates/ggen-engine/src/sync.rs`:

```rust
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum EngineKind {
    #[default]
    GraphLaw,   // praxis-graphlaw
    Oxigraph,
}

pub fn new_graph_engine(kind: EngineKind) -> Result<Arc<dyn GraphEngine>> {
    match kind {
        EngineKind::GraphLaw => Arc::new(GraphLawStore::new()?),
        EngineKind::Oxigraph => Arc::new(DeterministicGraph::new()?),
    }
}
```

`EngineKind::default()` is `GraphLaw`, and `load_for_query` (the ordinary,
no-engine-argument entry point in `crates/ggen-engine/src/project_graph.rs`)
calls `load_for_query_with_engine(root, EngineKind::default())`. So the live
default graph backend for `ggen sync` is **praxis-graphlaw's `GraphLawStore`**,
not oxigraph — confirmed by reading the real code, not assumed.

## Benchmark

`crates/ggen-engine/tests/graph_scale_benchmark.rs` — a `#[test]`, `#[ignore]`d
by default so it doesn't slow down `just test-lib`/`cargo test`. It:

1. Synthesizes Turtle shaped like a real capability-catalog individual
   (`rdf:type` + `name` + `owner` + `tier` + `status` — 5 triples/individual,
   the same shape as `autofde-lab-capabilities.ttl`'s real 88 individuals,
   scaled up) at 1,000 / 10,000 / 100,000 individuals.
2. Inserts it into a fresh `GraphLawStore` via the real `GraphEngine::insert_turtle`,
   timing the insert.
3. Runs one real SPARQL `SELECT ?cap ?name WHERE { ?cap a ex:Capability ;
   ex:name ?name ; ex:tier ?tier . FILTER(?tier = 2) }` via the real
   `GraphEngine::query`, timing the query.
4. Asserts on real returned state: triple count inserted, and SELECT row
   count against the true expected count (`n/5` individuals per tier
   residue) — not an interaction/mock assertion.

Run it yourself:

```bash
cd ~/chatman-ecosystem/platform-console/services/ggen/ggen-src
cargo test --release -p ggen-engine --test graph_scale_benchmark -- --ignored --nocapture
```

## Real numbers observed (this machine, two runs, release build)

| scale (individuals) | triples inserted | load (ms) | SELECT (ms) | rows returned |
|---:|---:|---:|---:|---:|
| 1,000   | 5,000   | 7.6 – 8.0    | 3.3 – 10.1   | 200    |
| 10,000  | 50,000  | 71.5 – 75.1  | 22.6 – 26.0  | 2,000  |
| 100,000 | 500,000 | 1,051 – 1,093 | 305 – 417   | 20,000 |

(Ranges are the min/max across the two consecutive runs above; run
`--nocapture` yourself for a fresh sample — this is a live measurement, not
a fixed constant.)

## Honest ceiling

- At **100k synthetic individuals / 500k triples**, `GraphLawStore` loads in
  roughly **1.0–1.1 seconds** and answers one filtered SELECT in roughly
  **0.3–0.4 seconds**, on this machine, in a release build, single-threaded,
  in-process, cold store per scale (no warm cache, no concurrent load).
- This is the actual current ceiling *measured*, not extrapolated. No claim
  is made here about behavior beyond 100k individuals / 500k triples — that
  would require a further real run at that scale, not a projection from this
  data.
- This benchmark does not exercise: persistence to disk (in-memory store
  only), concurrent readers/writers, N3/Datalog materialization, SHACL
  validation, or the full `ggen sync` pipeline (Resolve→Enrich→Extract→
  Render→Write) — only raw `insert_turtle` + one `query` call on
  `GraphLawStore` in isolation. Those are separate, unmeasured surfaces.
