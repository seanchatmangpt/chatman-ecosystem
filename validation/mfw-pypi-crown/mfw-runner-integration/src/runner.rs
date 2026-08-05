use crate::{
    config::{executable_identity, EngineConfig, EnginePurpose, OutputMode},
    digest::{bytes_digest, file_digest},
    model::{
        ArtifactReceipt, EngineAdmissionReceipt, EngineRunReceipt, ProcessReceipt, RunStatus,
        ValidationStatus,
    },
    template::expand,
    Error, Result,
};
use std::{
    collections::BTreeMap,
    fs::{self, File},
    path::{Path, PathBuf},
    process::{Command, Stdio},
    time::{Duration, Instant},
};
use wait_timeout::ChildExt;

#[derive(Debug, Clone)]
pub struct RunRequest {
    pub role: String,
    pub run_dir: PathBuf,
    pub placeholders: BTreeMap<String, String>,
    pub timeout: Duration,
    pub domain: Option<PathBuf>,
    pub problem: Option<PathBuf>,
    pub plan: Option<PathBuf>,
    pub validation: bool,
}

pub fn probe_engine(role: &str, engine: &EngineConfig, timeout: Duration) -> Result<String> {
    if engine.version_args.is_empty() {
        return Err(Error::MissingVersionArgs(role.to_owned()));
    }
    let identity = executable_identity(&engine.program)?;
    let output = Command::new(&identity.canonical_path)
        .args(&engine.version_args)
        .output()
        .map_err(|source| Error::Spawn {
            program: identity.canonical_path.display().to_string(),
            source,
        })?;
    let mut text = String::from_utf8_lossy(&output.stdout).trim().to_owned();
    if text.is_empty() {
        text = String::from_utf8_lossy(&output.stderr).trim().to_owned();
    }
    let _ = timeout;
    Ok(text)
}

pub fn run_engine(engine: &EngineConfig, req: &RunRequest) -> Result<EngineRunReceipt> {
    let purpose = EnginePurpose::for_role(&req.role)?;
    let requested = if req.validation {
        "independent_validation"
    } else {
        "candidate_generation"
    };
    if purpose.is_validator() != req.validation {
        return Err(Error::EnginePurposeMismatch {
            role: req.role.clone(),
            actual: purpose.as_str(),
            requested,
        });
    }
    if !purpose.permits_output(engine.output_mode) {
        return Err(Error::InvalidEngineConfiguration(format!(
            "engine role `{}` with purpose `{}` cannot use output mode `{}`",
            req.role,
            purpose.as_str(),
            engine.output_mode.as_str()
        )));
    }

    fs::create_dir_all(&req.run_dir).map_err(|source| Error::Write {
        path: req.run_dir.clone(),
        source,
    })?;
    let canonical_run_dir = req.run_dir.canonicalize().map_err(|source| Error::Read {
        path: req.run_dir.clone(),
        source,
    })?;

    for path in req.domain.iter().chain(req.problem.iter()) {
        if !path.exists() {
            return Err(Error::MissingPath(path.clone()));
        }
    }
    if engine.output_mode != OutputMode::None {
        let plan = req.plan.as_ref().ok_or_else(|| {
            Error::InvalidEngineConfiguration(format!(
                "candidate role `{}` has no plan output path",
                req.role
            ))
        })?;
        ensure_output_in_run_dir(plan, &canonical_run_dir)?;
    } else {
        let plan = req.plan.as_ref().ok_or_else(|| {
            Error::InvalidEngineConfiguration(format!(
                "validator role `{}` has no candidate-plan input",
                req.role
            ))
        })?;
        if !plan.exists() {
            return Err(Error::MissingPath(plan.clone()));
        }
    }

    let args = engine
        .args
        .iter()
        .map(|argument| expand(argument, &req.placeholders))
        .collect::<Result<Vec<_>>>()?;
    let admission = admit_engine(engine, req, purpose, &args)?;
    let canonical_program = PathBuf::from(&admission.canonical_program);

    let stdout_path = req.run_dir.join("stdout.log");
    let stderr_path = req.run_dir.join("stderr.log");
    let stdout_file = File::create(&stdout_path).map_err(|source| Error::Write {
        path: stdout_path.clone(),
        source,
    })?;
    let stderr_file = File::create(&stderr_path).map_err(|source| Error::Write {
        path: stderr_path.clone(),
        source,
    })?;

    let start = Instant::now();
    let mut child = Command::new(&canonical_program)
        .args(&args)
        .current_dir(&req.run_dir)
        .stdin(Stdio::null())
        .stdout(Stdio::from(stdout_file))
        .stderr(Stdio::from(stderr_file))
        .spawn()
        .map_err(|source| Error::Spawn {
            program: canonical_program.display().to_string(),
            source,
        })?;

    let waited = child
        .wait_timeout(req.timeout)
        .map_err(|source| Error::Wait {
            program: canonical_program.display().to_string(),
            source,
        })?;
    let (status, timed_out) = match waited {
        Some(status) => (status, false),
        None => {
            let _ = child.kill();
            let status = child.wait().map_err(|source| Error::Wait {
                program: canonical_program.display().to_string(),
                source,
            })?;
            (status, true)
        }
    };
    let elapsed_ms = start.elapsed().as_millis();
    let stdout = fs::read(&stdout_path).map_err(|source| Error::Read {
        path: stdout_path.clone(),
        source,
    })?;
    let stderr = fs::read(&stderr_path).map_err(|source| Error::Read {
        path: stderr_path.clone(),
        source,
    })?;

    if engine.output_mode == OutputMode::Stdout {
        let plan = req.plan.as_ref().ok_or_else(|| {
            Error::InvalidEngineConfiguration(format!(
                "stdout candidate role `{}` has no plan output path",
                req.role
            ))
        })?;
        fs::write(plan, &stdout).map_err(|source| Error::Write {
            path: plan.clone(),
            source,
        })?;
    }

    let plan_receipt = req
        .plan
        .as_ref()
        .and_then(|path| artifact_receipt(path).ok())
        .filter(|artifact| artifact.size_bytes > 0);
    let exit_code = status.code();
    let success = exit_code.is_some_and(|code| engine.success_codes.contains(&code));
    let run_status = if timed_out {
        RunStatus::Bounded
    } else if !success {
        RunStatus::ToolFailed
    } else if engine.output_mode == OutputMode::None {
        RunStatus::Completed
    } else if plan_receipt.is_none() {
        RunStatus::NoCandidate
    } else {
        RunStatus::Found
    };

    let validation_status = req
        .validation
        .then(|| classify_validation(&stdout, &stderr, success));
    let version = probe_engine(&req.role, engine, Duration::from_secs(5)).ok();

    Ok(EngineRunReceipt {
        schema: "urn:mfw:planning-engine-run:v2".to_owned(),
        engine_role: req.role.clone(),
        engine_version_output: version,
        admission,
        status: run_status,
        validation_status,
        domain_digest: req.domain.as_deref().map(file_digest).transpose()?,
        problem_digest: req.problem.as_deref().map(file_digest).transpose()?,
        plan: plan_receipt,
        process: ProcessReceipt {
            program: canonical_program.display().to_string(),
            argv: args,
            exit_code,
            timed_out,
            elapsed_ms,
            stdout_digest: bytes_digest(&stdout),
            stderr_digest: bytes_digest(&stderr),
            stdout_path: stdout_path.display().to_string(),
            stderr_path: stderr_path.display().to_string(),
        },
    })
}

fn admit_engine(
    engine: &EngineConfig,
    req: &RunRequest,
    purpose: EnginePurpose,
    expanded_args: &[String],
) -> Result<EngineAdmissionReceipt> {
    let identity = executable_identity(&engine.program)?;
    let mut contract = blake3::Hasher::new();
    commit_field(&mut contract, req.role.as_bytes());
    commit_field(&mut contract, purpose.as_str().as_bytes());
    commit_field(
        &mut contract,
        identity.canonical_path.to_string_lossy().as_bytes(),
    );
    commit_field(&mut contract, identity.digest.as_bytes());
    commit_field(&mut contract, engine.output_mode.as_str().as_bytes());
    for argument in &engine.args {
        commit_field(&mut contract, argument.as_bytes());
    }
    for argument in &engine.version_args {
        commit_field(&mut contract, argument.as_bytes());
    }
    for code in &engine.success_codes {
        commit_field(&mut contract, &code.to_le_bytes());
    }
    let contract_digest = contract.finalize().to_hex().to_string();

    let mut request = blake3::Hasher::new();
    commit_field(&mut request, contract_digest.as_bytes());
    commit_field(&mut request, &req.timeout.as_millis().to_le_bytes());
    commit_field(&mut request, &[u8::from(req.validation)]);
    for argument in expanded_args {
        commit_field(&mut request, argument.as_bytes());
    }
    for path in [&req.domain, &req.problem] {
        match path.as_deref() {
            Some(path) => commit_field(&mut request, file_digest(path)?.as_bytes()),
            None => commit_field(&mut request, b"none"),
        }
    }
    if req.validation {
        match req.plan.as_deref() {
            Some(path) => commit_field(&mut request, file_digest(path)?.as_bytes()),
            None => commit_field(&mut request, b"none"),
        }
    } else {
        commit_field(&mut request, b"candidate-output-not-yet-materialized");
    }
    let request_digest = request.finalize().to_hex().to_string();

    Ok(EngineAdmissionReceipt {
        schema: "urn:mfw:planning-engine-admission:v1".to_owned(),
        role: req.role.clone(),
        purpose,
        canonical_program: identity.canonical_path.display().to_string(),
        executable_digest: identity.digest,
        contract_digest,
        request_digest,
    })
}

fn commit_field(hasher: &mut blake3::Hasher, bytes: &[u8]) {
    hasher.update(&(bytes.len() as u64).to_le_bytes());
    hasher.update(bytes);
}

fn ensure_output_in_run_dir(path: &Path, canonical_run_dir: &Path) -> Result<()> {
    let parent = path.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent).map_err(|source| Error::Write {
        path: parent.to_path_buf(),
        source,
    })?;
    let parent = parent.canonicalize().map_err(|source| Error::Read {
        path: parent.to_path_buf(),
        source,
    })?;
    if !parent.starts_with(canonical_run_dir) {
        return Err(Error::OutputEscapesRunDir(path.to_path_buf()));
    }
    Ok(())
}

fn artifact_receipt(path: &Path) -> Result<ArtifactReceipt> {
    let metadata = fs::metadata(path).map_err(|source| Error::Read {
        path: path.to_path_buf(),
        source,
    })?;
    Ok(ArtifactReceipt {
        path: path.display().to_string(),
        digest: file_digest(path)?,
        size_bytes: metadata.len(),
    })
}

fn classify_validation(stdout: &[u8], stderr: &[u8], success: bool) -> ValidationStatus {
    let text = format!(
        "{}\n{}",
        String::from_utf8_lossy(stdout),
        String::from_utf8_lossy(stderr)
    )
    .to_ascii_lowercase();
    if text.contains("plan valid") || text.contains("successful plans: 1") {
        ValidationStatus::Valid
    } else if text.contains("plan invalid") || text.contains("failed plans: 1") || !success {
        ValidationStatus::Invalid
    } else {
        ValidationStatus::Unknown
    }
}
