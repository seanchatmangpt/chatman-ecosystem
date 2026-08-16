//! Gall-sequenced execution capsule for Chatman ecosystem phases 0 through 3.
//!
//! The crate is intentionally dependency-free. It proves a bounded local system:
//! source admission, exclusive broker actuation, channel/session routing, and a
//! capability-fenced WebAssembly skill path.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt::{Display, Formatter};

const ECOSYSTEM_LOCK: &str = include_str!("../../../ecosystem.lock");

/// Exact standing vocabulary used by every checkpoint.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Standing {
    Unknown,
    PartialAlive,
    Alive,
    Blocked,
    BuildBroken,
    Unsupported,
    Refused,
}

impl Display for Standing {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        let value = match self {
            Self::Unknown => "UNKNOWN",
            Self::PartialAlive => "PARTIAL_ALIVE",
            Self::Alive => "ALIVE",
            Self::Blocked => "BLOCKED",
            Self::BuildBroken => "BUILD_BROKEN",
            Self::Unsupported => "UNSUPPORTED",
            Self::Refused => "REFUSED",
        };
        formatter.write_str(value)
    }
}

/// Typed refusal classes. Refusal is distinct from unsupported or blocked.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Refusal {
    InvalidSourcePin,
    DuplicateSource,
    AuthorityMultiplicity,
    AuthorityOwnerMismatch,
    SubjectUnknown,
    SubjectRevoked,
    CapabilityDenied,
    PolicyDigestMismatch,
    ActionDigestMismatch,
    ImportNotDeclared,
    UnsupportedWasm,
    ModuleDigestMismatch,
    FuelExceeded,
    MalformedWasm,
}

impl Display for Refusal {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        let value = match self {
            Self::InvalidSourcePin => "INVALID_SOURCE_PIN",
            Self::DuplicateSource => "DUPLICATE_SOURCE",
            Self::AuthorityMultiplicity => "AUTHORITY_MULTIPLICITY",
            Self::AuthorityOwnerMismatch => "AUTHORITY_OWNER_MISMATCH",
            Self::SubjectUnknown => "SUBJECT_UNKNOWN",
            Self::SubjectRevoked => "SUBJECT_REVOKED",
            Self::CapabilityDenied => "CAPABILITY_DENIED",
            Self::PolicyDigestMismatch => "POLICY_DIGEST_MISMATCH",
            Self::ActionDigestMismatch => "ACTION_DIGEST_MISMATCH",
            Self::ImportNotDeclared => "IMPORT_NOT_DECLARED",
            Self::UnsupportedWasm => "UNSUPPORTED_WASM",
            Self::ModuleDigestMismatch => "MODULE_DIGEST_MISMATCH",
            Self::FuelExceeded => "FUEL_EXCEEDED",
            Self::MalformedWasm => "MALFORMED_WASM",
        };
        formatter.write_str(value)
    }
}

/// A single Gall checkpoint receipt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Checkpoint {
    pub sequence: u8,
    pub subject: String,
    pub standing: Standing,
    pub detail: String,
}

/// Source pinned into the local ecosystem lock.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourcePin {
    pub repository: String,
    pub sha: String,
    pub role: String,
}

/// Parsed source admission registry.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceRegistry {
    sources: BTreeMap<String, SourcePin>,
}

impl SourceRegistry {
    pub fn embedded() -> Result<Self, Refusal> {
        Self::parse(ECOSYSTEM_LOCK)
    }

    pub fn parse(input: &str) -> Result<Self, Refusal> {
        let mut sources = BTreeMap::new();
        for line in input.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            let mut fields = line.split('|');
            let repository = fields.next().ok_or(Refusal::InvalidSourcePin)?.trim();
            let sha = fields.next().ok_or(Refusal::InvalidSourcePin)?.trim();
            let role = fields.next().ok_or(Refusal::InvalidSourcePin)?.trim();
            if fields.next().is_some()
                || repository.is_empty()
                || role.is_empty()
                || sha.len() != 40
                || !sha.bytes().all(|byte| byte.is_ascii_hexdigit())
            {
                return Err(Refusal::InvalidSourcePin);
            }
            let pin = SourcePin {
                repository: repository.to_owned(),
                sha: sha.to_ascii_lowercase(),
                role: role.to_owned(),
            };
            if sources.insert(repository.to_owned(), pin).is_some() {
                return Err(Refusal::DuplicateSource);
            }
        }
        if sources.is_empty() {
            return Err(Refusal::InvalidSourcePin);
        }
        Ok(Self { sources })
    }

    pub fn get(&self, repository: &str) -> Option<&SourcePin> {
        self.sources.get(repository)
    }

    pub fn repositories(&self) -> impl Iterator<Item = &str> {
        self.sources.keys().map(String::as_str)
    }
}

/// Exactly one broker owns actuation. There is no ambient DO authority.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Broker {
    owner: String,
}

impl Broker {
    pub fn new(owner: impl Into<String>) -> Result<Self, Refusal> {
        let owner = owner.into();
        if owner.trim().is_empty() {
            return Err(Refusal::AuthorityMultiplicity);
        }
        Ok(Self { owner })
    }

    pub fn owner(&self) -> &str {
        &self.owner
    }

    pub fn authorize(&self, subject: &str, registry: &SubjectRegistry) -> Result<(), Refusal> {
        let record = registry.get(subject).ok_or(Refusal::SubjectUnknown)?;
        if record.revoked {
            return Err(Refusal::SubjectRevoked);
        }
        if record.authority_owner != self.owner {
            return Err(Refusal::AuthorityOwnerMismatch);
        }
        Ok(())
    }
}

/// Subject admission record.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SubjectRecord {
    pub authority_owner: String,
    pub capabilities: BTreeSet<String>,
    pub revoked: bool,
}

/// Canonical admitted subject registry.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct SubjectRegistry {
    subjects: BTreeMap<String, SubjectRecord>,
}

impl SubjectRegistry {
    pub fn admit(
        &mut self,
        subject: impl Into<String>,
        authority_owner: impl Into<String>,
        capabilities: impl IntoIterator<Item = String>,
    ) -> Result<(), Refusal> {
        let subject = subject.into();
        let authority_owner = authority_owner.into();
        if subject.trim().is_empty() || authority_owner.trim().is_empty() {
            return Err(Refusal::SubjectUnknown);
        }
        self.subjects.insert(
            subject,
            SubjectRecord {
                authority_owner,
                capabilities: capabilities.into_iter().collect(),
                revoked: false,
            },
        );
        Ok(())
    }

    pub fn revoke(&mut self, subject: &str) -> Result<(), Refusal> {
        let record = self
            .subjects
            .get_mut(subject)
            .ok_or(Refusal::SubjectUnknown)?;
        record.revoked = true;
        Ok(())
    }

    pub fn get(&self, subject: &str) -> Option<&SubjectRecord> {
        self.subjects.get(subject)
    }

    pub fn require_capability(&self, subject: &str, capability: &str) -> Result<(), Refusal> {
        let record = self.get(subject).ok_or(Refusal::SubjectUnknown)?;
        if record.revoked {
            return Err(Refusal::SubjectRevoked);
        }
        if !record.capabilities.contains(capability) {
            return Err(Refusal::CapabilityDenied);
        }
        Ok(())
    }
}

/// Route from a channel to a session actor.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Route {
    pub channel: String,
    pub session: String,
}

/// Deterministic channel/session router.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Router {
    routes: BTreeMap<String, String>,
}

impl Router {
    pub fn bind(
        &mut self,
        channel: impl Into<String>,
        session: impl Into<String>,
    ) -> Result<(), Refusal> {
        let channel = channel.into();
        let session = session.into();
        if channel.trim().is_empty() || session.trim().is_empty() {
            return Err(Refusal::SubjectUnknown);
        }
        self.routes.insert(channel, session);
        Ok(())
    }

    pub fn route(&self, channel: &str) -> Option<Route> {
        self.routes.get(channel).map(|session| Route {
            channel: channel.to_owned(),
            session: session.clone(),
        })
    }
}

/// A tiny capability-fenced WebAssembly envelope.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WasmEnvelope {
    pub module_sha: String,
    pub imports: BTreeSet<String>,
    pub fuel: u64,
}

impl WasmEnvelope {
    pub fn verify(
        &self,
        expected_sha: &str,
        allowed_imports: &BTreeSet<String>,
        fuel_limit: u64,
    ) -> Result<(), Refusal> {
        if self.module_sha != expected_sha {
            return Err(Refusal::ModuleDigestMismatch);
        }
        if self.fuel > fuel_limit {
            return Err(Refusal::FuelExceeded);
        }
        if !self.imports.is_subset(allowed_imports) {
            return Err(Refusal::ImportNotDeclared);
        }
        Ok(())
    }
}

/// Exact four-stage phase executor.
#[derive(Debug)]
pub struct GallExecutor {
    registry: SourceRegistry,
    broker: Broker,
    subjects: SubjectRegistry,
    router: Router,
}

impl GallExecutor {
    pub fn new(
        registry: SourceRegistry,
        broker: Broker,
        subjects: SubjectRegistry,
        router: Router,
    ) -> Self {
        Self {
            registry,
            broker,
            subjects,
            router,
        }
    }

    pub fn execute_s0_s3(
        &self,
        subject: &str,
        channel: &str,
        required_capability: &str,
        wasm: &WasmEnvelope,
        expected_module_sha: &str,
        allowed_imports: &BTreeSet<String>,
        fuel_limit: u64,
    ) -> Result<Vec<Checkpoint>, Refusal> {
        let mut checkpoints = Vec::with_capacity(4);
        let source = self
            .registry
            .get("chatman-ecosystem")
            .ok_or(Refusal::InvalidSourcePin)?;
        checkpoints.push(Checkpoint {
            sequence: 0,
            subject: source.repository.clone(),
            standing: Standing::Alive,
            detail: source.sha.clone(),
        });

        self.broker.authorize(subject, &self.subjects)?;
        self.subjects
            .require_capability(subject, required_capability)?;
        checkpoints.push(Checkpoint {
            sequence: 1,
            subject: subject.to_owned(),
            standing: Standing::Alive,
            detail: self.broker.owner.clone(),
        });

        let route = self.router.route(channel).ok_or(Refusal::SubjectUnknown)?;
        checkpoints.push(Checkpoint {
            sequence: 2,
            subject: route.channel,
            standing: Standing::Alive,
            detail: route.session,
        });

        wasm.verify(expected_module_sha, allowed_imports, fuel_limit)?;
        checkpoints.push(Checkpoint {
            sequence: 3,
            subject: expected_module_sha.to_owned(),
            standing: Standing::Alive,
            detail: "WASM_CAPABILITY_FENCE".to_owned(),
        });

        Ok(checkpoints)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sha(character: char) -> String {
        std::iter::repeat_n(character, 40).collect()
    }

    fn executor() -> GallExecutor {
        let registry = SourceRegistry::parse(&format!(
            "chatman-ecosystem|{}|actuation-authority\n",
            sha('a')
        ))
        .unwrap();
        let broker = Broker::new("brce").unwrap();
        let mut subjects = SubjectRegistry::default();
        subjects
            .admit("job-1", "brce", ["filesystem.write".to_owned()])
            .unwrap();
        let mut router = Router::default();
        router.bind("cli", "session-1").unwrap();
        GallExecutor::new(registry, broker, subjects, router)
    }

    #[test]
    fn source_registry_embeds_exact_lock() {
        let registry = SourceRegistry::embedded().unwrap();
        assert!(registry.get("ggen").is_some());
        assert!(registry.get("chatman-ecosystem").is_some());
    }

    #[test]
    fn executes_all_four_checkpoints() {
        let executor = executor();
        let allowed = ["wasi:clocks".to_owned()].into_iter().collect();
        let wasm = WasmEnvelope {
            module_sha: sha('b'),
            imports: ["wasi:clocks".to_owned()].into_iter().collect(),
            fuel: 100,
        };
        let checkpoints = executor
            .execute_s0_s3(
                "job-1",
                "cli",
                "filesystem.write",
                &wasm,
                &sha('b'),
                &allowed,
                100,
            )
            .unwrap();
        assert_eq!(checkpoints.len(), 4);
        assert_eq!(checkpoints[0].sequence, 0);
        assert_eq!(checkpoints[3].sequence, 3);
    }

    #[test]
    fn refuses_unauthorized_subject() {
        let executor = executor();
        let allowed = BTreeSet::new();
        let wasm = WasmEnvelope {
            module_sha: sha('b'),
            imports: BTreeSet::new(),
            fuel: 1,
        };
        let result = executor.execute_s0_s3(
            "missing",
            "cli",
            "filesystem.write",
            &wasm,
            &sha('b'),
            &allowed,
            1,
        );
        assert_eq!(result, Err(Refusal::SubjectUnknown));
    }

    #[test]
    fn refuses_capability_escape() {
        let executor = executor();
        let allowed = BTreeSet::new();
        let wasm = WasmEnvelope {
            module_sha: sha('b'),
            imports: ["wasi:sockets".to_owned()].into_iter().collect(),
            fuel: 1,
        };
        let result = executor.execute_s0_s3(
            "job-1",
            "cli",
            "filesystem.write",
            &wasm,
            &sha('b'),
            &allowed,
            1,
        );
        assert_eq!(result, Err(Refusal::ImportNotDeclared));
    }

    #[test]
    fn refuses_revoked_subject() {
        let registry = SourceRegistry::parse(&format!(
            "chatman-ecosystem|{}|actuation-authority\n",
            sha('a')
        ))
        .unwrap();
        let broker = Broker::new("brce").unwrap();
        let mut subjects = SubjectRegistry::default();
        subjects
            .admit("job-1", "brce", ["filesystem.write".to_owned()])
            .unwrap();
        subjects.revoke("job-1").unwrap();
        let mut router = Router::default();
        router.bind("cli", "session-1").unwrap();
        let executor = GallExecutor::new(registry, broker, subjects, router);
        let wasm = WasmEnvelope {
            module_sha: sha('b'),
            imports: BTreeSet::new(),
            fuel: 1,
        };
        let result = executor.execute_s0_s3(
            "job-1",
            "cli",
            "filesystem.write",
            &wasm,
            &sha('b'),
            &BTreeSet::new(),
            1,
        );
        assert_eq!(result, Err(Refusal::SubjectRevoked));
    }
}
