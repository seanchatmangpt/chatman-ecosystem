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
fn admission_commands_are_black_box_verified() -> Result<(), Box<dyn std::error::Error>> {
    for arguments in [
        vec!["catalog", "validate"],
        vec!["receipt", "verify-all"],
        vec!["projection", "check"],
        vec!["architecture", "check"],
        vec!["crown", "--verify"],
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
fn malformed_command_fails_closed() -> Result<(), Box<dyn std::error::Error>> {
    let output = run(&["unknown"])?;
    assert!(!output.status.success());
    Ok(())
}
