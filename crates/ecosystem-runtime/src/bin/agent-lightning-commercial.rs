#[path = "../agent_lightning_commercial_plane.rs"]
mod agent_lightning_commercial_plane;
#[path = "../agent_lightning_service.rs"]
mod agent_lightning_service;
#[path = "../commerce.rs"]
mod commerce;

use agent_lightning_commercial_plane::{DeploymentPolicy, verify_full_fixtures};
use agent_lightning_service::{Policy, REPOSITORY, SHA};
use std::env;
use std::process::ExitCode;

fn usage() -> &'static str {
    "agent-lightning-commercial\n\nUSAGE:\n  agent-lightning-commercial verify-fixtures\n  agent-lightning-commercial describe\n"
}

async fn execute(arguments: &[String]) -> Result<String, String> {
    match arguments {
        [command] if command == "verify-fixtures" => {
            let report = verify_full_fixtures()
                .await
                .map_err(|error| error.to_string())?;
            serde_json::to_string_pretty(&report).map_err(|error| error.to_string())
        }
        [command] if command == "describe" => {
            let policy = Policy::agent_lightning();
            let deployment = DeploymentPolicy::enterprise_default();
            serde_json::to_string_pretty(&serde_json::json!({
                "implementation_standing": "ALIVE",
                "service_standing": "PARTIAL_ALIVE",
                "workload": {
                    "repository": REPOSITORY,
                    "sha": SHA,
                },
                "service_policy": policy,
                "deployment_policy": deployment,
                "commercial_path": [
                    "marketplace_fulfillment_receipt",
                    "tenant_entitlement_binding",
                    "fingerprint_only_identity_registration",
                    "file_backed_sqlite_identity_snapshot",
                    "api_key_rotation",
                    "deployment_reliability_admission",
                    "multi_meter_cost_quote",
                    "usage_reservation",
                    "actuation_receipt",
                    "actuation_permit",
                    "usage_reconciliation",
                    "provider_neutral_metering_intent",
                    "provider_meter_receipt",
                    "provider_settlement_receipt",
                    "settlement_acceptance_receipt",
                    "deterministic_replay",
                ],
                "excluded_do": [
                    "direct Agent Lightning actuation without a permit receipt",
                    "plaintext API key persistence",
                    "provider metering without receipted usage",
                    "settlement acceptance without matching provider receipts",
                ],
            }))
            .map_err(|error| error.to_string())
        }
        [command] if command == "--help" || command == "-h" => Ok(usage().into()),
        _ => Err(usage().into()),
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
