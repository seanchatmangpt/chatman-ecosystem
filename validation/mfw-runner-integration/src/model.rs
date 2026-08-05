use crate::config::EnginePurpose;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RunStatus {
    Found,
    Completed,
    NoCandidate,
    Bounded,
    ToolFailed,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ValidationStatus {
    Valid,
    Invalid,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactReceipt {
    pub path: String,
    pub digest: String,
    pub size_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessReceipt {
    pub program: String,
    pub argv: Vec<String>,
    pub exit_code: Option<i32>,
    pub timed_out: bool,
    pub elapsed_ms: u128,
    pub stdout_digest: String,
    pub stderr_digest: String,
    pub stdout_path: String,
    pub stderr_path: String,
}

/// Pre-spawn certificate binding one executable artifact to one semantic request.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineAdmissionReceipt {
    pub schema: String,
    pub role: String,
    pub purpose: EnginePurpose,
    pub canonical_program: String,
    pub executable_digest: String,
    pub contract_digest: String,
    pub request_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EngineRunReceipt {
    pub schema: String,
    pub engine_role: String,
    pub engine_version_output: Option<String>,
    pub admission: EngineAdmissionReceipt,
    pub status: RunStatus,
    pub validation_status: Option<ValidationStatus>,
    pub domain_digest: Option<String>,
    pub problem_digest: Option<String>,
    pub plan: Option<ArtifactReceipt>,
    pub process: ProcessReceipt,
}
