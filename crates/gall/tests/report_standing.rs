//! Real-struct tests: the JSON projection must derive `standing` from the
//! checkpoints actually carried, not assert ALIVE unconditionally.

use chatman_ecosystem::{Checkpoint, GallReport, Standing};

fn checkpoint(phase: u8, standing: Standing) -> Checkpoint {
    Checkpoint {
        id: format!("S{phase}"),
        phase,
        name: "n".to_owned(),
        standing,
        receipt_hash: "deadbeef".to_owned(),
        evidence: "none".to_owned(),
    }
}

#[test]
fn blocked_checkpoint_is_not_reported_alive() {
    let report = GallReport {
        checkpoints: vec![
            checkpoint(0, Standing::Alive),
            checkpoint(1, Standing::Blocked),
        ],
        root_receipt: "0000".to_owned(),
    };
    assert_eq!(report.standing(), Standing::Blocked);
    assert!(report.to_json().starts_with("{\"standing\":\"BLOCKED\","));
}

#[test]
fn empty_report_is_unknown() {
    let report = GallReport {
        checkpoints: Vec::new(),
        root_receipt: "0000".to_owned(),
    };
    assert_eq!(report.standing(), Standing::Unknown);
    assert!(report.to_json().starts_with("{\"standing\":\"UNKNOWN\","));
}

#[test]
fn all_alive_reports_alive() {
    let report = GallReport {
        checkpoints: vec![
            checkpoint(0, Standing::Alive),
            checkpoint(1, Standing::Alive),
        ],
        root_receipt: "0000".to_owned(),
    };
    assert_eq!(report.standing(), Standing::Alive);
    assert!(report.to_json().starts_with("{\"standing\":\"ALIVE\","));
}

#[test]
fn run_gall_report_is_alive_and_well_formed() {
    let report = chatman_ecosystem::run_gall().expect("gall crown must execute");
    assert_eq!(report.standing(), Standing::Alive);
    assert_eq!(report.root_receipt.len(), 64);
}

#[test]
fn crown_line_reports_derived_standing() {
    let report = GallReport {
        checkpoints: vec![
            checkpoint(0, Standing::Alive),
            checkpoint(1, Standing::Blocked),
        ],
        root_receipt: "abcd".to_owned(),
    };
    assert_eq!(report.crown_line(), "GALL_CROWN BLOCKED abcd");
}

#[test]
fn crown_line_for_alive_report_keeps_shape() {
    let report = GallReport {
        checkpoints: vec![checkpoint(0, Standing::Alive)],
        root_receipt: "abcd".to_owned(),
    };
    assert_eq!(report.crown_line(), "GALL_CROWN ALIVE abcd");
}

#[test]
fn empty_report_crown_line_is_unknown() {
    let report = GallReport {
        checkpoints: Vec::new(),
        root_receipt: "abcd".to_owned(),
    };
    assert_eq!(report.crown_line(), "GALL_CROWN UNKNOWN abcd");
}

#[test]
fn exit_code_fails_closed_for_non_alive_standing() {
    let blocked = GallReport {
        checkpoints: vec![checkpoint(0, Standing::Blocked)],
        root_receipt: "abcd".to_owned(),
    };
    let empty = GallReport {
        checkpoints: Vec::new(),
        root_receipt: "abcd".to_owned(),
    };
    let alive = GallReport {
        checkpoints: vec![checkpoint(0, Standing::Alive)],
        root_receipt: "abcd".to_owned(),
    };
    assert_eq!(blocked.exit_code(), 1);
    assert_eq!(empty.exit_code(), 1);
    assert_eq!(alive.exit_code(), 0);
}
