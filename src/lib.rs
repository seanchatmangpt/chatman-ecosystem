//! Gall-sequenced execution capsule for Chatman ecosystem phases 0 through 3.
//!
//! The crate is intentionally dependency-free. It proves a bounded local system:
//! source admission, exclusive broker actuation, channel/session routing, and a
//! capability-fenced WebAssembly skill path.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt::{Display, Formatter};

const ECOSYSTEM_LOCK: &str = include_str!("../ecosystem.lock");

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
    pub id: String,
    pub phase: u8,
    pub name: String,
    pub standing: Standing,
    pub receipt_hash: String,
    pub evidence: String,
}

/// Crown report emitted only after S0, S1, S2 and S3 execute in order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GallReport {
    pub checkpoints: Vec<Checkpoint>,
    pub root_receipt: String,
}

impl GallReport {
    /// Deterministic, dependency-free JSON projection.
    #[must_use]
    pub fn to_json(&self) -> String {
        let checkpoints = self
            .checkpoints
            .iter()
            .map(|checkpoint| {
                format!(
                    concat!(
                        "{{\"id\":\"{}\",\"phase\":{},\"name\":\"{}\",",
                        "\"standing\":\"{}\",\"receipt_hash\":\"{}\",",
                        "\"evidence\":\"{}\"}}"
                    ),
                    json_escape(&checkpoint.id),
                    checkpoint.phase,
                    json_escape(&checkpoint.name),
                    checkpoint.standing,
                    json_escape(&checkpoint.receipt_hash),
                    json_escape(&checkpoint.evidence)
                )
            })
            .collect::<Vec<_>>()
            .join(",");
        format!(
            "{{\"standing\":\"ALIVE\",\"root_receipt\":\"{}\",\"checkpoints\":[{}]}}",
            json_escape(&self.root_receipt),
            checkpoints
        )
    }
}

fn json_escape(value: &str) -> String {
    let mut escaped = String::with_capacity(value.len());
    for character in value.chars() {
        match character {
            '"' => escaped.push_str("\\\""),
            '\\' => escaped.push_str("\\\\"),
            '\n' => escaped.push_str("\\n"),
            '\r' => escaped.push_str("\\r"),
            '\t' => escaped.push_str("\\t"),
            value if value.is_control() => {
                escaped.push_str(&format!("\\u{:04x}", u32::from(value)));
            }
            value => escaped.push(value),
        }
    }
    escaped
}

/// Admitted role of a pinned source repository.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SourceRole {
    ReceiptReference,
    CapabilityReference,
    ProcessEvidence,
    Planner,
    Oracle,
    Manufacturer,
    Certifier,
    SemanticAdmission,
    ActuationAuthority,
}

impl SourceRole {
    fn parse(value: &str) -> Option<Self> {
        match value {
            "receipt-reference" => Some(Self::ReceiptReference),
            "capability-reference" => Some(Self::CapabilityReference),
            "process-evidence" => Some(Self::ProcessEvidence),
            "planner" => Some(Self::Planner),
            "oracle" => Some(Self::Oracle),
            "manufacturer" => Some(Self::Manufacturer),
            "certifier" => Some(Self::Certifier),
            "semantic-admission" => Some(Self::SemanticAdmission),
            "actuation-authority" => Some(Self::ActuationAuthority),
            _ => None,
        }
    }

    fn as_str(&self) -> &'static str {
        match self {
            Self::ReceiptReference => "receipt-reference",
            Self::CapabilityReference => "capability-reference",
            Self::ProcessEvidence => "process-evidence",
            Self::Planner => "planner",
            Self::Oracle => "oracle",
            Self::Manufacturer => "manufacturer",
            Self::Certifier => "certifier",
            Self::SemanticAdmission => "semantic-admission",
            Self::ActuationAuthority => "actuation-authority",
        }
    }
}

/// Exact repository coordinate admitted into Phase 0.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourcePin {
    pub repository: String,
    pub commit: String,
    pub role: SourceRole,
}

/// Phase 0 admission result.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceAdmission {
    pub pins: Vec<SourcePin>,
    pub graph_digest: String,
}

fn parse_source_lock(contents: &str) -> Result<Vec<SourcePin>, Refusal> {
    let mut pins = Vec::new();
    for line in contents.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts = line.split('|').collect::<Vec<_>>();
        if parts.len() != 3 {
            return Err(Refusal::InvalidSourcePin);
        }
        let role = SourceRole::parse(parts[2]).ok_or(Refusal::InvalidSourcePin)?;
        pins.push(SourcePin {
            repository: parts[0].to_owned(),
            commit: parts[1].to_owned(),
            role,
        });
    }
    Ok(pins)
}

/// Admit a source graph only when all identities are exact and one authority exists.
pub fn admit_source_graph(contents: &str) -> Result<SourceAdmission, Refusal> {
    let pins = parse_source_lock(contents)?;
    if pins.len() != 9 {
        return Err(Refusal::InvalidSourcePin);
    }

    let expected = BTreeSet::from([
        "chatman-ecosystem",
        "ferroplan",
        "ggen",
        "mcpp",
        "mfact",
        "mfw",
        "truex",
        "unrdf",
        "wasm4pm",
    ]);
    let mut observed = BTreeSet::new();
    let mut authority_owners = Vec::new();

    for pin in &pins {
        if pin.repository.is_empty()
            || pin.commit.len() != 40
            || !pin
                .commit
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
        {
            return Err(Refusal::InvalidSourcePin);
        }
        if !observed.insert(pin.repository.as_str()) {
            return Err(Refusal::DuplicateSource);
        }
        if pin.role == SourceRole::ActuationAuthority {
            authority_owners.push(pin.repository.as_str());
        }
    }

    if observed != expected {
        return Err(Refusal::InvalidSourcePin);
    }
    if authority_owners.len() != 1 {
        return Err(Refusal::AuthorityMultiplicity);
    }
    if authority_owners[0] != "chatman-ecosystem" {
        return Err(Refusal::AuthorityOwnerMismatch);
    }

    let canonical = pins
        .iter()
        .map(|pin| {
            format!(
                "{}|{}|{}",
                pin.repository,
                pin.commit,
                pin.role.as_str()
            )
        })
        .collect::<Vec<_>>()
        .join("\n");
    Ok(SourceAdmission {
        pins,
        graph_digest: sha256_hex(canonical.as_bytes()),
    })
}

/// Canonical action object. This is the only object BRCE may actuate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Action {
    pub subject: String,
    pub capability: String,
    pub arguments: Vec<String>,
    pub working_directory: String,
    pub nonce: u64,
}

impl Action {
    /// Length-prefixed encoding prevents delimiter ambiguity.
    #[must_use]
    pub fn canonical_bytes(&self) -> Vec<u8> {
        let mut output = Vec::new();
        append_field(&mut output, self.subject.as_bytes());
        append_field(&mut output, self.capability.as_bytes());
        append_field(&mut output, self.working_directory.as_bytes());
        output.extend_from_slice(&self.nonce.to_be_bytes());
        output.extend_from_slice(&(self.arguments.len() as u64).to_be_bytes());
        for argument in &self.arguments {
            append_field(&mut output, argument.as_bytes());
        }
        output
    }

    #[must_use]
    pub fn digest(&self) -> String {
        sha256_hex(&self.canonical_bytes())
    }
}

fn append_field(output: &mut Vec<u8>, value: &[u8]) {
    output.extend_from_slice(&(value.len() as u64).to_be_bytes());
    output.extend_from_slice(value);
}

/// Versioned capability policy.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Policy {
    version: String,
    allowed: BTreeMap<String, BTreeSet<String>>,
    revoked: BTreeSet<String>,
}

impl Policy {
    #[must_use]
    pub fn new(version: impl Into<String>) -> Self {
        Self {
            version: version.into(),
            allowed: BTreeMap::new(),
            revoked: BTreeSet::new(),
        }
    }

    pub fn allow(&mut self, subject: impl Into<String>, capability: impl Into<String>) {
        self.allowed
            .entry(subject.into())
            .or_default()
            .insert(capability.into());
    }

    pub fn revoke(&mut self, subject: impl Into<String>) {
        self.revoked.insert(subject.into());
    }

    #[must_use]
    pub fn digest(&self) -> String {
        let mut canonical = format!("version={}\n", self.version);
        for (subject, capabilities) in &self.allowed {
            for capability in capabilities {
                canonical.push_str(subject);
                canonical.push('|');
                canonical.push_str(capability);
                canonical.push('\n');
            }
        }
        for subject in &self.revoked {
            canonical.push_str("revoked|");
            canonical.push_str(subject);
            canonical.push('\n');
        }
        sha256_hex(canonical.as_bytes())
    }

    fn admit(&self, action: &Action) -> Result<AdmissionToken, Refusal> {
        if action.subject.starts_with("unknown:") {
            return Err(Refusal::SubjectUnknown);
        }
        if self.revoked.contains(&action.subject) {
            return Err(Refusal::SubjectRevoked);
        }
        let admitted = self
            .allowed
            .get(&action.subject)
            .is_some_and(|capabilities| capabilities.contains(&action.capability));
        if !admitted {
            return Err(Refusal::CapabilityDenied);
        }
        Ok(AdmissionToken {
            action_digest: action.digest(),
            policy_digest: self.digest(),
        })
    }
}

/// Exact action/policy binding manufactured at admission.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdmissionToken {
    action_digest: String,
    policy_digest: String,
}

/// Consequence emitted by the bounded execution kernel.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Consequence {
    Text(String),
    Number(i32),
}

impl Consequence {
    fn canonical_bytes(&self) -> Vec<u8> {
        match self {
            Self::Text(value) => {
                let mut bytes = b"text:".to_vec();
                bytes.extend_from_slice(value.as_bytes());
                bytes
            }
            Self::Number(value) => {
                let mut bytes = b"number:".to_vec();
                bytes.extend_from_slice(&value.to_be_bytes());
                bytes
            }
        }
    }
}

/// Receipt produced for every BRCE success or refusal.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Receipt {
    pub receipt_hash: String,
    pub previous_hash: String,
    pub sequence: u64,
    pub action_hash: String,
    pub policy_hash: String,
    pub standing: Standing,
    pub outcome_code: String,
    pub consequence_hash: String,
}

/// Result and receipt of one broker attempt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BrokerOutcome {
    pub result: Result<Consequence, Refusal>,
    pub receipt: Receipt,
}

/// Exclusive DO boundary.
#[derive(Debug, Clone)]
pub struct Broker {
    previous_hash: String,
    sequence: u64,
}

impl Default for Broker {
    fn default() -> Self {
        Self::new()
    }
}

impl Broker {
    #[must_use]
    pub fn new() -> Self {
        Self {
            previous_hash: "GENESIS".to_owned(),
            sequence: 0,
        }
    }

    fn replay_seed(receipt: &Receipt) -> Self {
        Self {
            previous_hash: receipt.previous_hash.clone(),
            sequence: receipt.sequence.saturating_sub(1),
        }
    }

    /// Submit an action. Final admission and all actuation occur inside BRCE.
    pub fn submit(
        &mut self,
        policy: &Policy,
        action: &Action,
        token: Option<&AdmissionToken>,
    ) -> BrokerOutcome {
        let admission = match token {
            Some(token) => self.validate_token(policy, action, token),
            None => policy.admit(action),
        };

        match admission {
            Ok(_) => {
                let consequence = self.actuate(action);
                match consequence {
                    Ok(consequence) => self.finish(
                        policy,
                        action,
                        Ok(consequence),
                        Standing::Alive,
                        "ACTUATED",
                    ),
                    Err(refusal) => {
                        let code = refusal.to_string();
                        self.finish(policy, action, Err(refusal), Standing::Refused, &code)
                    }
                }
            }
            Err(refusal) => {
                let code = refusal.to_string();
                self.finish(policy, action, Err(refusal), Standing::Refused, &code)
            }
        }
    }

    /// Record a pre-actuation refusal through the same receipt chain.
    pub fn record_refusal(
        &mut self,
        policy: &Policy,
        action: &Action,
        refusal: Refusal,
    ) -> BrokerOutcome {
        let code = refusal.to_string();
        self.finish(policy, action, Err(refusal), Standing::Refused, &code)
    }

    fn validate_token(
        &self,
        policy: &Policy,
        action: &Action,
        token: &AdmissionToken,
    ) -> Result<AdmissionToken, Refusal> {
        if token.policy_digest != policy.digest() {
            return Err(Refusal::PolicyDigestMismatch);
        }
        if token.action_digest != action.digest() {
            return Err(Refusal::ActionDigestMismatch);
        }
        policy.admit(action)
    }

    fn actuate(&self, action: &Action) -> Result<Consequence, Refusal> {
        match action.capability.as_str() {
            "echo" => Ok(Consequence::Text(
                action.arguments.first().cloned().unwrap_or_default(),
            )),
            "wasm.actuate" => {
                let value = action
                    .arguments
                    .first()
                    .and_then(|argument| argument.parse::<i32>().ok())
                    .ok_or(Refusal::CapabilityDenied)?;
                Ok(Consequence::Number(value))
            }
            _ => Err(Refusal::CapabilityDenied),
        }
    }

    fn finish(
        &mut self,
        policy: &Policy,
        action: &Action,
        result: Result<Consequence, Refusal>,
        standing: Standing,
        outcome_code: &str,
    ) -> BrokerOutcome {
        self.sequence += 1;
        let action_hash = action.digest();
        let policy_hash = policy.digest();
        let consequence_hash = match &result {
            Ok(consequence) => sha256_hex(&consequence.canonical_bytes()),
            Err(refusal) => sha256_hex(refusal.to_string().as_bytes()),
        };
        let canonical = format!(
            "{}|{}|{}|{}|{}|{}|{}",
            self.previous_hash,
            self.sequence,
            action_hash,
            policy_hash,
            standing,
            outcome_code,
            consequence_hash
        );
        let receipt_hash = sha256_hex(canonical.as_bytes());
        let receipt = Receipt {
            receipt_hash: receipt_hash.clone(),
            previous_hash: self.previous_hash.clone(),
            sequence: self.sequence,
            action_hash,
            policy_hash,
            standing,
            outcome_code: outcome_code.to_owned(),
            consequence_hash,
        };
        self.previous_hash = receipt_hash;
        BrokerOutcome { result, receipt }
    }

    /// Verify receipt identity without trusting stored prose.
    #[must_use]
    pub fn verify_receipt(receipt: &Receipt) -> bool {
        let canonical = format!(
            "{}|{}|{}|{}|{}|{}|{}",
            receipt.previous_hash,
            receipt.sequence,
            receipt.action_hash,
            receipt.policy_hash,
            receipt.standing,
            receipt.outcome_code,
            receipt.consequence_hash
        );
        sha256_hex(canonical.as_bytes()) == receipt.receipt_hash
    }

    /// Replay re-enters BRCE from the receipt-bound predecessor state.
    #[must_use]
    pub fn replay(receipt: &Receipt, policy: &Policy, action: &Action) -> bool {
        if receipt.action_hash != action.digest() || receipt.policy_hash != policy.digest() {
            return false;
        }
        let mut broker = Self::replay_seed(receipt);
        let replay = broker.submit(policy, action, None);
        replay.receipt == *receipt
    }
}

/// Inbound presentation channel. All variants share one gateway core.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Channel {
    Cli,
    WebChat,
    Telegram,
    Discord,
}

impl Channel {
    fn as_str(self) -> &'static str {
        match self {
            Self::Cli => "cli",
            Self::WebChat => "webchat",
            Self::Telegram => "telegram",
            Self::Discord => "discord",
        }
    }
}

/// One channel message.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Message {
    pub channel: Channel,
    pub external_subject: String,
    pub body: String,
}

/// Shared gateway: identity -> construct -> broker. No channel owns DO authority.
#[derive(Debug, Clone)]
pub struct Gateway {
    identities: BTreeMap<(Channel, String), String>,
    policy: Policy,
    broker: Broker,
    nonce: u64,
}

impl Gateway {
    #[must_use]
    pub fn new(policy: Policy) -> Self {
        Self {
            identities: BTreeMap::new(),
            policy,
            broker: Broker::new(),
            nonce: 0,
        }
    }

    pub fn register(
        &mut self,
        channel: Channel,
        external_subject: impl Into<String>,
        subject: impl Into<String>,
    ) {
        self.identities
            .insert((channel, external_subject.into()), subject.into());
    }

    pub fn revoke(&mut self, subject: impl Into<String>) {
        self.policy.revoke(subject);
    }

    pub fn handle(&mut self, message: &Message) -> BrokerOutcome {
        self.nonce += 1;
        let subject = self
            .identities
            .get(&(message.channel, message.external_subject.clone()))
            .cloned()
            .unwrap_or_else(|| {
                format!(
                    "unknown:{}:{}",
                    message.channel.as_str(),
                    message.external_subject
                )
            });
        let (capability, arguments) = construct_intent(&message.body);
        let action = Action {
            subject,
            capability,
            arguments,
            working_directory: "/".to_owned(),
            nonce: self.nonce,
        };
        self.broker.submit(&self.policy, &action, None)
    }
}

fn construct_intent(body: &str) -> (String, Vec<String>) {
    if let Some(value) = body.strip_prefix("echo ") {
        ("echo".to_owned(), vec![value.to_owned()])
    } else {
        ("unsupported.request".to_owned(), vec![body.to_owned()])
    }
}

/// Capability manifest for a single immutable WASM module.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SkillManifest {
    pub module_digest: String,
    pub subject: String,
    pub allowed_imports: BTreeSet<(String, String)>,
    pub fuel: u64,
}

/// WASM execution result. Every result carries a BRCE receipt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SkillOutcome {
    pub result: Result<i32, Refusal>,
    pub receipt: Receipt,
    pub action: Action,
}

/// Bounded MVP interpreter for the exact Gall skill shape.
pub struct WasmRuntime;

impl WasmRuntime {
    pub fn execute(
        broker: &mut Broker,
        policy: &Policy,
        module: &[u8],
        manifest: &SkillManifest,
        input: i32,
        nonce: u64,
    ) -> SkillOutcome {
        let load_action = Action {
            subject: manifest.subject.clone(),
            capability: "wasm.load".to_owned(),
            arguments: vec![sha256_hex(module)],
            working_directory: "/skill".to_owned(),
            nonce,
        };

        if sha256_hex(module) != manifest.module_digest {
            return skill_refusal(
                broker,
                policy,
                load_action,
                Refusal::ModuleDigestMismatch,
            );
        }

        let parsed = match ParsedModule::parse(module) {
            Ok(parsed) => parsed,
            Err(refusal) => return skill_refusal(broker, policy, load_action, refusal),
        };

        for import in &parsed.imports {
            if !manifest
                .allowed_imports
                .contains(&(import.module.clone(), import.name.clone()))
            {
                return skill_refusal(
                    broker,
                    policy,
                    load_action,
                    Refusal::ImportNotDeclared,
                );
            }
            if import.module != "fabric" || import.name != "actuate" {
                return skill_refusal(broker, policy, load_action, Refusal::UnsupportedWasm);
            }
        }

        let action = Action {
            subject: manifest.subject.clone(),
            capability: "wasm.actuate".to_owned(),
            arguments: vec![input.to_string()],
            working_directory: "/skill".to_owned(),
            nonce,
        };

        match parsed.interpret(input, manifest.fuel, broker, policy, &action) {
            Ok((value, outcome)) => SkillOutcome {
                result: Ok(value),
                receipt: outcome.receipt,
                action,
            },
            Err((refusal, Some(outcome))) => SkillOutcome {
                result: Err(refusal),
                receipt: outcome.receipt,
                action,
            },
            Err((refusal, None)) => skill_refusal(broker, policy, action, refusal),
        }
    }
}

fn skill_refusal(
    broker: &mut Broker,
    policy: &Policy,
    action: Action,
    refusal: Refusal,
) -> SkillOutcome {
    let outcome = broker.record_refusal(policy, &action, refusal.clone());
    SkillOutcome {
        result: Err(refusal),
        receipt: outcome.receipt,
        action,
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct WasmImport {
    module: String,
    name: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct ParsedModule {
    imports: Vec<WasmImport>,
    run_function_index: u32,
    run_body: Vec<u8>,
}

impl ParsedModule {
    fn parse(module: &[u8]) -> Result<Self, Refusal> {
        if module.len() < 8 || &module[..8] != b"\0asm\x01\0\0\0" {
            return Err(Refusal::MalformedWasm);
        }
        let mut reader = Reader::new(&module[8..]);
        let mut imports = Vec::new();
        let mut declared_functions = Vec::new();
        let mut run_function_index = None;
        let mut bodies = Vec::new();
        let mut type_count = 0_u32;

        while !reader.is_empty() {
            let section_id = reader.read_u8()?;
            let section_size = reader.read_leb_u32()? as usize;
            let section_bytes = reader.read_exact(section_size)?;
            let mut section = Reader::new(section_bytes);
            match section_id {
                1 => {
                    type_count = section.read_leb_u32()?;
                    for _ in 0..type_count {
                        if section.read_u8()? != 0x60 {
                            return Err(Refusal::UnsupportedWasm);
                        }
                        let parameters = section.read_leb_u32()?;
                        if parameters != 1 || section.read_u8()? != 0x7f {
                            return Err(Refusal::UnsupportedWasm);
                        }
                        let results = section.read_leb_u32()?;
                        if results != 1 || section.read_u8()? != 0x7f {
                            return Err(Refusal::UnsupportedWasm);
                        }
                    }
                }
                2 => {
                    let count = section.read_leb_u32()?;
                    for _ in 0..count {
                        let module = section.read_name()?;
                        let name = section.read_name()?;
                        if section.read_u8()? != 0 {
                            return Err(Refusal::UnsupportedWasm);
                        }
                        let type_index = section.read_leb_u32()?;
                        if type_index >= type_count {
                            return Err(Refusal::MalformedWasm);
                        }
                        imports.push(WasmImport { module, name });
                    }
                }
                3 => {
                    let count = section.read_leb_u32()?;
                    for _ in 0..count {
                        let type_index = section.read_leb_u32()?;
                        if type_index >= type_count {
                            return Err(Refusal::MalformedWasm);
                        }
                        declared_functions.push(type_index);
                    }
                }
                7 => {
                    let count = section.read_leb_u32()?;
                    for _ in 0..count {
                        let name = section.read_name()?;
                        let kind = section.read_u8()?;
                        let index = section.read_leb_u32()?;
                        if name == "run" {
                            if kind != 0 {
                                return Err(Refusal::UnsupportedWasm);
                            }
                            run_function_index = Some(index);
                        }
                    }
                }
                10 => {
                    let count = section.read_leb_u32()?;
                    for _ in 0..count {
                        let size = section.read_leb_u32()? as usize;
                        bodies.push(section.read_exact(size)?.to_vec());
                    }
                }
                0 | 4..=6 | 8 | 9 | 11..=12 => {
                    // Known but unused standard sections remain data-only.
                }
                _ => return Err(Refusal::UnsupportedWasm),
            }
            if !section.is_empty() {
                return Err(Refusal::MalformedWasm);
            }
        }

        let run_function_index = run_function_index.ok_or(Refusal::MalformedWasm)?;
        let imported_count = imports.len() as u32;
        if run_function_index < imported_count {
            return Err(Refusal::UnsupportedWasm);
        }
        let body_index = (run_function_index - imported_count) as usize;
        if declared_functions.len() != bodies.len() || body_index >= bodies.len() {
            return Err(Refusal::MalformedWasm);
        }

        Ok(Self {
            imports,
            run_function_index,
            run_body: bodies[body_index].clone(),
        })
    }

    fn interpret(
        &self,
        input: i32,
        fuel: u64,
        broker: &mut Broker,
        policy: &Policy,
        action: &Action,
    ) -> Result<(i32, BrokerOutcome), (Refusal, Option<BrokerOutcome>)> {
        let _run_index = self.run_function_index;
        let mut reader = Reader::new(&self.run_body);
        let local_groups = reader
            .read_leb_u32()
            .map_err(|refusal| (refusal, None))?;
        if local_groups != 0 {
            return Err((Refusal::UnsupportedWasm, None));
        }

        let mut remaining_fuel = fuel;
        let mut stack = Vec::new();
        let mut broker_outcome = None;

        loop {
            if remaining_fuel == 0 {
                return Err((Refusal::FuelExceeded, broker_outcome));
            }
            remaining_fuel -= 1;
            let opcode = reader.read_u8().map_err(|refusal| (refusal, None))?;
            match opcode {
                0x20 => {
                    let local_index = reader
                        .read_leb_u32()
                        .map_err(|refusal| (refusal, None))?;
                    if local_index != 0 {
                        return Err((Refusal::UnsupportedWasm, broker_outcome));
                    }
                    stack.push(input);
                }
                0x10 => {
                    let function_index = reader
                        .read_leb_u32()
                        .map_err(|refusal| (refusal, None))?;
                    if function_index != 0 || self.imports.len() != 1 {
                        return Err((Refusal::UnsupportedWasm, broker_outcome));
                    }
                    let argument = stack
                        .pop()
                        .ok_or((Refusal::MalformedWasm, broker_outcome.clone()))?;
                    let mut call_action = action.clone();
                    call_action.arguments = vec![argument.to_string()];
                    let outcome = broker.submit(policy, &call_action, None);
                    let result = outcome.result.clone();
                    let value = match result {
                        Ok(Consequence::Number(value)) => value,
                        Ok(Consequence::Text(_)) => {
                            return Err((Refusal::UnsupportedWasm, Some(outcome)));
                        }
                        Err(refusal) => return Err((refusal, Some(outcome))),
                    };
                    stack.push(value);
                    broker_outcome = Some(outcome);
                }
                0x0b => {
                    if !reader.is_empty() {
                        return Err((Refusal::MalformedWasm, broker_outcome));
                    }
                    let value = stack
                        .pop()
                        .ok_or((Refusal::MalformedWasm, broker_outcome.clone()))?;
                    let outcome = broker_outcome
                        .ok_or((Refusal::MalformedWasm, None))?;
                    return Ok((value, outcome));
                }
                _ => return Err((Refusal::UnsupportedWasm, broker_outcome)),
            }
        }
    }
}

#[derive(Debug, Clone)]
struct Reader<'a> {
    bytes: &'a [u8],
    cursor: usize,
}

impl<'a> Reader<'a> {
    fn new(bytes: &'a [u8]) -> Self {
        Self { bytes, cursor: 0 }
    }

    fn is_empty(&self) -> bool {
        self.cursor == self.bytes.len()
    }

    fn read_u8(&mut self) -> Result<u8, Refusal> {
        let value = *self.bytes.get(self.cursor).ok_or(Refusal::MalformedWasm)?;
        self.cursor += 1;
        Ok(value)
    }

    fn read_exact(&mut self, length: usize) -> Result<&'a [u8], Refusal> {
        let end = self
            .cursor
            .checked_add(length)
            .ok_or(Refusal::MalformedWasm)?;
        let value = self
            .bytes
            .get(self.cursor..end)
            .ok_or(Refusal::MalformedWasm)?;
        self.cursor = end;
        Ok(value)
    }

    fn read_leb_u32(&mut self) -> Result<u32, Refusal> {
        let mut result = 0_u32;
        let mut shift = 0_u32;
        for _ in 0..5 {
            let byte = self.read_u8()?;
            result |= u32::from(byte & 0x7f) << shift;
            if byte & 0x80 == 0 {
                return Ok(result);
            }
            shift += 7;
        }
        Err(Refusal::MalformedWasm)
    }

    fn read_name(&mut self) -> Result<String, Refusal> {
        let length = self.read_leb_u32()? as usize;
        let bytes = self.read_exact(length)?;
        std::str::from_utf8(bytes)
            .map(str::to_owned)
            .map_err(|_| Refusal::MalformedWasm)
    }
}

/// Manufacture the smallest valid module: `(i32) -> i32` through fabric.actuate.
#[must_use]
pub fn gall_skill_module() -> Vec<u8> {
    vec![
        0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00, // magic + version
        0x01, 0x06, 0x01, 0x60, 0x01, 0x7f, 0x01, 0x7f, // type
        0x02, 0x12, 0x01, 0x06, b'f', b'a', b'b', b'r', b'i', b'c', 0x07, b'a',
        b'c', b't', b'u', b'a', b't', b'e', 0x00, 0x00, // import
        0x03, 0x02, 0x01, 0x00, // function
        0x07, 0x07, 0x01, 0x03, b'r', b'u', b'n', 0x00, 0x01, // export
        0x0a, 0x08, 0x01, 0x06, 0x00, 0x20, 0x00, 0x10, 0x00, 0x0b, // code
    ]
}

fn phase_zero() -> Result<Checkpoint, String> {
    let admission = admit_source_graph(ECOSYSTEM_LOCK).map_err(|error| error.to_string())?;

    let duplicate = format!(
        "{ECOSYSTEM_LOCK}truex|7da0500926ddd0374e91f6ab8d58244f6611fe4a|receipt-reference\n"
    );
    if admit_source_graph(&duplicate) != Err(Refusal::InvalidSourcePin) {
        return Err("phase 0 duplicate source negative fixture failed".to_owned());
    }

    let multiple_authority = ECOSYSTEM_LOCK.replace(
        "mcpp|9995559a9042806ba18cd8177b1f5dd4c064008b|capability-reference",
        "mcpp|9995559a9042806ba18cd8177b1f5dd4c064008b|actuation-authority",
    );
    if admit_source_graph(&multiple_authority) != Err(Refusal::AuthorityMultiplicity) {
        return Err("phase 0 authority multiplicity fixture failed".to_owned());
    }

    let receipt_hash = sha256_hex(
        format!("GALL-S0|{}|{}", admission.graph_digest, admission.pins.len()).as_bytes(),
    );
    Ok(Checkpoint {
        id: "GALL-S0".to_owned(),
        phase: 0,
        name: "source-admission".to_owned(),
        standing: Standing::Alive,
        receipt_hash,
        evidence: format!(
            "positive=9 exact pins;authority=chatman-ecosystem;negative=duplicate+multiple-authority refused;graph={}",
            admission.graph_digest
        ),
    })
}

fn phase_one(parent: &Checkpoint) -> Result<Checkpoint, String> {
    let mut policy = Policy::new("phase-1");
    policy.allow("operator", "echo");

    let action = Action {
        subject: "operator".to_owned(),
        capability: "echo".to_owned(),
        arguments: vec!["hello".to_owned()],
        working_directory: "/".to_owned(),
        nonce: 1,
    };
    let token = policy.admit(&action).map_err(|error| error.to_string())?;
    let mut broker = Broker::new();
    let success = broker.submit(&policy, &action, Some(&token));
    if success.result != Ok(Consequence::Text("hello".to_owned()))
        || success.receipt.standing != Standing::Alive
        || !Broker::verify_receipt(&success.receipt)
        || !Broker::replay(&success.receipt, &policy, &action)
    {
        return Err("phase 1 successful actuation or replay failed".to_owned());
    }

    let mut mutated = action.clone();
    mutated.arguments = vec!["tampered".to_owned()];
    let mutation = broker.submit(&policy, &mutated, Some(&token));
    if mutation.result != Err(Refusal::ActionDigestMismatch)
        || mutation.receipt.standing != Standing::Refused
        || !Broker::verify_receipt(&mutation.receipt)
    {
        return Err("phase 1 approval/action mutation refusal failed".to_owned());
    }

    let denied = Action {
        capability: "admin".to_owned(),
        nonce: 2,
        ..action.clone()
    };
    let denial = broker.submit(&policy, &denied, None);
    if denial.result != Err(Refusal::CapabilityDenied)
        || !Broker::verify_receipt(&denial.receipt)
    {
        return Err("phase 1 undeclared capability refusal failed".to_owned());
    }

    let receipt_hash = sha256_hex(
        format!(
            "{}|{}|{}|{}",
            parent.receipt_hash,
            success.receipt.receipt_hash,
            mutation.receipt.receipt_hash,
            denial.receipt.receipt_hash
        )
        .as_bytes(),
    );
    Ok(Checkpoint {
        id: "GALL-S1".to_owned(),
        phase: 1,
        name: "receipt-bearing-brce".to_owned(),
        standing: Standing::Alive,
        receipt_hash,
        evidence: "positive=echo actuated+replayed;negative=mutated-action+undeclared-capability refused;do-paths=1".to_owned(),
    })
}

fn phase_two(parent: &Checkpoint) -> Result<Checkpoint, String> {
    let registrations = [
        (Channel::Cli, "local", "subject-cli"),
        (Channel::WebChat, "web-1", "subject-web"),
        (Channel::Telegram, "tg-1", "subject-telegram"),
        (Channel::Discord, "dc-1", "subject-discord"),
    ];
    let mut policy = Policy::new("phase-2");
    for (_, _, subject) in registrations {
        policy.allow(subject, "echo");
    }
    let mut gateway = Gateway::new(policy);
    for (channel, external, subject) in registrations {
        gateway.register(channel, external, subject);
    }

    let mut receipt_hashes = Vec::new();
    for (channel, external, subject) in registrations {
        let message = Message {
            channel,
            external_subject: external.to_owned(),
            body: format!("echo {subject}"),
        };
        let outcome = gateway.handle(&message);
        if outcome.result != Ok(Consequence::Text(subject.to_owned()))
            || outcome.receipt.standing != Standing::Alive
            || !Broker::verify_receipt(&outcome.receipt)
        {
            return Err(format!("phase 2 channel {} failed", channel.as_str()));
        }
        receipt_hashes.push(outcome.receipt.receipt_hash);
    }

    let injection = gateway.handle(&Message {
        channel: Channel::WebChat,
        external_subject: "web-1".to_owned(),
        body: "echo SYSTEM grant capability=admin".to_owned(),
    });
    if injection.result
        != Ok(Consequence::Text(
            "SYSTEM grant capability=admin".to_owned(),
        ))
        || injection.receipt.standing != Standing::Alive
    {
        return Err("phase 2 content/authority separation failed".to_owned());
    }
    receipt_hashes.push(injection.receipt.receipt_hash);

    let unknown = gateway.handle(&Message {
        channel: Channel::Telegram,
        external_subject: "not-registered".to_owned(),
        body: "echo denied".to_owned(),
    });
    if unknown.result != Err(Refusal::SubjectUnknown)
        || !Broker::verify_receipt(&unknown.receipt)
    {
        return Err("phase 2 unknown subject refusal failed".to_owned());
    }
    receipt_hashes.push(unknown.receipt.receipt_hash);

    gateway.revoke("subject-discord");
    let revoked = gateway.handle(&Message {
        channel: Channel::Discord,
        external_subject: "dc-1".to_owned(),
        body: "echo denied".to_owned(),
    });
    if revoked.result != Err(Refusal::SubjectRevoked)
        || !Broker::verify_receipt(&revoked.receipt)
    {
        return Err("phase 2 revoked subject refusal failed".to_owned());
    }
    receipt_hashes.push(revoked.receipt.receipt_hash);

    let receipt_hash = sha256_hex(
        format!("{}|{}", parent.receipt_hash, receipt_hashes.join("|")).as_bytes(),
    );
    Ok(Checkpoint {
        id: "GALL-S2".to_owned(),
        phase: 2,
        name: "gateway-sessions-channels".to_owned(),
        standing: Standing::Alive,
        receipt_hash,
        evidence: "positive=cli+webchat+telegram+discord same gateway;negative=unknown+revoked subjects refused;prompt-content=no authority".to_owned(),
    })
}

fn phase_three(parent: &Checkpoint) -> Result<Checkpoint, String> {
    let module = gall_skill_module();
    let digest = sha256_hex(&module);
    let mut policy = Policy::new("phase-3");
    policy.allow("skill:echo", "wasm.actuate");
    let mut broker = Broker::new();

    let allowed_imports = BTreeSet::from([("fabric".to_owned(), "actuate".to_owned())]);
    let manifest = SkillManifest {
        module_digest: digest.clone(),
        subject: "skill:echo".to_owned(),
        allowed_imports,
        fuel: 3,
    };
    let success = WasmRuntime::execute(&mut broker, &policy, &module, &manifest, 41, 30);
    if success.result != Ok(41)
        || success.receipt.standing != Standing::Alive
        || !Broker::verify_receipt(&success.receipt)
        || !Broker::replay(&success.receipt, &policy, &success.action)
    {
        return Err("phase 3 WASM actuation or replay failed".to_owned());
    }

    let undeclared = SkillManifest {
        allowed_imports: BTreeSet::new(),
        ..manifest.clone()
    };
    let import_refusal =
        WasmRuntime::execute(&mut broker, &policy, &module, &undeclared, 41, 31);
    if import_refusal.result != Err(Refusal::ImportNotDeclared)
        || !Broker::verify_receipt(&import_refusal.receipt)
    {
        return Err("phase 3 undeclared import refusal failed".to_owned());
    }

    let mut tampered = module.clone();
    let last = tampered
        .last_mut()
        .ok_or_else(|| "phase 3 empty module".to_owned())?;
    *last ^= 1;
    let digest_refusal =
        WasmRuntime::execute(&mut broker, &policy, &tampered, &manifest, 41, 32);
    if digest_refusal.result != Err(Refusal::ModuleDigestMismatch)
        || !Broker::verify_receipt(&digest_refusal.receipt)
    {
        return Err("phase 3 module digest refusal failed".to_owned());
    }

    let starved = SkillManifest {
        fuel: 1,
        ..manifest.clone()
    };
    let fuel_refusal = WasmRuntime::execute(&mut broker, &policy, &module, &starved, 41, 33);
    if fuel_refusal.result != Err(Refusal::FuelExceeded)
        || !Broker::verify_receipt(&fuel_refusal.receipt)
    {
        return Err("phase 3 fuel refusal failed".to_owned());
    }

    let receipt_hash = sha256_hex(
        format!(
            "{}|{}|{}|{}|{}|{}",
            parent.receipt_hash,
            digest,
            success.receipt.receipt_hash,
            import_refusal.receipt.receipt_hash,
            digest_refusal.receipt.receipt_hash,
            fuel_refusal.receipt.receipt_hash
        )
        .as_bytes(),
    );
    Ok(Checkpoint {
        id: "GALL-S3".to_owned(),
        phase: 3,
        name: "wasm-skills-capabilities".to_owned(),
        standing: Standing::Alive,
        receipt_hash,
        evidence: format!(
            "positive=real-wasm fabric.actuate through BRCE+replay;negative=undeclared-import+digest+fuel refused;module={digest}"
        ),
    })
}

/// Execute every phase in strict Gall order. Later phases are unreachable if a
/// lower checkpoint does not work.
pub fn run_gall() -> Result<GallReport, String> {
    let phase_zero = phase_zero()?;
    let phase_one = phase_one(&phase_zero)?;
    let phase_two = phase_two(&phase_one)?;
    let phase_three = phase_three(&phase_two)?;
    let checkpoints = vec![phase_zero, phase_one, phase_two, phase_three];

    if checkpoints
        .iter()
        .enumerate()
        .any(|(index, checkpoint)| {
            checkpoint.phase as usize != index || checkpoint.standing != Standing::Alive
        })
    {
        return Err("Gall checkpoint order or standing violation".to_owned());
    }

    let root_receipt = sha256_hex(
        checkpoints
            .iter()
            .map(|checkpoint| checkpoint.receipt_hash.as_str())
            .collect::<Vec<_>>()
            .join("|")
            .as_bytes(),
    );
    Ok(GallReport {
        checkpoints,
        root_receipt,
    })
}

/// SHA-256 digest rendered as lower-case hexadecimal.
#[must_use]
pub fn sha256_hex(input: &[u8]) -> String {
    let digest = sha256(input);
    let mut output = String::with_capacity(64);
    for byte in digest {
        output.push_str(&format!("{byte:02x}"));
    }
    output
}

fn sha256(input: &[u8]) -> [u8; 32] {
    const INITIAL: [u32; 8] = [
        0x6a09_e667,
        0xbb67_ae85,
        0x3c6e_f372,
        0xa54f_f53a,
        0x510e_527f,
        0x9b05_688c,
        0x1f83_d9ab,
        0x5be0_cd19,
    ];
    const ROUND: [u32; 64] = [
        0x428a_2f98, 0x7137_4491, 0xb5c0_fbcf, 0xe9b5_dba5, 0x3956_c25b, 0x59f1_11f1,
        0x923f_82a4, 0xab1c_5ed5, 0xd807_aa98, 0x1283_5b01, 0x2431_85be, 0x550c_7dc3,
        0x72be_5d74, 0x80de_b1fe, 0x9bdc_06a7, 0xc19b_f174, 0xe49b_69c1, 0xefbe_4786,
        0x0fc1_9dc6, 0x240c_a1cc, 0x2de9_2c6f, 0x4a74_84aa, 0x5cb0_a9dc, 0x76f9_88da,
        0x983e_5152, 0xa831_c66d, 0xb003_27c8, 0xbf59_7fc7, 0xc6e0_0bf3, 0xd5a7_9147,
        0x06ca_6351, 0x1429_2967, 0x27b7_0a85, 0x2e1b_2138, 0x4d2c_6dfc, 0x5338_0d13,
        0x650a_7354, 0x766a_0abb, 0x81c2_c92e, 0x9272_2c85, 0xa2bf_e8a1, 0xa81a_664b,
        0xc24b_8b70, 0xc76c_51a3, 0xd192_e819, 0xd699_0624, 0xf40e_3585, 0x106a_a070,
        0x19a4_c116, 0x1e37_6c08, 0x2748_774c, 0x34b0_bcb5, 0x391c_0cb3, 0x4ed8_aa4a,
        0x5b9c_ca4f, 0x682e_6ff3, 0x748f_82ee, 0x78a5_636f, 0x84c8_7814, 0x8cc7_0208,
        0x90be_fffa, 0xa450_6ceb, 0xbef9_a3f7, 0xc671_78f2,
    ];

    let bit_length = (input.len() as u64).wrapping_mul(8);
    let mut padded = input.to_vec();
    padded.push(0x80);
    while padded.len() % 64 != 56 {
        padded.push(0);
    }
    padded.extend_from_slice(&bit_length.to_be_bytes());

    let mut state = INITIAL;
    for chunk in padded.chunks_exact(64) {
        let mut schedule = [0_u32; 64];
        for (index, word) in chunk.chunks_exact(4).enumerate().take(16) {
            schedule[index] = u32::from_be_bytes([word[0], word[1], word[2], word[3]]);
        }
        for index in 16..64 {
            let s0 = schedule[index - 15].rotate_right(7)
                ^ schedule[index - 15].rotate_right(18)
                ^ (schedule[index - 15] >> 3);
            let s1 = schedule[index - 2].rotate_right(17)
                ^ schedule[index - 2].rotate_right(19)
                ^ (schedule[index - 2] >> 10);
            schedule[index] = schedule[index - 16]
                .wrapping_add(s0)
                .wrapping_add(schedule[index - 7])
                .wrapping_add(s1);
        }

        let mut a = state[0];
        let mut b = state[1];
        let mut c = state[2];
        let mut d = state[3];
        let mut e = state[4];
        let mut f = state[5];
        let mut g = state[6];
        let mut h = state[7];

        for index in 0..64 {
            let sum1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let choose = (e & f) ^ ((!e) & g);
            let temp1 = h
                .wrapping_add(sum1)
                .wrapping_add(choose)
                .wrapping_add(ROUND[index])
                .wrapping_add(schedule[index]);
            let sum0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let majority = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = sum0.wrapping_add(majority);

            h = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        state[0] = state[0].wrapping_add(a);
        state[1] = state[1].wrapping_add(b);
        state[2] = state[2].wrapping_add(c);
        state[3] = state[3].wrapping_add(d);
        state[4] = state[4].wrapping_add(e);
        state[5] = state[5].wrapping_add(f);
        state[6] = state[6].wrapping_add(g);
        state[7] = state[7].wrapping_add(h);
    }

    let mut output = [0_u8; 32];
    for (index, word) in state.into_iter().enumerate() {
        output[index * 4..index * 4 + 4].copy_from_slice(&word.to_be_bytes());
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sha256_matches_known_vector() {
        assert_eq!(
            sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn source_admission_refuses_wrong_authority_owner() {
        let moved = ECOSYSTEM_LOCK
            .replace(
                "chatman-ecosystem|14cfd7b01aac25b3271963378d07357eb0c55af6|actuation-authority",
                "chatman-ecosystem|14cfd7b01aac25b3271963378d07357eb0c55af6|semantic-admission",
            )
            .replace(
                "unrdf|a7b5a907d029dbca1af1bc2734ef1f7fb981a98d|semantic-admission",
                "unrdf|a7b5a907d029dbca1af1bc2734ef1f7fb981a98d|actuation-authority",
            );
        assert_eq!(
            admit_source_graph(&moved),
            Err(Refusal::AuthorityOwnerMismatch)
        );
    }

    #[test]
    fn broker_receipts_success_mutation_and_denial() {
        let checkpoint = phase_zero().expect("phase zero");
        let phase = phase_one(&checkpoint).expect("phase one");
        assert_eq!(phase.standing, Standing::Alive);
        assert!(phase.evidence.contains("mutated-action"));
    }

    #[test]
    fn gateway_proves_channels_identity_and_content_fences() {
        let phase_zero = phase_zero().expect("phase zero");
        let phase_one = phase_one(&phase_zero).expect("phase one");
        let phase = phase_two(&phase_one).expect("phase two");
        assert_eq!(phase.standing, Standing::Alive);
        assert!(phase.evidence.contains("prompt-content=no authority"));
    }

    #[test]
    fn wasm_proves_import_digest_and_fuel_fences() {
        let phase_zero = phase_zero().expect("phase zero");
        let phase_one = phase_one(&phase_zero).expect("phase one");
        let phase_two = phase_two(&phase_one).expect("phase two");
        let phase = phase_three(&phase_two).expect("phase three");
        assert_eq!(phase.standing, Standing::Alive);
        assert!(phase.evidence.contains("undeclared-import+digest+fuel"));
    }
}
