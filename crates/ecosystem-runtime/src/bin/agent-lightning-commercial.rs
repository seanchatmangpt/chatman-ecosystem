#[path = "../commerce.rs"]
mod commerce;
#[path = "../agent_lightning_service.rs"]
mod agent_lightning_service;

use agent_lightning_service::{Policy, REPOSITORY, SHA, verify_fixtures};
use std::env;
use std::process::ExitCode;

fn usage() -> &'static str {
    "agent-lightning-commercial\n\nUSAGE:\n  agent-lightning-commercial verify-fixtures\n  agent-lightning-commercial describe\n"
}

fn execute(arguments: &[String]) -> Result<String, String> {
    match arguments {
        [command] if command == "verify-fixtures" => {
            let report = verify_fixtures().map_err(|error| error.to_string())?;
            serde_json::to_string_pretty(&report).map_err(|error| error.to_string())
        }
        [command] if command == "describe" => {
            let policy = Policy::agent_lightning();
            serde_json::to_string_pretty(&serde_json::json!({
                "standing": "PARTIAL_ALIVE",
                "workload": {
                    "repository": REPOSITORY,
                    "sha": SHA,
                },
                "policy": policy,
                "do_path": [
                    "commercial_receipt",
                    "entitlement_binding",
                    "usage_reservation",
                    "actuation_receipt",
                    "actuation_permit",
                    "usage_reconciliation",
                ],
            }))
            .map_err(|error| error.to_string())
        }
        [command] if command == "--help" || command == "-h" => Ok(usage().into()),
        _ => Err(usage().into()),
    }
}

fn main() -> ExitCode {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match execute(&arguments) {
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
