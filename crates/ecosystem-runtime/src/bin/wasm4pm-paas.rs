//! Fail-closed PaaS bridge for the exact wasm4pm process-mining boundary.
//!
//! The bridge deliberately does not reimplement wasm4pm. It verifies the generated
//! Node-target WASM package, preserves wasm4pm refusals, delegates canonical CLI
//! workflows to `wpm`, and binds every successful response to source and WASM identity.

use serde::Serialize;
use serde_json::{Value, json};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

const WASM4PM_REPOSITORY: &str = "https://github.com/seanchatmangpt/wasm4pm";
const WASM4PM_SOURCE_SHA: &str = "5ae555e4d71e76a2ed3ab08ad8f6360decb7ae0b";
const REQUIRED_EXPORTS: &[&str] = &[
    "load_ocel_v2",
    "flatten_ocel_v2",
    "discover_powl_from_log",
    "discover_powl_from_log_config",
    "parse_powl",
    "validate_partial_orders",
    "powl_execute",
];

#[derive(Debug, Serialize)]
struct ArtifactIdentity {
    repository: &'static str,
    source_sha: &'static str,
    wasm_path: String,
    wasm_blake3: String,
    declaration_path: String,
    exports: Vec<&'static str>,
}

#[derive(Debug, Serialize)]
struct BridgeReceipt {
    schema: &'static str,
    operation: String,
    subject_blake3: String,
    result_blake3: String,
    wasm_blake3: String,
    source_sha: &'static str,
    exit_code: i32,
    standing: &'static str,
}

#[derive(Debug, Serialize)]
struct BridgeResponse {
    identity: ArtifactIdentity,
    result: Value,
    receipt: BridgeReceipt,
}

fn digest(bytes: &[u8]) -> String {
    format!("blake3:{}", blake3::hash(bytes).to_hex())
}

fn package_paths(root: &Path) -> (PathBuf, PathBuf, PathBuf) {
    let pkg = root.join("wasm4pm").join("pkg");
    (
        pkg.join("wasm4pm.js"),
        pkg.join("wasm4pm.d.ts"),
        pkg.join("wasm4pm_bg.wasm"),
    )
}

fn artifact_identity(root: &Path) -> Result<ArtifactIdentity, String> {
    let (js, declaration, wasm) = package_paths(root);
    if !js.is_file() {
        return Err(format!("BUILD_BROKEN: missing generated Node module {}", js.display()));
    }
    let declaration_text = fs::read_to_string(&declaration)
        .map_err(|error| format!("BUILD_BROKEN: cannot read {}: {error}", declaration.display()))?;
    for export in REQUIRED_EXPORTS {
        if !declaration_text.contains(export) {
            return Err(format!(
                "UNSUPPORTED: exact build does not declare required export `{export}`"
            ));
        }
    }
    let wasm_bytes = fs::read(&wasm)
        .map_err(|error| format!("BUILD_BROKEN: cannot read {}: {error}", wasm.display()))?;
    if wasm_bytes.is_empty() {
        return Err(format!("BUILD_BROKEN: empty WASM artifact {}", wasm.display()));
    }
    Ok(ArtifactIdentity {
        repository: WASM4PM_REPOSITORY,
        source_sha: WASM4PM_SOURCE_SHA,
        wasm_path: wasm.display().to_string(),
        wasm_blake3: digest(&wasm_bytes),
        declaration_path: declaration.display().to_string(),
        exports: REQUIRED_EXPORTS.to_vec(),
    })
}

fn output_value(output: &Output, operation: &str) -> Result<Value, String> {
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_owned();
        return Err(format!(
            "REFUSED: wasm4pm `{operation}` failed with exit {:?}: {stderr}",
            output.status.code()
        ));
    }
    let stdout = String::from_utf8(output.stdout.clone())
        .map_err(|error| format!("REFUSED: wasm4pm `{operation}` emitted non-UTF8 output: {error}"))?;
    let trimmed = stdout.trim();
    if trimmed.is_empty() {
        return Ok(Value::Null);
    }
    Ok(serde_json::from_str(trimmed).unwrap_or_else(|_| Value::String(trimmed.to_owned())))
}

fn receipt(operation: &str, subject: &[u8], result: &Value, identity: &ArtifactIdentity) -> BridgeReceipt {
    let encoded = serde_json::to_vec(result).unwrap_or_default();
    BridgeReceipt {
        schema: "chatman.ecosystem.wasm4pm.receipt.v1",
        operation: operation.to_owned(),
        subject_blake3: digest(subject),
        result_blake3: digest(&encoded),
        wasm_blake3: identity.wasm_blake3.clone(),
        source_sha: WASM4PM_SOURCE_SHA,
        exit_code: 0,
        standing: "PARTIAL_ALIVE",
    }
}

fn emit(operation: &str, subject: &[u8], result: Value, identity: ArtifactIdentity) -> Result<(), String> {
    let response = BridgeResponse {
        receipt: receipt(operation, subject, &result, &identity),
        identity,
        result,
    };
    let text = serde_json::to_string_pretty(&response)
        .map_err(|error| format!("REFUSED: response serialization failed: {error}"))?;
    println!("{text}");
    Ok(())
}

fn wpm_binary() -> String {
    env::var("WASM4PM_WPM").unwrap_or_else(|_| "wpm".to_owned())
}

fn run_wpm(root: &Path, args: &[String]) -> Result<Output, String> {
    Command::new(wpm_binary())
        .current_dir(root)
        .args(args)
        .output()
        .map_err(|error| format!("BLOCKED: unable to execute canonical wpm CLI: {error}"))
}

fn cli(root: &Path, args: &[String]) -> Result<(), String> {
    let identity = artifact_identity(root)?;
    if args.is_empty() {
        return Err("REFUSED: at least one wpm argument is required".to_owned());
    }
    let subject = serde_json::to_vec(args)
        .map_err(|error| format!("REFUSED: cannot encode CLI subject: {error}"))?;
    let operation = format!("wpm {}", args.join(" "));
    let output = run_wpm(root, args)?;
    let value = output_value(&output, &operation)?;
    emit(&operation, &subject, value, identity)
}

fn doctor(root: &Path) -> Result<(), String> {
    let args = vec![
        "system".to_owned(),
        "doctor".to_owned(),
        "capabilities".to_owned(),
        "--format".to_owned(),
        "json".to_owned(),
    ];
    cli(root, &args)
}

fn invoke(root: &Path, export: &str, args_json: &str) -> Result<(), String> {
    if !REQUIRED_EXPORTS.contains(&export) {
        return Err(format!("UNSUPPORTED: export `{export}` is outside the admitted wasm4pm PaaS surface"));
    }
    let args: Value = serde_json::from_str(args_json)
        .map_err(|error| format!("REFUSED: export arguments must be a JSON array: {error}"))?;
    if !args.is_array() {
        return Err("REFUSED: export arguments must be a JSON array".to_owned());
    }
    let identity = artifact_identity(root)?;
    let (js, _, _) = package_paths(root);
    let script = r#"
import { pathToFileURL } from 'node:url';
const modulePath = process.env.WASM4PM_JS;
const exportName = process.env.WASM4PM_EXPORT;
const encodedArgs = process.env.WASM4PM_ARGS;
if (!modulePath || !exportName || encodedArgs === undefined) throw new Error('missing bridge environment');
const wasm = await import(pathToFileURL(modulePath).href);
const fn = wasm[exportName];
if (typeof fn !== 'function') throw new Error(`missing export ${exportName}`);
const args = JSON.parse(encodedArgs);
const result = await fn(...args);
if (typeof result === 'string') process.stdout.write(result);
else process.stdout.write(JSON.stringify(result));
"#;
    let output = Command::new("node")
        .arg("--input-type=module")
        .arg("--eval")
        .arg(script)
        .env("WASM4PM_JS", &js)
        .env("WASM4PM_EXPORT", export)
        .env("WASM4PM_ARGS", args_json)
        .output()
        .map_err(|error| format!("BLOCKED: unable to execute Node WASM host: {error}"))?;
    let operation = format!("wasm4pm::{export}");
    let value = output_value(&output, &operation)?;
    emit(&operation, args_json.as_bytes(), value, identity)
}

fn capabilities(root: &Path) -> Result<(), String> {
    let identity = artifact_identity(root)?;
    let result = json!({
        "standing": "PARTIAL_ALIVE",
        "authority": "construct_only_unless_wpm_brce_admits_do",
        "fallback": "forbidden",
        "canonical_cli": [
            "system doctor capabilities",
            "system doctor fix",
            "run",
            "algorithms",
            "evidence session",
            "evidence live"
        ],
        "wasm_exports": REQUIRED_EXPORTS,
        "replay": "delegate_to_wpm_evidence_session_mode_replay",
        "release_identity": {
            "repository": WASM4PM_REPOSITORY,
            "source_sha": WASM4PM_SOURCE_SHA
        }
    });
    emit("capabilities", b"wasm4pm-paas", result, identity)
}

fn usage() -> &'static str {
    "usage: wasm4pm-paas <capabilities|doctor|invoke|cli> <wasm4pm-root> [arguments]\n\
     invoke: wasm4pm-paas invoke <root> <export> '<json-array>'\n\
     cli:    wasm4pm-paas cli <root> -- <exact wpm arguments>"
}

fn run() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let command = args.next().ok_or_else(|| usage().to_owned())?;
    let root = args.next().ok_or_else(|| usage().to_owned())?;
    let root = PathBuf::from(root);
    match command.as_str() {
        "capabilities" => capabilities(&root),
        "doctor" => doctor(&root),
        "invoke" => {
            let export = args.next().ok_or_else(|| usage().to_owned())?;
            let encoded = args.next().ok_or_else(|| usage().to_owned())?;
            if args.next().is_some() {
                return Err("REFUSED: invoke accepts exactly one JSON argument array".to_owned());
            }
            invoke(&root, &export, &encoded)
        }
        "cli" => {
            let forwarded: Vec<String> = args.filter(|value| value != "--").collect();
            cli(&root, &forwarded)
        }
        _ => Err(format!("UNSUPPORTED: unknown bridge command `{command}`\n{}", usage())),
    }
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{}", json!({"standing":"REFUSED","error":error}));
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_session_exports_are_admitted() {
        assert_eq!(REQUIRED_EXPORTS.len(), 7);
        assert!(REQUIRED_EXPORTS.contains(&"load_ocel_v2"));
        assert!(REQUIRED_EXPORTS.contains(&"flatten_ocel_v2"));
        assert!(REQUIRED_EXPORTS.contains(&"discover_powl_from_log"));
        assert!(REQUIRED_EXPORTS.contains(&"discover_powl_from_log_config"));
        assert!(REQUIRED_EXPORTS.contains(&"parse_powl"));
        assert!(REQUIRED_EXPORTS.contains(&"validate_partial_orders"));
        assert!(REQUIRED_EXPORTS.contains(&"powl_execute"));
    }

    #[test]
    fn unknown_export_is_not_admitted() {
        assert!(!REQUIRED_EXPORTS.contains(&"actuate_cloud"));
    }

    #[test]
    fn identity_requires_all_exports_and_nonempty_wasm() {
        let root = env::temp_dir().join(format!("chatman-wasm4pm-{}", std::process::id()));
        let pkg = root.join("wasm4pm").join("pkg");
        let created = fs::create_dir_all(&pkg);
        assert!(created.is_ok());
        let declaration = REQUIRED_EXPORTS
            .iter()
            .map(|name| format!("export function {name}(): unknown;"))
            .collect::<Vec<_>>()
            .join("\n");
        assert!(fs::write(pkg.join("wasm4pm.d.ts"), declaration).is_ok());
        assert!(fs::write(pkg.join("wasm4pm.js"), "export {};\n").is_ok());
        assert!(fs::write(pkg.join("wasm4pm_bg.wasm"), b"wasm").is_ok());
        let identity = artifact_identity(&root);
        assert!(identity.is_ok());
        let _ = fs::remove_dir_all(root);
    }
}
