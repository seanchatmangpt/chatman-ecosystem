use ecosystem_core::{
    check_architecture, check_projections, verify_all_receipts, write_projections, Catalog,
    CrownReport, Standing,
};
use ecosystem_runtime::{differential_store_check, McpBoundary};
use std::env;
use std::io::{self, Read};
use std::path::PathBuf;
use std::process::{Command, ExitCode};

fn root() -> Result<PathBuf, String> {
    if let Ok(value) = env::var("ECOSYSTEM_ROOT") {
        return Ok(PathBuf::from(value));
    }
    env::current_dir().map_err(|error| error.to_string())
}

fn subject(root: &PathBuf) -> String {
    if let Ok(value) = env::var("GITHUB_SHA") {
        if !value.trim().is_empty() {
            return format!("git:{value}");
        }
    }
    match Command::new("git")
        .arg("-C")
        .arg(root)
        .args(["rev-parse", "HEAD"])
        .output()
    {
        Ok(output) if output.status.success() => {
            format!("git:{}", String::from_utf8_lossy(&output.stdout).trim())
        }
        _ => "git:UNKNOWN".to_owned(),
    }
}

fn usage() -> &'static str {
    "Chatman Ecosystem control plane\n\nUSAGE:\n  ecosystem catalog validate\n  ecosystem standing calculate\n  ecosystem receipt verify-all\n  ecosystem projection render\n  ecosystem projection check\n  ecosystem architecture check\n  ecosystem storage verify\n  ecosystem mcp handle\n  ecosystem crown [--json|--verify]\n"
}

async fn execute(arguments: &[String]) -> Result<String, String> {
    let root = root()?;
    match arguments {
        [command] if command == "--help" || command == "-h" => Ok(usage().to_owned()),
        [command] if command == "--version" || command == "-V" => {
            Ok(env!("CARGO_PKG_VERSION").to_owned())
        }
        [area, action] if area == "catalog" && action == "validate" => {
            let catalog = Catalog::load(&root).map_err(|error| error.to_string())?;
            catalog.validate(&root).map_err(|error| error.to_string())?;
            Ok("CATALOG_ALIVE".to_owned())
        }
        [area, action] if area == "standing" && action == "calculate" => {
            let report =
                CrownReport::evaluate(&root, subject(&root)).map_err(|error| error.to_string())?;
            Ok(format!("{:?}", report.standing))
        }
        [area, action] if area == "receipt" && action == "verify-all" => {
            let count = verify_all_receipts(&root).map_err(|error| error.to_string())?;
            Ok(format!("RECEIPTS_ALIVE count={count}"))
        }
        [area, action] if area == "projection" && action == "render" => {
            let count = write_projections(&root).map_err(|error| error.to_string())?;
            Ok(format!("PROJECTION_RENDERED count={count}"))
        }
        [area, action] if area == "projection" && action == "check" => {
            let count = check_projections(&root).map_err(|error| error.to_string())?;
            Ok(format!("PROJECTION_ALIVE count={count}"))
        }
        [area, action] if area == "architecture" && action == "check" => {
            check_architecture(&root).map_err(|error| error.to_string())?;
            Ok("ARCHITECTURE_GATES_ALIVE".to_owned())
        }
        [area, action] if area == "storage" && action == "verify" => {
            differential_store_check()
                .await
                .map_err(|error| error.to_string())?;
            Ok("STORAGE_MEMORY_ALIVE STORAGE_SQLX_ALIVE".to_owned())
        }
        [area, action] if area == "mcp" && action == "handle" => {
            let mut request = String::new();
            io::stdin()
                .read_to_string(&mut request)
                .map_err(|error| error.to_string())?;
            McpBoundary::handle(&request, ecosystem_core::Authority::Observe)
                .map_err(|error| error.to_string())
        }
        [command] if command == "crown" => crown(&root, false, false),
        [command, flag] if command == "crown" && flag == "--json" => crown(&root, true, false),
        [command, flag] if command == "crown" && flag == "--verify" => crown(&root, false, true),
        _ => Err(usage().to_owned()),
    }
}

fn crown(root: &PathBuf, json: bool, verify: bool) -> Result<String, String> {
    let report = CrownReport::evaluate(root, subject(root)).map_err(|error| error.to_string())?;
    if verify && report.standing != Standing::Alive {
        return Err("CROWN_NOT_ALIVE".to_owned());
    }
    if json {
        serde_json::to_string_pretty(&report).map_err(|error| error.to_string())
    } else if report.standing == Standing::Alive {
        Ok(format!(
            "CHATMAN_ECOSYSTEM_CROWN_ALIVE subject={}",
            report.subject
        ))
    } else {
        Ok(format!(
            "CHATMAN_ECOSYSTEM_CROWN_{:?} subject={}",
            report.standing, report.subject
        ))
    }
}

#[tokio::main]
async fn main() -> ExitCode {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match execute(&arguments).await {
        Ok(output) => {
            println!("{output}");
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::FAILURE
        }
    }
}
