use serde_json::Value;
use std::path::PathBuf;
use std::process::Command;

fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn run(arguments: &[&str]) -> Result<std::process::Output, std::io::Error> {
    Command::new(env!("CARGO_BIN_EXE_ecosystem"))
        .env("ECOSYSTEM_ROOT", root())
        .env_remove("GITHUB_SHA")
        .args(arguments)
        .output()
}

#[test]
fn capability_cli_lists_exact_catalog() -> Result<(), Box<dyn std::error::Error>> {
    let output = run(&["capability", "list"])?;
    assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    let items: Vec<Value> = serde_json::from_slice(&output.stdout)?;
    assert_eq!(items.len(), 22);
    assert!(items.iter().all(|item| item["authority_from_surface"] == false));
    Ok(())
}

#[test]
fn capability_cli_projects_all_protocol_surfaces_without_do() -> Result<(), Box<dyn std::error::Error>> {
    for surface in ["cli", "api", "mcp", "a2a"] {
        let output = run(&["capability", "surface", surface])?;
        assert!(output.status.success(), "{surface}: {}", String::from_utf8_lossy(&output.stderr));
        let payload: Value = serde_json::from_slice(&output.stdout)?;
        assert_eq!(payload["surface"], surface);
        assert_eq!(payload["consequential_do_claimed"], false);
        assert_eq!(payload["capabilities"].as_array().map(Vec::len), Some(22));
    }
    Ok(())
}

#[test]
fn capability_cli_refuses_unknown_identity() -> Result<(), Box<dyn std::error::Error>> {
    let output = run(&["capability", "show", "capability:not-present"])?;
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("REFUSED:UNKNOWN_CAPABILITY"));
    Ok(())
}
