//! Qualification harness (chatman-ecosystem-release-pack qualify.sh step 7h/7i): the `receipt seal` /
//! `receipt verify-all` arms of chatman-ecosystem apps/ecosystem-cli/src/main.rs at c59596f5, calling
//! the same ecosystem-core functions (seal_all_receipts, verify_all_receipts) and printing the same
//! RECEIPTS_SEALED / RECEIPTS_ALIVE lines, without the CLI's deploy/MCP dependency tree. The receipt law
//! it executes is ecosystem-core's own code, extracted byte-for-byte from that commit by qualify.sh.
use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let root = match std::env::current_dir() {
        Ok(root) => root,
        Err(e) => {
            eprintln!("current directory unreadable: {e}");
            return ExitCode::from(2);
        }
    };
    let out = match args.iter().map(String::as_str).collect::<Vec<_>>().as_slice() {
        ["receipt", "seal"] => ecosystem_core::seal_all_receipts(&root).map(|n| format!("RECEIPTS_SEALED count={n}")),
        ["receipt", "verify-all"] => ecosystem_core::verify_all_receipts(&root).map(|n| format!("RECEIPTS_ALIVE count={n}")),
        _ => {
            eprintln!("usage: receipt seal|verify-all");
            return ExitCode::from(2);
        }
    };
    match out {
        Ok(line) => {
            println!("{line}");
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("{e}");
            ExitCode::FAILURE
        }
    }
}
