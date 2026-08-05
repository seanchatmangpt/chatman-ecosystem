use ecosystem_core::REQUIRED_ADMISSION_GATES;
use serde_json::json;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn run(arguments: &[&str]) -> Result<std::process::Output, std::io::Error> {
    Command::new(env!("CARGO_BIN_EXE_ecosystem"))
        .env("ECOSYSTEM_ROOT", root())
        .args(arguments)
        .output()
}

fn git_subject() -> Result<String, Box<dyn std::error::Error>> {
    let output = Command::new("git")
        .arg("-C")
        .arg(root())
        .args(["rev-parse", "HEAD"])
        .output()?;
    if !output.status.success() {
        return Err("git rev-parse failed".into());
    }
    Ok(format!(
        "git:{}",
        String::from_utf8(output.stdout)?.trim()
    ))
}

#[test]
fn help_and_version_are_process_contracts() -> Result<(), Box<dyn std::error::Error>> {
    let help = run(&["--help"])?;
    assert!(help.status.success());
    assert!(String::from_utf8(help.stdout)?.contains("USAGE"));
    let version = run(&["--version"])?;
    assert!(version.status.success());
    assert_eq!(
        String::from_utf8(version.stdout)?.trim(),
        env!("CARGO_PKG_VERSION")
    );
    Ok(())
}

#[test]
fn component_admission_commands_are_black_box_verified() -> Result<(), Box<dyn std::error::Error>> {
    for arguments in [
        vec!["catalog", "validate"],
        vec!["receipt", "verify-all"],
        vec!["projection", "check"],
        vec!["architecture", "check"],
    ] {
        let output = run(&arguments)?;
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    Ok(())
}

#[test]
fn crown_requires_exact_admission_evidence() -> Result<(), Box<dyn std::error::Error>> {
    let path = root().join("target/crown/admission.json");
    if path.exists() {
        fs::remove_file(&path)?;
    }

    let refused = run(&["crown", "--verify"])?;
    assert!(!refused.status.success());

    fs::create_dir_all(path.parent().ok_or("admission parent missing")?)?;
    fs::write(
        &path,
        serde_json::to_vec_pretty(&json!({
            "subject": git_subject()?,
            "gates": REQUIRED_ADMISSION_GATES,
        }))?,
    )?;

    let admitted = run(&["crown", "--verify"])?;
    assert!(
        admitted.status.success(),
        "{}",
        String::from_utf8_lossy(&admitted.stderr)
    );
    fs::remove_file(path)?;
    Ok(())
}

#[test]
fn malformed_command_fails_closed() -> Result<(), Box<dyn std::error::Error>> {
    let output = run(&["unknown"])?;
    assert!(!output.status.success());
    Ok(())
}
