use chatman_ecosystem::{run_gall, Standing};

#[test]
fn all_four_phases_are_alive_in_gall_order() {
    let report = run_gall().expect("the complete Gall sequence must execute");
    assert_eq!(report.checkpoints.len(), 4);
    for (phase, checkpoint) in report.checkpoints.iter().enumerate() {
        assert_eq!(checkpoint.phase as usize, phase);
        assert_eq!(checkpoint.standing, Standing::Alive);
        assert!(checkpoint.id.starts_with("GALL-S"));
        assert_eq!(checkpoint.receipt_hash.len(), 64);
    }
    assert_eq!(report.root_receipt.len(), 64);
}

#[test]
fn every_checkpoint_contains_positive_and_negative_execution_evidence() {
    let report = run_gall().expect("the complete Gall sequence must execute");
    for checkpoint in report.checkpoints {
        assert!(
            checkpoint.evidence.contains("positive="),
            "{} lacks a positive fixture",
            checkpoint.id
        );
        assert!(
            checkpoint.evidence.contains("negative="),
            "{} lacks a negative fixture",
            checkpoint.id
        );
    }
}

#[test]
fn json_projection_is_machine_readable_in_shape_and_binds_the_crown() {
    let report = run_gall().expect("the complete Gall sequence must execute");
    let json = report.to_json();
    assert!(json.starts_with("{\"standing\":\"ALIVE\""));
    assert!(json.contains(&format!(
        "\"root_receipt\":\"{}\"",
        report.root_receipt
    )));
    assert_eq!(json.matches("\"standing\":\"ALIVE\"").count(), 5);
}
