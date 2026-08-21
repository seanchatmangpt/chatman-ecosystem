#[path = "../commerce.rs"]
mod commerce;

use commerce::{Provider, ProviderEventKind, normalize, verify_all_provider_fixtures};
use std::env;
use std::io::{self, Read};
use std::process::ExitCode;

fn parse_provider(value: &str) -> Result<Provider, String> {
    match value {
        "aws" => Ok(Provider::Aws),
        "microsoft" | "azure" => Ok(Provider::Microsoft),
        "google" | "gcp" => Ok(Provider::Google),
        other => Err(format!("REFUSED:UNKNOWN_PROVIDER:{other}")),
    }
}

fn parse_kind(value: &str) -> Result<ProviderEventKind, String> {
    match value {
        "agreement" => Ok(ProviderEventKind::Agreement),
        "entitlement" => Ok(ProviderEventKind::Entitlement),
        "entitlement-changed" => Ok(ProviderEventKind::EntitlementChanged),
        "suspended" => Ok(ProviderEventKind::Suspended),
        "reinstated" => Ok(ProviderEventKind::Reinstated),
        "revoked" => Ok(ProviderEventKind::Revoked),
        "meter-accepted" => Ok(ProviderEventKind::MeterAccepted),
        "settlement" => Ok(ProviderEventKind::Settlement),
        other => Err(format!("REFUSED:UNKNOWN_EVENT_KIND:{other}")),
    }
}

fn usage() -> &'static str {
    "marketplace-commerce\n\nUSAGE:\n  marketplace-commerce verify-fixtures\n  marketplace-commerce normalize <aws|microsoft|google> <event-kind> < payload.json\n\nEVENT KINDS:\n  agreement entitlement entitlement-changed suspended reinstated revoked meter-accepted settlement\n"
}

fn execute(arguments: &[String]) -> Result<String, String> {
    match arguments {
        [command] if command == "verify-fixtures" => {
            let report = verify_all_provider_fixtures().map_err(|error| error.to_string())?;
            serde_json::to_string_pretty(&report).map_err(|error| error.to_string())
        }
        [command, provider, kind] if command == "normalize" => {
            let provider = parse_provider(provider)?;
            let kind = parse_kind(kind)?;
            let mut input = String::new();
            io::stdin()
                .read_to_string(&mut input)
                .map_err(|error| error.to_string())?;
            let observation = normalize(provider, kind, &input).map_err(|error| error.to_string())?;
            serde_json::to_string_pretty(&observation).map_err(|error| error.to_string())
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
