//! Framework-free constitutional core for the Chatman Ecosystem.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

pub const REQUIRED_RAILS: &[&str] = &[
    "constitutional_core",
    "catalog",
    "authority",
    "evidence",
    "receipts",
    "projection",
    "cli",
    "architecture_gates",
    "ci_admission",
    "cache_policy",
    "artifact_transfer",
    "storage_memory",
    "storage_sqlx",
    "governor_runtime",
    "mcp_boundary",
    "connector_boundary",
    "github_connector",
    "document_connector",
    "gall_checkpoints",
    "release_admission",
];
pub const REQUIRED_ADMISSION_GATES: &[&str] = &[
    "format",
    "clippy",
    "tests",
    "rustdoc",
    "dependency_policy",
    "catalog",
    "receipts",
    "projection",
    "architecture",
    "storage_differential",
    "cold_cache",
    "github_read",
    "artifact_transfer",
];

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("invalid identifier `{0}`")]
    InvalidId(String),
    #[error("invalid subject `{0}`")]
    InvalidSubject(String),
    #[error("illegal transition {0:?} -> {1:?}")]
    IllegalTransition(Standing, Standing),
    #[error("authority denied: have {0:?}, require {1:?}")]
    AuthorityDenied(Authority, Authority),
    #[error("I/O at {0}: {1}")]
    Io(String, String),
    #[error("TOML at {0}: {1}")]
    Toml(String, String),
    #[error("catalog: {0}")]
    Catalog(String),
    #[error("receipt: {0}")]
    Receipt(String),
    #[error("projection drift: {0}")]
    Projection(String),
    #[error("architecture: {0}")]
    Architecture(String),
}

fn read(path: &Path) -> Result<String, Error> {
    fs::read_to_string(path).map_err(|e| Error::Io(path.display().to_string(), e.to_string()))
}

fn atomic_write(path: &Path, text: &str) -> Result<(), Error> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| Error::Io(parent.display().to_string(), e.to_string()))?;
    }
    let temp = path.with_extension("tmp");
    fs::write(&temp, text).map_err(|e| Error::Io(temp.display().to_string(), e.to_string()))?;
    fs::rename(&temp, path).map_err(|e| Error::Io(path.display().to_string(), e.to_string()))
}

fn valid_id(value: &str, prefix: &str) -> bool {
    let expected = format!("{prefix}:");
    value.strip_prefix(&expected).is_some_and(|suffix| {
        !suffix.is_empty()
            && suffix
                .chars()
                .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-' || c == '_')
    })
}

macro_rules! id_type {
    ($name:ident, $prefix:literal) => {
        #[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
        #[serde(transparent)]
        pub struct $name(pub String);
        impl $name {
            pub fn parse(value: impl Into<String>) -> Result<Self, Error> {
                let value = value.into();
                if valid_id(&value, $prefix) {
                    Ok(Self(value))
                } else {
                    Err(Error::InvalidId(value))
                }
            }
        }
    };
}

id_type!(ProjectId, "project");
id_type!(ProgramId, "program");
id_type!(RepositoryId, "repository");
id_type!(DocumentId, "document");
id_type!(AutomationId, "automation");
id_type!(GovernorId, "governor");
id_type!(ReceiptId, "receipt");
id_type!(EvidenceId, "evidence");
id_type!(TransitionId, "transition");
id_type!(AuthorityId, "authority");
id_type!(ConnectorId, "connector");

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ExactSubject {
    SelfHead,
    GitCommit {
        repository: RepositoryId,
        sha: String,
    },
    File {
        path: String,
        blake3: String,
    },
    DocumentRevision {
        document: DocumentId,
        revision: String,
        blake3: String,
    },
    ExternalArtifact {
        uri: String,
        digest: String,
    },
}

fn valid_digest(value: &str) -> bool {
    value
        .strip_prefix("blake3:")
        .is_some_and(|hex| hex.len() == 64 && hex.chars().all(|c| c.is_ascii_hexdigit()))
}

impl ExactSubject {
    pub fn validate(&self) -> Result<(), Error> {
        match self {
            Self::SelfHead => Ok(()),
            Self::GitCommit { sha, .. }
                if sha.len() == 40 && sha.chars().all(|c| c.is_ascii_hexdigit()) =>
            {
                Ok(())
            }
            Self::File { path, blake3 }
                if !path.is_empty()
                    && !path.starts_with('/')
                    && !path.contains("..")
                    && valid_digest(blake3) =>
            {
                Ok(())
            }
            Self::DocumentRevision {
                revision, blake3, ..
            } if !revision.trim().is_empty() && valid_digest(blake3) => Ok(()),
            Self::ExternalArtifact { uri, digest }
                if (uri.starts_with("https://") || uri.starts_with("urn:"))
                    && valid_digest(digest) =>
            {
                Ok(())
            }
            _ => Err(Error::InvalidSubject(format!("{self:?}"))),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Standing {
    Unknown,
    Observed,
    Candidate,
    PartialAlive,
    Alive,
    Blocked,
    Unsupported,
    Rejected,
    Superseded,
}

impl Standing {
    pub fn permits(self, next: Self) -> bool {
        self == next
            || matches!(
                (self, next),
                (Self::Unknown, Self::Observed | Self::Rejected)
                    | (
                        Self::Observed,
                        Self::Candidate | Self::Unsupported | Self::Rejected
                    )
                    | (
                        Self::Candidate,
                        Self::PartialAlive | Self::Blocked | Self::Rejected
                    )
                    | (
                        Self::PartialAlive,
                        Self::Alive | Self::Blocked | Self::Rejected
                    )
                    | (
                        Self::Blocked,
                        Self::Candidate | Self::PartialAlive | Self::Rejected
                    )
                    | (Self::Alive, Self::Superseded | Self::Blocked)
                    | (Self::Superseded, Self::Observed)
            )
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Authority {
    Observe,
    Classify,
    Draft,
    PersistControlPlane,
    OpenDraftPullRequest,
    ModifyExternalObject,
    Communicate,
    Merge,
    Delete,
    Spend,
    Approve,
    Release,
}

impl Authority {
    pub fn permits(self, required: Self) -> bool {
        self == required
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transition {
    pub id: TransitionId,
    pub subject: ExactSubject,
    pub from: Standing,
    pub to: Standing,
    pub authority: Authority,
    pub evidence: Vec<EvidenceId>,
    #[serde(default)]
    pub exclusions: Vec<String>,
    pub occurred_at: String,
}

impl Transition {
    pub fn validate(&self, required: Authority) -> Result<(), Error> {
        self.subject.validate()?;
        if !self.from.permits(self.to) {
            return Err(Error::IllegalTransition(self.from, self.to));
        }
        if !self.authority.permits(required) {
            return Err(Error::AuthorityDenied(self.authority, required));
        }
        if matches!(self.to, Standing::PartialAlive | Standing::Alive) && self.evidence.is_empty() {
            return Err(Error::Catalog(
                "standing advancement requires evidence".into(),
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Deserialize)]
pub struct EcosystemManifest {
    pub ecosystem: EcosystemInfo,
}
#[derive(Debug, Clone, Deserialize)]
pub struct EcosystemInfo {
    pub id: String,
    pub name: String,
    pub version: String,
    pub subject: String,
}
#[derive(Debug, Clone, Deserialize)]
pub struct RailsManifest {
    pub rail: Vec<Rail>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rail {
    pub id: String,
    pub standing: Standing,
    pub subject: String,
    pub evidence: Vec<String>,
}
#[derive(Debug, Clone, Deserialize)]
pub struct RepositoriesManifest {
    #[serde(default)]
    pub repository: Vec<Repository>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Repository {
    pub id: String,
    pub name: String,
    pub url: String,
    pub role: String,
    pub standing: Standing,
}
#[derive(Debug, Clone, Deserialize)]
pub struct DocumentsManifest {
    #[serde(default)]
    pub document: Vec<Document>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub id: String,
    pub title: String,
    pub path: String,
    pub canonical: bool,
}
#[derive(Debug, Clone, Deserialize)]
pub struct AutomationsManifest {
    #[serde(default)]
    pub automation: Vec<Automation>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Automation {
    pub id: String,
    pub title: String,
    pub mode: String,
    pub authority: Vec<Authority>,
}

#[derive(Debug, Clone)]
pub struct Catalog {
    pub ecosystem: EcosystemManifest,
    pub rails: RailsManifest,
    pub repositories: RepositoriesManifest,
    pub documents: DocumentsManifest,
    pub automations: AutomationsManifest,
}

fn load_toml<T: for<'a> Deserialize<'a>>(path: &Path) -> Result<T, Error> {
    toml::from_str(&read(path)?).map_err(|e| Error::Toml(path.display().to_string(), e.to_string()))
}

fn unique<'a>(values: impl Iterator<Item = &'a str>, kind: &str) -> Result<(), Error> {
    let mut seen = BTreeSet::new();
    for value in values {
        if !seen.insert(value) {
            return Err(Error::Catalog(format!("duplicate {kind} `{value}`")));
        }
    }
    Ok(())
}

impl Catalog {
    pub fn load(root: &Path) -> Result<Self, Error> {
        let dir = root.join("catalog");
        Ok(Self {
            ecosystem: load_toml(&dir.join("ecosystem.toml"))?,
            rails: load_toml(&dir.join("rails.toml"))?,
            repositories: load_toml(&dir.join("repositories.toml"))?,
            documents: load_toml(&dir.join("documents.toml"))?,
            automations: load_toml(&dir.join("automations.toml"))?,
        })
    }

    pub fn validate(&self, root: &Path) -> Result<(), Error> {
        if self.ecosystem.ecosystem.id != "ecosystem:chatman" {
            return Err(Error::Catalog("wrong ecosystem id".into()));
        }
        unique(self.rails.rail.iter().map(|x| x.id.as_str()), "rail")?;
        unique(
            self.repositories.repository.iter().map(|x| x.id.as_str()),
            "repository",
        )?;
        unique(
            self.documents.document.iter().map(|x| x.id.as_str()),
            "document",
        )?;
        unique(
            self.automations.automation.iter().map(|x| x.id.as_str()),
            "automation",
        )?;
        let subjects = self
            .rails
            .rail
            .iter()
            .map(|x| x.subject.as_str())
            .collect::<BTreeSet<_>>();
        if subjects != BTreeSet::from(["SELF"]) {
            return Err(Error::Catalog("rails must share SELF subject".into()));
        }
        for required in REQUIRED_RAILS {
            if !self.rails.rail.iter().any(|x| x.id == *required) {
                return Err(Error::Catalog(format!("missing rail `{required}`")));
            }
        }
        for rail in &self.rails.rail {
            if rail.evidence.is_empty() {
                return Err(Error::Catalog(format!("rail `{}` lacks evidence", rail.id)));
            }
            for path in &rail.evidence {
                if !root.join(path).exists() {
                    return Err(Error::Catalog(format!("missing evidence `{path}`")));
                }
            }
        }
        for repository in &self.repositories.repository {
            if !valid_id(&repository.id, "repository")
                || !repository.url.starts_with("https://github.com/")
            {
                return Err(Error::Catalog(format!(
                    "invalid repository `{}`",
                    repository.id
                )));
            }
        }
        for document in &self.documents.document {
            if !valid_id(&document.id, "document") || !root.join(&document.path).exists() {
                return Err(Error::Catalog(format!(
                    "invalid document `{}`",
                    document.id
                )));
            }
        }
        for automation in &self.automations.automation {
            if !valid_id(&automation.id, "automation") {
                return Err(Error::Catalog(format!(
                    "invalid automation `{}`",
                    automation.id
                )));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Receipt {
    pub id: ReceiptId,
    pub subject: String,
    pub actor: String,
    pub authority: Authority,
    pub intention: String,
    pub observed: Vec<String>,
    pub executed: Vec<String>,
    pub changed: Vec<String>,
    pub verified: Vec<String>,
    #[serde(default)]
    pub excluded: Vec<String>,
    pub replay: Vec<String>,
    pub standing_before: Standing,
    pub standing_after: Standing,
    pub timestamp: String,
    pub digest: String,
}

impl Receipt {
    fn unsigned(&self) -> Result<String, Error> {
        let mut copy = self.clone();
        copy.digest.clear();
        toml::to_string(&copy).map_err(|e| Error::Receipt(e.to_string()))
    }
    pub fn calculate_digest(&self) -> Result<String, Error> {
        Ok(format!(
            "blake3:{}",
            blake3::hash(self.unsigned()?.as_bytes()).to_hex()
        ))
    }
    pub fn sign(&mut self) -> Result<(), Error> {
        self.digest = self.calculate_digest()?;
        Ok(())
    }
    pub fn verify(&self) -> Result<(), Error> {
        if !valid_id(&self.id.0, "receipt") {
            return Err(Error::Receipt(format!(
                "invalid receipt id `{}`",
                self.id.0
            )));
        }
        if self.subject.trim().is_empty()
            || self.actor.trim().is_empty()
            || self.intention.trim().is_empty()
            || self.verified.is_empty()
            || self.replay.is_empty()
            || self.timestamp.trim().is_empty()
        {
            return Err(Error::Receipt("incomplete receipt".into()));
        }
        if !self.standing_before.permits(self.standing_after) {
            return Err(Error::Receipt(format!(
                "illegal receipt transition {:?} -> {:?}",
                self.standing_before, self.standing_after
            )));
        }
        if !valid_digest(&self.digest) || self.digest != self.calculate_digest()? {
            return Err(Error::Receipt(format!("digest mismatch for {:?}", self.id)));
        }
        Ok(())
    }
}

pub fn verify_all_receipts(root: &Path) -> Result<usize, Error> {
    let dir = root.join("receipts");
    let entries =
        fs::read_dir(&dir).map_err(|e| Error::Io(dir.display().to_string(), e.to_string()))?;
    let mut paths = entries
        .filter_map(Result::ok)
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|x| x.to_str()) == Some("toml"))
        .collect::<Vec<_>>();
    paths.sort();
    if paths.is_empty() {
        return Err(Error::Receipt("no receipts".into()));
    }
    for path in &paths {
        let mut receipt: Receipt = load_toml(path)?;
        if receipt.digest.is_empty() {
            receipt.sign()?;
            let name = path
                .file_name()
                .ok_or_else(|| Error::Receipt("missing receipt filename".into()))?;
            let target = root.join("target/crown/receipts").join(name);
            atomic_write(
                &target,
                &toml::to_string_pretty(&receipt).map_err(|e| Error::Receipt(e.to_string()))?,
            )?;
        }
        receipt.verify()?;
    }
    Ok(paths.len())
}

pub fn render_standing(catalog: &Catalog) -> String {
    let mut rails = catalog.rails.rail.clone();
    rails.sort_by(|a, b| a.id.cmp(&b.id));
    let mut out = String::from(
        "# Chatman Ecosystem Standing\n\n> Generated from `catalog/rails.toml`. Do not edit manually.\n\n| Rail | Standing | Subject | Evidence |\n|---|---|---|---|\n",
    );
    for rail in rails {
        out.push_str(&format!(
            "| `{}` | `{:?}` | `{}` | {} |\n",
            rail.id,
            rail.standing,
            rail.subject,
            rail.evidence.join("<br>")
        ));
    }
    out
}

pub fn render_portfolio(catalog: &Catalog) -> String {
    let mut repositories = catalog.repositories.repository.clone();
    repositories.sort_by(|a, b| a.id.cmp(&b.id));
    let mut documents = catalog.documents.document.clone();
    documents.sort_by(|a, b| a.id.cmp(&b.id));
    let mut out = format!(
        "# {} Portfolio\n\nVersion: `{}`\n\n## Repositories\n\n| Repository | Role | Standing |\n|---|---|---|\n",
        catalog.ecosystem.ecosystem.name, catalog.ecosystem.ecosystem.version
    );
    for item in repositories {
        out.push_str(&format!(
            "| `{}` | {} | `{:?}` |\n",
            item.id, item.role, item.standing
        ));
    }
    out.push_str("\n## Documents\n\n| Document | Path | Canonical |\n|---|---|---|\n");
    for item in documents {
        out.push_str(&format!(
            "| `{}` | `{}` | {} |\n",
            item.id, item.path, item.canonical
        ));
    }
    out
}

pub fn render_all(root: &Path) -> Result<BTreeMap<PathBuf, String>, Error> {
    let catalog = Catalog::load(root)?;
    catalog.validate(root)?;
    Ok(BTreeMap::from([
        (
            root.join("views/generated/standing.md"),
            render_standing(&catalog),
        ),
        (
            root.join("views/generated/portfolio.md"),
            render_portfolio(&catalog),
        ),
    ]))
}

pub fn write_projections(root: &Path) -> Result<usize, Error> {
    let rendered = render_all(root)?;
    for (path, text) in &rendered {
        atomic_write(path, text)?;
    }
    Ok(rendered.len())
}

pub fn check_projections(root: &Path) -> Result<usize, Error> {
    let rendered = render_all(root)?;
    for (path, expected) in &rendered {
        if read(path)? != *expected {
            return Err(Error::Projection(path.display().to_string()));
        }
    }
    Ok(rendered.len())
}

fn check_core_manifest(core: &str) -> Result<(), Error> {
    for forbidden in ["tokio", "sqlx", "axum", "tower", "reqwest", "rmcp"] {
        if core.lines().any(|line| {
            let line = line.trim_start();
            line.starts_with(&format!("{forbidden} "))
                || line.starts_with(&format!("{forbidden}="))
                || line.starts_with(&format!("{forbidden}."))
        }) {
            return Err(Error::Architecture(format!(
                "core depends on `{forbidden}`"
            )));
        }
    }
    Ok(())
}

pub fn check_architecture(root: &Path) -> Result<(), Error> {
    let core = read(&root.join("crates/ecosystem-core/Cargo.toml"))?;
    check_core_manifest(&core)?;
    let workspace = read(&root.join("Cargo.toml"))?;
    for member in [
        "crates/ecosystem-core",
        "crates/ecosystem-runtime",
        "apps/ecosystem-cli",
    ] {
        if !workspace.contains(member) {
            return Err(Error::Architecture(format!("workspace omits `{member}`")));
        }
    }
    Ok(())
}

#[derive(Debug, Clone, Deserialize)]
struct AdmissionEvidence {
    subject: String,
    gates: Vec<String>,
}

fn verify_admission(root: &Path, subject: &str) -> Result<(), Error> {
    let path = root.join("target/crown/admission.json");
    let evidence: AdmissionEvidence = serde_json::from_str(&read(&path)?)
        .map_err(|error| Error::Catalog(format!("invalid admission evidence: {error}")))?;
    if evidence.subject != subject {
        return Err(Error::Catalog(format!(
            "admission subject `{}` does not match Crown subject `{subject}`",
            evidence.subject
        )));
    }
    unique(evidence.gates.iter().map(String::as_str), "admission gate")?;
    for required in REQUIRED_ADMISSION_GATES {
        if !evidence.gates.iter().any(|gate| gate == required) {
            return Err(Error::Catalog(format!(
                "missing admission gate `{required}`"
            )));
        }
    }
    Ok(())
}

#[derive(Debug, Clone, Serialize)]
pub struct CrownReport {
    pub subject: String,
    pub rails: Vec<Rail>,
    pub standing: Standing,
}

impl CrownReport {
    pub fn evaluate(root: &Path, subject: impl Into<String>) -> Result<Self, Error> {
        let subject = subject.into();
        let sha = subject
            .strip_prefix("git:")
            .ok_or_else(|| Error::Catalog("Crown subject must be a git SHA".into()))?;
        if sha.len() != 40 || !sha.chars().all(|c| c.is_ascii_hexdigit()) {
            return Err(Error::Catalog(format!("invalid Crown subject `{subject}`")));
        }
        let catalog = Catalog::load(root)?;
        catalog.validate(root)?;
        verify_all_receipts(root)?;
        check_projections(root)?;
        check_architecture(root)?;
        verify_admission(root, &subject)?;
        let all_alive = catalog
            .rails
            .rail
            .iter()
            .all(|x| x.standing == Standing::Alive)
            && REQUIRED_RAILS
                .iter()
                .all(|required| catalog.rails.rail.iter().any(|x| x.id == *required));
        let rails = catalog
            .rails
            .rail
            .into_iter()
            .map(|mut rail| {
                rail.subject = subject.clone();
                rail
            })
            .collect();
        Ok(Self {
            subject,
            rails,
            standing: if all_alive {
                Standing::Alive
            } else {
                Standing::PartialAlive
            },
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identities_and_subjects_fail_closed() -> Result<(), Error> {
        assert!(ProjectId::parse("project:lsp-max").is_ok());
        assert!(ProjectId::parse("project:LSP Max").is_err());
        let repository = RepositoryId::parse("repository:chatman-ecosystem")?;
        assert!(
            ExactSubject::GitCommit {
                repository,
                sha: "bad".into()
            }
            .validate()
            .is_err()
        );
        assert!(
            ExactSubject::File {
                path: "../secret".into(),
                blake3: format!("blake3:{}", "0".repeat(64))
            }
            .validate()
            .is_err()
        );
        Ok(())
    }

    #[test]
    fn standing_and_authority_are_bounded() {
        assert!(Standing::PartialAlive.permits(Standing::Alive));
        assert!(!Standing::Unknown.permits(Standing::Alive));
        assert!(Authority::Merge.permits(Authority::Merge));
        assert!(!Authority::Release.permits(Authority::Merge));
    }

    #[test]
    fn architecture_gate_proves_it_can_fail() {
        assert!(check_core_manifest("[dependencies]\ntokio = \"1\"\n").is_err());
        assert!(check_core_manifest("[dependencies]\nserde = \"1\"\n").is_ok());
    }

    #[test]
    fn crown_rejects_non_exact_subjects() {
        assert!(CrownReport::evaluate(Path::new("."), "git:UNKNOWN").is_err());
    }
    #[test]
    fn receipt_tampering_is_detected() -> Result<(), Error> {
        let mut receipt = Receipt {
            id: ReceiptId::parse("receipt:test")?,
            subject: "SELF".into(),
            actor: "test".into(),
            authority: Authority::Observe,
            intention: "verify".into(),
            observed: vec!["input".into()],
            executed: vec!["test".into()],
            changed: vec![],
            verified: vec!["result".into()],
            excluded: vec![],
            replay: vec!["cargo test".into()],
            standing_before: Standing::Candidate,
            standing_after: Standing::Alive,
            timestamp: "2026-08-05T00:00:00Z".into(),
            digest: String::new(),
        };
        receipt.sign()?;
        receipt.verify()?;
        receipt.intention = "tampered".into();
        assert!(receipt.verify().is_err());
        Ok(())
    }
}
