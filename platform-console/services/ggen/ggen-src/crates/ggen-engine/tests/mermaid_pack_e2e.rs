//! Chicago-TDD e2e test for `packs/mermaid-pack` — real, non-empty consumer
//! ontology exercising real generation, not the empty-ontology stub this
//! file used to be.
//!
//! The consumer ontology declares one `mer:Diagram` individual referencing
//! an existing `mer:DiagramType` from the pack's own `ontology.ttl`
//! (`mer:Type_flowchart_v2`), satisfying every required property checked by
//! `packs/mermaid-pack/gates/*.rq` (diagramType/outputPath/sourceText/
//! authorityClass on the Diagram; standingCeiling="Observed" so gate
//! `060_no_standing_without_source_pin.rq` is satisfied by the upstream
//! release's real `prov:value` commit pin already present on
//! `mer:Type_flowchart_v2 mer:upstreamRelease mer:Mermaid_11_16_0`).
//!
//! Asserts real, non-trivial generated file content:
//! `docs/diagrams/login-flow.mmd` (from `diagram.mmd.tmpl`, driven by a
//! per-diagram SPARQL SELECT) contains the exact `sourceText` triple value,
//! and `docs/mermaid/図面台帳.md` (from `diagram_index.md.tmpl`) contains a
//! table row citing the diagram's output path and diagram-type id.

#![allow(clippy::unwrap_used, clippy::expect_used, clippy::panic)]

mod support;

use std::path::{Path, PathBuf};

use support::{assert_idempotent, read, scaffold_pack_with_ontology};

fn packs_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../../packs")
}

const CONSUMER_ONTOLOGY: &str = r#"
@prefix mer: <https://seanchatmangpt.github.io/ontology/mermaid#> .

mer:LoginFlow a mer:Diagram ;
    mer:diagramType mer:Type_flowchart_v2 ;
    mer:outputPath "docs/diagrams/login-flow.mmd" ;
    mer:sourceText "flowchart TD\n    A[User submits credentials] --> B{Valid?}\n    B -- yes --> C[Issue session token]\n    B -- no --> D[Reject with 401]" ;
    mer:authorityClass mer:Observational ;
    mer:standingCeiling "Observed" .
"#;

#[test]
fn mermaid_pack_e2e_syncs_real_diagram_from_non_empty_ontology() {
    let (_dir, project) =
        scaffold_pack_with_ontology(&packs_dir().join("mermaid-pack"), CONSUMER_ONTOLOGY);

    ggen_engine::sync::sync(
        &project,
        ggen_engine::sync::SyncOptions {
            dry_run: false,
            ..Default::default()
        },
    )
    .expect("sync must succeed against a real, gate-conforming consumer ontology");

    // Real generation: the per-diagram template rendered the diagram's own
    // sourceText verbatim to the path named by its own outputPath fact.
    let diagram = read(&project, "docs/diagrams/login-flow.mmd");
    assert!(
        diagram.contains("flowchart TD"),
        "generated .mmd must contain the real sourceText, got: {diagram}"
    );
    assert!(
        diagram.contains("Issue session token"),
        "generated .mmd must contain the real sourceText verbatim, got: {diagram}"
    );

    // Real generation: the ledger template's SPARQL SELECT joined Diagram
    // and DiagramType facts across files (consumer ontology + pack
    // ontology) to produce a non-trivial table row.
    let ledger = read(&project, "docs/mermaid/図面台帳.md");
    assert!(
        ledger.contains("docs/diagrams/login-flow.mmd"),
        "ledger must cite the real output path, got: {ledger}"
    );
    assert!(
        ledger.contains("flowchart-v2"),
        "ledger must cite the joined DiagramType's diagramId, got: {ledger}"
    );
    assert!(
        ledger.contains("Observational"),
        "ledger must cite the real authorityClass, got: {ledger}"
    );
    assert!(
        ledger.contains("Observed"),
        "ledger must cite the real standingCeiling, got: {ledger}"
    );

    assert_idempotent(&project);
}
