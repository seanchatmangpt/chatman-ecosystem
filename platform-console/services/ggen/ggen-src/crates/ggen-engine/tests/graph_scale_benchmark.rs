//! Real, repeatable scale benchmark for the live default graph backend
//! (`EngineKind::GraphLaw` / `GraphLawStore`, praxis-graphlaw) used by
//! `ggen sync`. Confirmed live-default by reading
//! `crates/ggen-engine/src/sync.rs` (`EngineKind::default() == GraphLaw`,
//! `new_graph_engine` maps it to `GraphLawStore::new()`).
//!
//! Not a criterion `[[bench]]` target: this crate's `Cargo.toml` has no
//! `benches/` harness wired for `ggen-engine`, and adding one is out of
//! scope for a single honest measurement. Instead this is a `#[test]`,
//! `#[ignore]`d by default so `just test-lib`/`cargo test` stay fast, run
//! explicitly for the real numbers:
//!
//! ```text
//! cargo test --release -p ggen-engine --test graph_scale_benchmark \
//!     -- --ignored --nocapture
//! ```
//!
//! Loads a synthetic triple set shaped like the real
//! `autofde-lab-capabilities.ttl` individuals (one `rdf:type` + a handful
//! of scalar predicates per individual) at 1k / 10k / 100k individuals,
//! then times one representative SPARQL SELECT at each scale. Numbers are
//! wall-clock, this machine, this run — no extrapolation is reported as a
//! measurement.

use ggen_engine::graph::{EngineQueryResults, GraphEngine, GraphLawStore};
use std::time::Instant;

const NS: &str = "http://example.org/bench#";

/// Synthesize `n` individuals shaped like a capability-catalog entry:
/// `ex:cap{i} a ex:Capability ; ex:name "..." ; ex:owner "..." ; ex:tier N ; ex:status "active" .`
fn synth_turtle(n: usize) -> String {
    let mut ttl = String::with_capacity(n * 180);
    ttl.push_str("@prefix ex: <http://example.org/bench#> .\n");
    ttl.push_str("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n");
    for i in 0..n {
        ttl.push_str(&format!(
            "ex:cap{i} a ex:Capability ; ex:name \"Capability {i}\" ; \
             ex:owner \"team{team}\" ; ex:tier {tier} ; ex:status \"active\" .\n",
            i = i,
            team = i % 25,
            tier = i % 5,
        ));
    }
    ttl
}

fn run_scale(n: usize) -> (usize, std::time::Duration, std::time::Duration, usize) {
    let store = GraphLawStore::new().expect("GraphLawStore::new");
    let ttl = synth_turtle(n);

    let load_start = Instant::now();
    let inserted = store.insert_turtle(&ttl).expect("insert_turtle");
    let load_elapsed = load_start.elapsed();

    let query = format!(
        "PREFIX ex: <{NS}>\n\
         SELECT ?cap ?name WHERE {{ ?cap a ex:Capability ; ex:name ?name ; ex:tier ?tier . \
         FILTER(?tier = 2) }}"
    );

    let query_start = Instant::now();
    let results = store.query(&query).expect("SELECT query");
    let query_elapsed = query_start.elapsed();

    let row_count = match results {
        EngineQueryResults::Solutions(rows) => rows.len(),
        other => panic!("expected SELECT solutions, got {other:?}"),
    };

    (inserted, load_elapsed, query_elapsed, row_count)
}

#[test]
#[ignore = "explicit benchmark run — see module docs; run with --ignored --nocapture"]
fn graph_scale_benchmark_graphlaw() {
    let scales = [1_000usize, 10_000, 100_000];
    println!("\n=== ggen-engine GraphLawStore (praxis-graphlaw) scale benchmark ===");
    println!(
        "{:>8} {:>12} {:>14} {:>14} {:>10}",
        "scale", "inserted", "load_ms", "select_ms", "rows"
    );
    for &n in &scales {
        let (inserted, load_elapsed, query_elapsed, rows) = run_scale(n);
        println!(
            "{:>8} {:>12} {:>14.2} {:>14.2} {:>10}",
            n,
            inserted,
            load_elapsed.as_secs_f64() * 1000.0,
            query_elapsed.as_secs_f64() * 1000.0,
            rows
        );
        // Sanity: every synthesized individual must actually load, and the
        // tier=2 filter must select roughly n/5 rows (n%5==2 residues).
        assert_eq!(inserted, n * 5, "expected 5 triples per individual");
        let expected_rows = (0..n).filter(|i| i % 5 == 2).count();
        assert_eq!(rows, expected_rows);
    }
}
