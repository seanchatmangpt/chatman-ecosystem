use chatman_ecosystem::run_gall;

fn main() {
    match run_gall() {
        Ok(report) => {
            if std::env::args().any(|argument| argument == "--json") {
                println!("{}", report.to_json());
            } else {
                for checkpoint in &report.checkpoints {
                    println!(
                        "{} {} {} {}",
                        checkpoint.id,
                        checkpoint.name,
                        checkpoint.standing,
                        checkpoint.receipt_hash
                    );
                }
                println!("{}", report.crown_line());
            }
            std::process::exit(report.exit_code());
        }
        Err(error) => {
            eprintln!("GALL_CROWN BUILD_BROKEN {error}");
            std::process::exit(1);
        }
    }
}
