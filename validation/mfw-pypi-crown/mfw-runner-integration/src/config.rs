use crate::{digest::file_digest, Error, Result};
use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeMap, BTreeSet},
    env, fs,
    path::{Path, PathBuf},
};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum OutputMode {
    #[default]
    File,
    Stdout,
    None,
}

impl OutputMode {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::File => "file",
            Self::Stdout => "stdout",
            Self::None => "none",
        }
    }
}

/// Admitted semantic purpose of an external planning executable.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum EnginePurpose {
    ClassicalCandidate,
    TemporalCandidate,
    IndependentValidator,
}

impl EnginePurpose {
    pub fn for_role(role: &str) -> Result<Self> {
        match role {
            "classical" => Ok(Self::ClassicalCandidate),
            "temporal" => Ok(Self::TemporalCandidate),
            "validator" => Ok(Self::IndependentValidator),
            _ => Err(Error::InvalidEngineConfiguration(format!(
                "engine role `{role}` has no admitted purpose mapping"
            ))),
        }
    }

    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ClassicalCandidate => "classical_candidate",
            Self::TemporalCandidate => "temporal_candidate",
            Self::IndependentValidator => "independent_validator",
        }
    }

    #[must_use]
    pub const fn is_validator(self) -> bool {
        matches!(self, Self::IndependentValidator)
    }

    #[must_use]
    pub const fn required_placeholders(self, output_mode: OutputMode) -> &'static [&'static str] {
        match (self, output_mode) {
            (Self::ClassicalCandidate, OutputMode::File) => &["domain", "problem", "plan"],
            (Self::ClassicalCandidate | Self::TemporalCandidate, OutputMode::Stdout) => {
                &["domain", "problem"]
            }
            (Self::TemporalCandidate, OutputMode::File) => &["domain", "problem", "plan"],
            (Self::IndependentValidator, OutputMode::None) => &["domain", "problem", "plan"],
            _ => &[],
        }
    }

    #[must_use]
    pub const fn permits_output(self, output_mode: OutputMode) -> bool {
        match self {
            Self::ClassicalCandidate | Self::TemporalCandidate => {
                matches!(output_mode, OutputMode::File | OutputMode::Stdout)
            }
            Self::IndependentValidator => matches!(output_mode, OutputMode::None),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EngineConfig {
    pub program: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default)]
    pub version_args: Vec<String>,
    #[serde(default)]
    pub output_mode: OutputMode,
    #[serde(default = "default_success_codes")]
    pub success_codes: Vec<i32>,
}

fn default_success_codes() -> Vec<i32> {
    vec![0]
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(transparent)]
pub struct EnginesConfig(pub BTreeMap<String, EngineConfig>);

/// Canonical identity of an executable admitted for one semantic purpose.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExecutableIdentity {
    pub canonical_path: PathBuf,
    pub digest: String,
}

impl EnginesConfig {
    pub fn load(path: &Path) -> Result<Self> {
        let text = fs::read_to_string(path).map_err(|source| Error::Read {
            path: path.to_path_buf(),
            source,
        })?;
        let config: Self = toml::from_str(&text)?;
        config.validate()?;
        Ok(config)
    }

    pub fn get(&self, role: &str) -> Result<&EngineConfig> {
        self.0
            .get(role)
            .ok_or_else(|| Error::UnknownEngine(role.to_owned()))
    }

    /// Resolve and compare the actual candidate and validator artifacts.
    ///
    /// Different strings are insufficient evidence of independence: symlinks,
    /// aliases, and copied paths can still identify the same executable bytes.
    pub fn require_independent(&self, candidate_role: &str, validator_role: &str) -> Result<()> {
        let candidate_purpose = EnginePurpose::for_role(candidate_role)?;
        let validator_purpose = EnginePurpose::for_role(validator_role)?;
        if candidate_purpose.is_validator() || !validator_purpose.is_validator() {
            return Err(Error::EnginePurposeMismatch {
                role: format!("{candidate_role}->{validator_role}"),
                actual: candidate_purpose.as_str(),
                requested: "candidate_then_independent_validator",
            });
        }

        let candidate = executable_identity(&self.get(candidate_role)?.program)?;
        let validator = executable_identity(&self.get(validator_role)?.program)?;
        if candidate.canonical_path == validator.canonical_path
            || candidate.digest == validator.digest
        {
            return Err(Error::EngineBinaryNotIndependent {
                candidate_role: candidate_role.to_owned(),
                validator_role: validator_role.to_owned(),
                candidate_path: candidate.canonical_path,
                validator_path: validator.canonical_path,
                digest: candidate.digest,
            });
        }
        Ok(())
    }

    fn validate(&self) -> Result<()> {
        let mut validator_roles = Vec::new();
        let mut candidate_count = 0_usize;

        for (role, engine) in &self.0 {
            let purpose = EnginePurpose::for_role(role)?;
            validate_engine_contract(role, purpose, engine)?;
            if purpose.is_validator() {
                validator_roles.push((role, engine));
            } else {
                candidate_count += 1;
            }
        }

        if candidate_count == 0 {
            return Err(Error::InvalidEngineConfiguration(
                "no candidate engine is configured".to_owned(),
            ));
        }
        if validator_roles.len() != 1 {
            return Err(Error::InvalidEngineConfiguration(format!(
                "exactly one independent validator role is required; observed {}",
                validator_roles.len()
            )));
        }

        let (validator_role, validator) = validator_roles[0];
        for (candidate_role, candidate) in &self.0 {
            if EnginePurpose::for_role(candidate_role)?.is_validator() {
                continue;
            }
            if candidate.program == validator.program {
                return Err(Error::EngineNotIndependent {
                    candidate_role: candidate_role.clone(),
                    validator_role: validator_role.clone(),
                    program: candidate.program.clone(),
                });
            }
        }
        Ok(())
    }
}

fn validate_engine_contract(
    role: &str,
    purpose: EnginePurpose,
    engine: &EngineConfig,
) -> Result<()> {
    if engine.program.trim().is_empty() || engine.program.as_bytes().contains(&0) {
        return Err(Error::InvalidEngineConfiguration(format!(
            "engine role `{role}` has an empty or non-canonical program"
        )));
    }
    if !purpose.permits_output(engine.output_mode) {
        return Err(Error::InvalidEngineConfiguration(format!(
            "engine role `{role}` with purpose `{}` cannot use output_mode = `{}`",
            purpose.as_str(),
            engine.output_mode.as_str()
        )));
    }
    if engine.version_args.is_empty() {
        return Err(Error::MissingVersionArgs(role.to_owned()));
    }
    if engine
        .args
        .iter()
        .chain(engine.version_args.iter())
        .any(|argument| argument.is_empty() || argument.as_bytes().contains(&0))
    {
        return Err(Error::InvalidEngineConfiguration(format!(
            "engine role `{role}` contains an empty or NUL-bearing argument"
        )));
    }
    if engine.success_codes.is_empty() {
        return Err(Error::InvalidEngineConfiguration(format!(
            "engine role `{role}` declares no success codes"
        )));
    }
    let unique_codes = engine
        .success_codes
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    if unique_codes.len() != engine.success_codes.len() {
        return Err(Error::InvalidEngineConfiguration(format!(
            "engine role `{role}` repeats a success code"
        )));
    }

    let placeholders = argument_placeholders(&engine.args)?;
    for required in purpose.required_placeholders(engine.output_mode) {
        if !placeholders.contains(*required) {
            return Err(Error::InvalidEngineConfiguration(format!(
                "engine role `{role}` omits required placeholder `{{{required}}}`"
            )));
        }
    }
    Ok(())
}

fn argument_placeholders(arguments: &[String]) -> Result<BTreeSet<String>> {
    let mut output = BTreeSet::new();
    for argument in arguments {
        let mut remainder = argument.as_str();
        while let Some(open) = remainder.find('{') {
            let after_open = &remainder[open + 1..];
            let close = after_open
                .find('}')
                .ok_or_else(|| Error::UnterminatedPlaceholder(argument.clone()))?;
            let name = &after_open[..close];
            if name.is_empty()
                || !name
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
            {
                return Err(Error::InvalidEngineConfiguration(format!(
                    "argument `{argument}` contains non-canonical placeholder `{{{name}}}`"
                )));
            }
            output.insert(name.to_owned());
            remainder = &after_open[close + 1..];
        }
        if remainder.contains('}') {
            return Err(Error::InvalidEngineConfiguration(format!(
                "argument `{argument}` contains an unmatched closing brace"
            )));
        }
    }
    Ok(output)
}

/// Resolve a configured command to one canonical executable artifact and hash it.
pub fn executable_identity(program: &str) -> Result<ExecutableIdentity> {
    let configured = Path::new(program);
    let path = if configured.is_absolute() || configured.components().count() > 1 {
        configured.to_path_buf()
    } else {
        let search = env::var_os("PATH").ok_or_else(|| Error::ProgramUnresolved {
            program: program.to_owned(),
        })?;
        env::split_paths(&search)
            .map(|directory| directory.join(configured))
            .find(|candidate| candidate.is_file())
            .ok_or_else(|| Error::ProgramUnresolved {
                program: program.to_owned(),
            })?
    };
    let canonical_path = path.canonicalize().map_err(|_| Error::ProgramUnresolved {
        program: program.to_owned(),
    })?;
    let digest = file_digest(&canonical_path)?;
    Ok(ExecutableIdentity {
        canonical_path,
        digest,
    })
}
