use std::path::PathBuf;

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("failed to read {path}: {source}")]
    Read {
        path: PathBuf,
        source: std::io::Error,
    },
    #[error("failed to write {path}: {source}")]
    Write {
        path: PathBuf,
        source: std::io::Error,
    },
    #[error("invalid TOML configuration: {0}")]
    Toml(#[from] toml::de::Error),
    #[error("JSON serialization failed: {0}")]
    Json(#[from] serde_json::Error),
    #[error("engine role `{0}` is not configured")]
    UnknownEngine(String),
    #[error("invalid engine configuration: {0}")]
    InvalidEngineConfiguration(String),
    #[error("configured engine program cannot be resolved to one executable artifact: {program}")]
    ProgramUnresolved { program: String },
    #[error(
        "candidate engine `{candidate_role}` and validator `{validator_role}` name the same configured program `{program}`"
    )]
    EngineNotIndependent {
        candidate_role: String,
        validator_role: String,
        program: String,
    },
    #[error(
        "candidate engine `{candidate_role}` and validator `{validator_role}` are not artifact-independent: candidate={candidate_path:?}, validator={validator_path:?}, digest={digest}"
    )]
    EngineBinaryNotIndependent {
        candidate_role: String,
        validator_role: String,
        candidate_path: PathBuf,
        validator_path: PathBuf,
        digest: String,
    },
    #[error("engine role `{role}` has purpose `{actual}` but was invoked for `{requested}`")]
    EnginePurposeMismatch {
        role: String,
        actual: &'static str,
        requested: &'static str,
    },
    #[error("unknown placeholder `{{{0}}}`")]
    UnknownPlaceholder(String),
    #[error("unterminated placeholder in argument `{0}`")]
    UnterminatedPlaceholder(String),
    #[error("required path does not exist: {0}")]
    MissingPath(PathBuf),
    #[error("output path escapes run directory: {0}")]
    OutputEscapesRunDir(PathBuf),
    #[error("failed to spawn `{program}`: {source}")]
    Spawn {
        program: String,
        source: std::io::Error,
    },
    #[error("failed while waiting for `{program}`: {source}")]
    Wait {
        program: String,
        source: std::io::Error,
    },
    #[error("engine has no version_args: {0}")]
    MissingVersionArgs(String),
    #[error("malformed plan: {0}")]
    MalformedPlan(String),
    #[error("invalid POWL 2 model: {0}")]
    InvalidPowl(String),
    #[error("failed to parse RDF graph {path}: {message}")]
    RdfParse { path: PathBuf, message: String },
    #[error("SHACL_REFUSED for {what}: {findings}")]
    ShaclRefused { what: String, findings: String },
    #[error("UNSUPPORTED: {0}")]
    CapabilityUnsupported(String),
    #[error("INCONSISTENT: {0}")]
    Inconsistent(String),
    #[error("SEMANTIC_PRESERVATION_UNSUPPORTED: {0}")]
    PreservationRefused(String),
    #[error("graph machinery failure: {0}")]
    Canon(String),
}

pub type Result<T> = std::result::Result<T, Error>;
