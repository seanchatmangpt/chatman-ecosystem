use mfw_runner_validation::{
    config::{EngineConfig, EnginesConfig, OutputMode},
    model::{RunStatus, ValidationStatus},
    runner::{run_engine, RunRequest},
    Result,
};
use serde_json::json;
use std::{
    collections::BTreeMap,
    env, fs,
    path::{Path, PathBuf},
    time::Duration,
};

fn text(path: &Path) -> String {
    path.display().to_string()
}

fn placeholders(domain: &Path, problem: &Path, plan: &Path) -> BTreeMap<String, String> {
    BTreeMap::from([
        ("domain".to_owned(), text(domain)),
        ("problem".to_owned(), text(problem)),
        ("plan".to_owned(), text(plan)),
        ("python_engine".to_owned(), "pyperplan".to_owned()),
    ])
}

fn main() -> Result<()> {
    let mut args = env::args_os().skip(1);
    let domain = PathBuf::from(args.next().expect("domain path"));
    let problem = PathBuf::from(args.next().expect("problem path"));
    let output_root = PathBuf::from(args.next().expect("output directory"));
    let validator_program = PathBuf::from(args.next().expect("VAL executable"));
    assert!(args.next().is_none(), "unexpected arguments");

    let domain = domain.canonicalize().expect("canonical domain");
    let problem = problem.canonicalize().expect("canonical problem");
    let validator_program = validator_program.canonicalize().expect("canonical VAL");
    fs::create_dir_all(&output_root).expect("create output root");
    let output_root = output_root.canonicalize().expect("canonical output root");

    let candidate = EngineConfig {
        program: "mfw-pypi-planner".to_owned(),
        args: vec![
            "solve".to_owned(),
            "--domain".to_owned(),
            "{domain}".to_owned(),
            "--problem".to_owned(),
            "{problem}".to_owned(),
            "--plan".to_owned(),
            "{plan}".to_owned(),
            "--engine".to_owned(),
            "{python_engine}".to_owned(),
            "--mode".to_owned(),
            "classical".to_owned(),
            "--timeout".to_owned(),
            "30".to_owned(),
        ],
        version_args: vec!["--version".to_owned()],
        output_mode: OutputMode::File,
        success_codes: vec![0],
    };
    let validator = EngineConfig {
        program: text(&validator_program),
        args: vec![
            "-v".to_owned(),
            "-t".to_owned(),
            "0.001".to_owned(),
            "{domain}".to_owned(),
            "{problem}".to_owned(),
            "{plan}".to_owned(),
        ],
        version_args: vec!["-h".to_owned()],
        output_mode: OutputMode::None,
        success_codes: vec![0],
    };

    let engines = EnginesConfig(BTreeMap::from([
        ("classical".to_owned(), candidate.clone()),
        ("validator".to_owned(), validator.clone()),
    ]));
    engines.require_independent("classical", "validator")?;

    let candidate_run = output_root.join("candidate");
    let plan = candidate_run.join("candidate.plan");
    let candidate_receipt = run_engine(
        &candidate,
        &RunRequest {
            role: "classical".to_owned(),
            run_dir: candidate_run,
            placeholders: placeholders(&domain, &problem, &plan),
            timeout: Duration::from_secs(60),
            domain: Some(domain.clone()),
            problem: Some(problem.clone()),
            plan: Some(plan.clone()),
            validation: false,
        },
    )?;
    assert_eq!(candidate_receipt.status, RunStatus::Found);
    let plan_receipt = candidate_receipt.plan.as_ref().expect("candidate receipt");
    assert!(plan_receipt.size_bytes > 0);

    let validation_run = output_root.join("validator");
    let validator_receipt = run_engine(
        &validator,
        &RunRequest {
            role: "validator".to_owned(),
            run_dir: validation_run,
            placeholders: placeholders(&domain, &problem, &plan),
            timeout: Duration::from_secs(60),
            domain: Some(domain.clone()),
            problem: Some(problem.clone()),
            plan: Some(plan.clone()),
            validation: true,
        },
    )?;
    assert_eq!(validator_receipt.status, RunStatus::Completed);
    assert_eq!(validator_receipt.validation_status, Some(ValidationStatus::Valid));

    let receipt = json!({
        "schema": "urn:chatman:mfw-rust-python-val-integration:v1",
        "status": "ALIVE",
        "mfw_head_sha": "5e9b3c41c1f4aa6de9522828716ffe41e70b760b",
        "exact_runner_blobs": {
            "config.rs": "480f36f7a3b5a836cc95dc652a053eb6c5b9ccc1",
            "digest.rs": "0a62f4bdd90832a5de43ea5c4dc9605d788458d0",
            "error.rs": "0a6a244add4cdf20e5d4fd3745faea00bd1bf9b2",
            "model.rs": "b1c83c72d14eddb50c91444539b3e03096cafe07",
            "runner.rs": "92be66ad878a96859fa2523dc27b5f5fb71675a0",
            "template.rs": "d3179fbc2af462ac4fa237e6193a872c657356a0"
        },
        "candidate": candidate_receipt,
        "validator": validator_receipt,
        "plan_path": text(&plan),
        "validator_source": {
            "repository": "KCL-Planning/VAL",
            "commit": "3c7a1f330bdab0ba28a4762bb45c3f06c27fb6d4",
            "executable": text(&validator_program)
        }
    });
    let receipt_path = output_root.join("receipt-rust-python-val.json");
    fs::write(&receipt_path, serde_json::to_vec_pretty(&receipt)?)
        .expect("write integration receipt");
    println!("{}", serde_json::to_string(&receipt)?);
    Ok(())
}
