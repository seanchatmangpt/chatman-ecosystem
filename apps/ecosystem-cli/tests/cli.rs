use ecosystem_core::REQUIRED_ADMISSION_GATES;
use serde_json::json;
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;

static PROCESS_TEST_LOCK: Mutex<()> = Mutex::new(());

fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn run(arguments: &[&str]) -> Result<std::process::Output, std::io::Error> {
    Command::new(env!("CARGO_BIN_EXE_ecosystem"))
        .env("ECOSYSTEM_ROOT", root())
        // GitHub pull_request jobs expose GITHUB_SHA as a synthetic merge ref even
        // when the repository is deliberately checked out at the exact candidate
        // head. Black-box process tests must exercise the admitted checkout, not
        // inherit an unrelated ambient subject identity.
        .env_remove("GITHUB_SHA")
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
    Ok(format!("git:{}", String::from_utf8(output.stdout)?.trim()))
}

#[test]
fn help_and_version_are_process_contracts() -> Result<(), Box<dyn std::error::Error>> {
    let _guard = PROCESS_TEST_LOCK
        .lock()
        .map_err(|error| error.to_string())?;
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
    let _guard = PROCESS_TEST_LOCK
        .lock()
        .map_err(|error| error.to_string())?;
    for arguments in [
        ["catalog", "validate"],
        ["receipt", "verify-all"],
        ["projection", "check"],
        ["architecture", "check"],
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

/// Copies the admitted working tree into `destination`, skipping build output and
/// version-control state. Negative admission tests must break a real checkout, never
/// the checkout under test.
fn copy_tree(source: &std::path::Path, destination: &std::path::Path) -> std::io::Result<()> {
    fs::create_dir_all(destination)?;
    for entry in fs::read_dir(source)? {
        let entry = entry?;
        let name = entry.file_name();
        if name == "target" || name == ".git" {
            continue;
        }
        let child = destination.join(&name);
        let kind = entry.file_type()?;
        if kind.is_dir() {
            copy_tree(&entry.path(), &child)?;
        } else if kind.is_file() {
            fs::copy(entry.path(), &child)?;
        }
    }
    Ok(())
}

struct Fixture {
    path: PathBuf,
}

impl Fixture {
    fn new(name: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let path =
            std::env::temp_dir().join(format!("ecosystem-negative-{name}-{}", std::process::id()));
        if path.exists() {
            fs::remove_dir_all(&path)?;
        }
        copy_tree(&root(), &path)?;
        Ok(Self { path })
    }

    fn run(&self, arguments: &[&str]) -> Result<std::process::Output, std::io::Error> {
        Command::new(env!("CARGO_BIN_EXE_ecosystem"))
            .env("ECOSYSTEM_ROOT", &self.path)
            .env_remove("GITHUB_SHA")
            .args(arguments)
            .output()
    }

    fn edit(&self, relative: &str, edit: impl Fn(String) -> String) -> std::io::Result<()> {
        let path = self.path.join(relative);
        let content = fs::read_to_string(&path)?;
        fs::write(&path, edit(content))
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

/// Induces one real violation in a throwaway copy of the working tree and asserts the
/// command surfaces it as a non-zero process exit carrying that violation's own
/// diagnostic. Correct library logic behind a zero exit code is invisible to
/// `scripts/crown.sh`, which gates purely on exit status.
fn assert_refuses(
    name: &str,
    relative: &str,
    edit: impl Fn(String) -> String,
    arguments: &[&str],
    expected: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let _guard = PROCESS_TEST_LOCK
        .lock()
        .map_err(|error| error.to_string())?;
    let fixture = Fixture::new(name)?;
    let admitted = fixture.run(arguments)?;
    assert!(
        admitted.status.success(),
        "fixture is not a faithful copy: {}",
        String::from_utf8_lossy(&admitted.stderr)
    );
    fixture.edit(relative, edit)?;
    let refused = fixture.run(arguments)?;
    assert!(
        !refused.status.success(),
        "violation was admitted: {}",
        String::from_utf8_lossy(&refused.stdout)
    );
    let stderr = String::from_utf8_lossy(&refused.stderr).into_owned();
    assert!(stderr.contains(expected), "wrong refusal reason: {stderr}");
    Ok(())
}

fn tamper_receipt(content: &str) -> String {
    content.replace(
        "admit the initial constitutional control-plane implementation",
        "admit anything at all",
    )
}

#[test]
fn catalog_validate_fails_closed_on_missing_evidence() -> Result<(), Box<dyn std::error::Error>> {
    assert_refuses(
        "catalog",
        "catalog/rails.toml",
        |content| content.replace("CONSTITUTION.md", "docs/THIS_EVIDENCE_DOES_NOT_EXIST.md"),
        &["catalog", "validate"],
        "missing evidence",
    )
}

#[test]
fn receipt_verify_all_fails_closed_on_tampered_body() -> Result<(), Box<dyn std::error::Error>> {
    assert_refuses(
        "receipt",
        "receipts/bootstrap.toml",
        |content| tamper_receipt(&content),
        &["receipt", "verify-all"],
        "digest mismatch",
    )
}

/// Blanking the digest must not launder tampering: a digest recomputed at verification
/// time authenticates whatever body it was handed.
#[test]
fn receipt_verify_all_fails_closed_on_unsealed_receipt() -> Result<(), Box<dyn std::error::Error>> {
    assert_refuses(
        "blanked",
        "receipts/bootstrap.toml",
        |content| {
            tamper_receipt(&content)
                .lines()
                .map(|line| {
                    if line.starts_with("digest = ") {
                        "digest = \"\""
                    } else {
                        line
                    }
                })
                .collect::<Vec<_>>()
                .join("\n")
        },
        &["receipt", "verify-all"],
        "unsealed receipt",
    )
}

#[test]
fn projection_check_fails_closed_on_drift() -> Result<(), Box<dyn std::error::Error>> {
    assert_refuses(
        "projection",
        "views/generated/standing.md",
        |content| content.replace("# Chatman Ecosystem Standing", "# Drifted Standing"),
        &["projection", "check"],
        "projection drift",
    )
}

#[test]
fn architecture_check_fails_closed_on_forbidden_dependency()
-> Result<(), Box<dyn std::error::Error>> {
    assert_refuses(
        "architecture",
        "crates/ecosystem-core/Cargo.toml",
        |content| {
            format!(
                "{content}\n[target.\"cfg(unix)\".dev-dependencies]\nharmless = {{ package = \"tokio\", version = \"1\" }}\n"
            )
        },
        &["architecture", "check"],
        "core depends on `tokio`",
    )
}

#[test]
fn crown_requires_exact_admission_evidence() -> Result<(), Box<dyn std::error::Error>> {
    let _guard = PROCESS_TEST_LOCK
        .lock()
        .map_err(|error| error.to_string())?;
    let path = root().join("target/crown/admission.json");
    if path.exists() {
        fs::remove_file(&path)?;
    }

    let refused = run(&["crown", "--json"])?;
    assert!(!refused.status.success());

    let exact_subject = git_subject()?;
    fs::create_dir_all(path.parent().ok_or("admission parent missing")?)?;
    fs::write(
        &path,
        serde_json::to_vec_pretty(&json!({
            "subject": exact_subject,
            "gates": REQUIRED_ADMISSION_GATES,
        }))?,
    )?;

    let admitted = run(&["crown", "--json"])?;
    assert!(
        admitted.status.success(),
        "{}",
        String::from_utf8_lossy(&admitted.stderr)
    );
    let report: serde_json::Value = serde_json::from_slice(&admitted.stdout)?;
    assert_eq!(report.get("subject").and_then(serde_json::Value::as_str), Some(exact_subject.as_str()));
    fs::remove_file(path)?;
    Ok(())
}

#[test]
fn malformed_command_fails_closed() -> Result<(), Box<dyn std::error::Error>> {
    let _guard = PROCESS_TEST_LOCK
        .lock()
        .map_err(|error| error.to_string())?;
    let output = run(&["unknown"])?;
    assert!(!output.status.success());
    Ok(())
}
