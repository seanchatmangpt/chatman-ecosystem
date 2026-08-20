//! HDITC / `DfCM` execution kernel.
//!
//! This crate turns the book-level algebra into executable invariants:
//! reversible candidate preservation, exact-subject admission, explicit
//! authority, pre-actuation receipt reservation, postcondition observation,
//! reconciliation, durable outcome receipts, and replay without actuation.
//!
//! It deliberately does not treat dimensionality, opacity, or cognitive
//! difficulty as a cryptographic hardness assumption.

use async_trait::async_trait;
use ecosystem_core::{Authority, ExactSubject, Standing};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use tokio::sync::Mutex;

pub type Dimensions = BTreeMap<String, String>;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RefusalCode {
    InvalidSubject,
    SubjectMismatch,
    CriticalUnknown,
    StaleObservation,
    IrreversibleCandidate,
    ConstraintClosure,
    AuthorityMismatch,
    AuthorityBound,
    MissingIdempotency,
    MissingPostcondition,
    InvalidReservation,
    ReceiptIntegrity,
    NoLawfulCandidate,
}

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("REFUSED:{code:?}:{detail}")]
    Refused { code: RefusalCode, detail: String },
    #[error("BLOCKED:JOURNAL:{0}")]
    Journal(String),
    #[error("BLOCKED:FINALIZE_AFTER_ACTUATION reservation={reservation}: {detail}")]
    FinalizeAfterActuation { reservation: String, detail: String },
    #[error("BLOCKED:SERIALIZATION:{0}")]
    Serialization(String),
    #[error("BLOCKED:REPLAY:{0}")]
    Replay(String),
}

fn refused(code: RefusalCode, detail: impl Into<String>) -> Error {
    Error::Refused {
        code,
        detail: detail.into(),
    }
}

fn canonical_digest<T: Serialize>(value: &T) -> Result<String, Error> {
    let bytes =
        serde_json::to_vec(value).map_err(|error| Error::Serialization(error.to_string()))?;
    Ok(format!("blake3:{}", blake3::hash(&bytes).to_hex()))
}

fn valid_digest(value: &str) -> bool {
    value
        .strip_prefix("blake3:")
        .is_some_and(|hex| hex.len() == 64 && hex.chars().all(|c| c.is_ascii_hexdigit()))
}

fn nonempty(value: &str, field: &str) -> Result<(), Error> {
    if value.trim().is_empty() {
        Err(refused(
            RefusalCode::ConstraintClosure,
            format!("{field} must be non-empty"),
        ))
    } else {
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct World {
    pub subject: ExactSubject,
    #[serde(default)]
    pub dimensions: Dimensions,
    #[serde(default)]
    pub critical_unknown: BTreeSet<String>,
    #[serde(default)]
    pub evidence_digests: BTreeSet<String>,
}

impl World {
    /// Validates exact subject identity and the evidence/unknown carriers.
    ///
    /// # Errors
    /// Returns a typed refusal when the world cannot be admitted.
    pub fn validate(&self) -> Result<(), Error> {
        self.subject
            .validate()
            .map_err(|error| refused(RefusalCode::InvalidSubject, error.to_string()))?;
        for key in self.dimensions.keys().chain(self.critical_unknown.iter()) {
            nonempty(key, "dimension")?;
        }
        for digest in &self.evidence_digests {
            if !valid_digest(digest) {
                return Err(refused(
                    RefusalCode::ConstraintClosure,
                    format!("invalid evidence digest `{digest}`"),
                ));
            }
        }
        Ok(())
    }

    /// Returns a deterministic content identity for this observed world.
    ///
    /// # Errors
    /// Returns a serialization error if the world cannot be encoded.
    pub fn digest(&self) -> Result<String, Error> {
        canonical_digest(self)
    }

    fn knows(&self, dimensions: &BTreeSet<String>) -> bool {
        self.critical_unknown.is_disjoint(dimensions)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Constraint {
    Present { dimension: String },
    Absent { dimension: String },
    Equals { dimension: String, value: String },
    NotEquals { dimension: String, value: String },
}

impl Constraint {
    #[must_use]
    pub fn dimension(&self) -> &str {
        match self {
            Self::Present { dimension }
            | Self::Absent { dimension }
            | Self::Equals { dimension, .. }
            | Self::NotEquals { dimension, .. } => dimension,
        }
    }

    #[must_use]
    pub fn holds(&self, dimensions: &Dimensions) -> bool {
        match self {
            Self::Present { dimension } => dimensions.contains_key(dimension),
            Self::Absent { dimension } => !dimensions.contains_key(dimension),
            Self::Equals { dimension, value } => dimensions
                .get(dimension)
                .is_some_and(|actual| actual == value),
            Self::NotEquals { dimension, value } => dimensions
                .get(dimension)
                .is_some_and(|actual| actual != value),
        }
    }
}

fn normalize_constraints(values: &[Constraint]) -> Vec<Constraint> {
    let mut normalized = values.to_vec();
    normalized.sort();
    normalized.dedup();
    normalized
}

fn constraints_hold(values: &[Constraint], dimensions: &Dimensions) -> bool {
    values.iter().all(|constraint| constraint.holds(dimensions))
}

fn constraint_dimensions(values: &[Constraint]) -> BTreeSet<String> {
    values
        .iter()
        .map(|constraint| constraint.dimension().to_owned())
        .collect()
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Mutation {
    pub dimension: String,
    pub before: Option<String>,
    pub after: Option<String>,
}

impl Mutation {
    fn apply(&self, dimensions: &mut Dimensions) -> Result<(), Error> {
        nonempty(&self.dimension, "mutation dimension")?;
        match (dimensions.get(&self.dimension), self.before.as_ref()) {
            (Some(actual), Some(expected)) if actual == expected => {}
            (None, None) => {}
            (actual, expected) => {
                return Err(refused(
                    RefusalCode::StaleObservation,
                    format!(
                        "dimension `{}` expected {:?}, observed {:?}",
                        self.dimension, expected, actual
                    ),
                ));
            }
        }

        if let Some(after) = &self.after {
            dimensions.insert(self.dimension.clone(), after.clone());
        } else {
            dimensions.remove(&self.dimension);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Candidate {
    pub id: String,
    pub subject: ExactSubject,
    pub command: String,
    pub idempotency_key: String,
    pub required_authority: Authority,
    pub reversible: bool,
    pub option_preservation: u64,
    pub information_gain_millibits: u64,
    pub cost_microunits: u64,
    #[serde(default)]
    pub requires_known: BTreeSet<String>,
    #[serde(default)]
    pub mutations: Vec<Mutation>,
    #[serde(default)]
    pub construction_constraints: Vec<Constraint>,
}

impl Candidate {
    /// Deterministically projects the candidate without actuating it.
    ///
    /// # Errors
    /// Returns a typed refusal if identity, reversibility, knowledge, stale-state,
    /// or construction constraints do not admit this candidate.
    pub fn project(&self, world: &World) -> Result<Dimensions, Error> {
        world.validate()?;
        self.subject
            .validate()
            .map_err(|error| refused(RefusalCode::InvalidSubject, error.to_string()))?;
        if self.subject != world.subject {
            return Err(refused(
                RefusalCode::SubjectMismatch,
                "candidate and world subjects differ",
            ));
        }
        nonempty(&self.id, "candidate id")?;
        nonempty(&self.command, "command")?;
        if self.idempotency_key.trim().is_empty() {
            return Err(refused(
                RefusalCode::MissingIdempotency,
                "DO candidates require an idempotency key",
            ));
        }
        if !self.reversible {
            return Err(refused(
                RefusalCode::IrreversibleCandidate,
                format!(
                    "candidate `{}` is not admitted during reversible search",
                    self.id
                ),
            ));
        }
        if !world.knows(&self.requires_known) {
            let unknown = world
                .critical_unknown
                .intersection(&self.requires_known)
                .cloned()
                .collect::<Vec<_>>();
            return Err(refused(
                RefusalCode::CriticalUnknown,
                format!("candidate `{}` depends on UNKNOWN {unknown:?}", self.id),
            ));
        }

        let mut projected = world.dimensions.clone();
        for mutation in &self.mutations {
            mutation.apply(&mut projected)?;
        }
        let constraints = normalize_constraints(&self.construction_constraints);
        if !constraints_hold(&constraints, &projected) {
            return Err(refused(
                RefusalCode::ConstraintClosure,
                format!("candidate `{}` violates construction constraints", self.id),
            ));
        }
        Ok(projected)
    }

    /// Returns the deterministic BLAKE3 identity of this candidate.
    ///
    /// # Errors
    /// Returns a serialization error if the candidate cannot be encoded.
    pub fn digest(&self) -> Result<String, Error> {
        canonical_digest(self)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExcludedCandidate {
    pub id: String,
    pub reason: RefusalCode,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DfcmFrontier {
    /// Every currently lawful reversible option, in deterministic preference order.
    pub lawful: Vec<Candidate>,
    /// Exclusions remain visible as topology rather than collapsing the graph.
    pub excluded: Vec<ExcludedCandidate>,
}

impl DfcmFrontier {
    #[must_use]
    pub fn best(&self) -> Option<&Candidate> {
        self.lawful.first()
    }
}

/// Builds the maximal lawful reversible frontier.
///
/// The function is SELECT/CONSTRUCT-only. It never actuates. One failed edge is
/// retained in `excluded`; it does not collapse the remaining graph.
#[must_use]
pub fn dfcm_frontier(
    world: &World,
    candidates: impl IntoIterator<Item = Candidate>,
) -> DfcmFrontier {
    let mut lawful = Vec::new();
    let mut excluded = Vec::new();

    for candidate in candidates {
        match candidate.project(world) {
            Ok(_) => lawful.push(candidate),
            Err(Error::Refused { code, .. }) => excluded.push(ExcludedCandidate {
                id: candidate.id,
                reason: code,
            }),
            Err(_) => excluded.push(ExcludedCandidate {
                id: candidate.id,
                reason: RefusalCode::ConstraintClosure,
            }),
        }
    }

    lawful.sort_by(|left, right| {
        right
            .option_preservation
            .cmp(&left.option_preservation)
            .then_with(|| {
                right
                    .information_gain_millibits
                    .cmp(&left.information_gain_millibits)
            })
            .then_with(|| left.cost_microunits.cmp(&right.cost_microunits))
            .then_with(|| left.id.cmp(&right.id))
    });
    excluded.sort_by(|left, right| left.id.cmp(&right.id));

    DfcmFrontier { lawful, excluded }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthorityGrant {
    pub id: String,
    pub subject: ExactSubject,
    pub authority: Authority,
    #[serde(default)]
    pub consequence_bound: Vec<Constraint>,
    pub nonce: String,
    pub issued_at: String,
    #[serde(default)]
    pub digest: String,
}

impl AuthorityGrant {
    fn unsigned(&self) -> Self {
        let mut copy = self.clone();
        copy.digest.clear();
        copy.consequence_bound = normalize_constraints(&copy.consequence_bound);
        copy
    }

    /// Seals this exact-subject authority grant.
    ///
    /// # Errors
    /// Returns a typed refusal or serialization error when the grant is invalid.
    pub fn seal(&mut self) -> Result<(), Error> {
        self.subject
            .validate()
            .map_err(|error| refused(RefusalCode::InvalidSubject, error.to_string()))?;
        nonempty(&self.id, "authority grant id")?;
        nonempty(&self.nonce, "authority nonce")?;
        nonempty(&self.issued_at, "authority issued_at")?;
        self.consequence_bound = normalize_constraints(&self.consequence_bound);
        self.digest = canonical_digest(&self.unsigned())?;
        Ok(())
    }

    /// Verifies grant integrity and exact authority/subject alignment.
    ///
    /// # Errors
    /// Returns a typed refusal when the grant is malformed, tampered, or mis-scoped.
    pub fn verify_for(&self, candidate: &Candidate) -> Result<(), Error> {
        if self.subject != candidate.subject {
            return Err(refused(
                RefusalCode::SubjectMismatch,
                "authority grant subject differs from candidate",
            ));
        }
        if !self.authority.permits(candidate.required_authority) {
            return Err(refused(
                RefusalCode::AuthorityMismatch,
                format!(
                    "grant has {:?}, candidate requires {:?}",
                    self.authority, candidate.required_authority
                ),
            ));
        }
        if !valid_digest(&self.digest) || self.digest != canonical_digest(&self.unsigned())? {
            return Err(refused(
                RefusalCode::AuthorityMismatch,
                "authority grant digest mismatch",
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReceiptReservation {
    pub id: String,
    pub subject: ExactSubject,
    pub candidate_digest: String,
    pub grant_digest: String,
    pub before_digest: String,
    pub expected_digest: String,
    pub idempotency_key: String,
    #[serde(default)]
    pub digest: String,
}

impl ReceiptReservation {
    fn unsigned(&self) -> Self {
        let mut copy = self.clone();
        copy.digest.clear();
        copy
    }

    fn seal(&mut self) -> Result<(), Error> {
        self.digest = canonical_digest(&self.unsigned())?;
        Ok(())
    }

    /// Verifies the pre-actuation receipt reservation.
    ///
    /// # Errors
    /// Returns a typed refusal when any identity or digest is invalid.
    pub fn verify(&self) -> Result<(), Error> {
        self.subject
            .validate()
            .map_err(|error| refused(RefusalCode::InvalidSubject, error.to_string()))?;
        if self.idempotency_key.trim().is_empty() {
            return Err(refused(
                RefusalCode::MissingIdempotency,
                "reservation idempotency key is empty",
            ));
        }
        for digest in [
            &self.candidate_digest,
            &self.grant_digest,
            &self.before_digest,
            &self.expected_digest,
            &self.digest,
        ] {
            if !valid_digest(digest) {
                return Err(refused(
                    RefusalCode::InvalidReservation,
                    format!("invalid reservation digest `{digest}`"),
                ));
            }
        }
        if self.digest != canonical_digest(&self.unsigned())? {
            return Err(refused(
                RefusalCode::InvalidReservation,
                "reservation digest mismatch",
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PreparedDo {
    pub candidate: Candidate,
    pub grant: AuthorityGrant,
    pub expected_postconditions: Vec<Constraint>,
    pub projected_dimensions: Dimensions,
    pub reservation: ReceiptReservation,
}

impl PreparedDo {
    /// Admits one candidate for DO and manufactures its receipt reservation.
    ///
    /// This is the SELECT/CONSTRUCT -> DO boundary. The caller still may not
    /// actuate until a [`ReceiptJournal`] durably reserves `reservation`.
    ///
    /// # Errors
    /// Returns a typed refusal when exact subject, knowledge, authority, bounds,
    /// or expected postconditions fail to close.
    pub fn prepare(
        world: &World,
        candidate: Candidate,
        grant: AuthorityGrant,
        expected_postconditions: impl AsRef<[Constraint]>,
    ) -> Result<Self, Error> {
        let projected_dimensions = candidate.project(world)?;
        grant.verify_for(&candidate)?;
        let expected_postconditions = normalize_constraints(expected_postconditions.as_ref());
        if expected_postconditions.is_empty() {
            return Err(refused(
                RefusalCode::MissingPostcondition,
                "DO requires at least one observed postcondition",
            ));
        }

        let required_dimensions = constraint_dimensions(&expected_postconditions)
            .union(&constraint_dimensions(&grant.consequence_bound))
            .cloned()
            .collect::<BTreeSet<_>>();
        if !world.knows(&required_dimensions) {
            return Err(refused(
                RefusalCode::CriticalUnknown,
                "postcondition or authority bound depends on UNKNOWN",
            ));
        }
        if !constraints_hold(&expected_postconditions, &projected_dimensions) {
            return Err(refused(
                RefusalCode::ConstraintClosure,
                "projected world does not satisfy expected postconditions",
            ));
        }
        if !constraints_hold(&grant.consequence_bound, &projected_dimensions) {
            return Err(refused(
                RefusalCode::AuthorityBound,
                "projected consequence exceeds authority grant",
            ));
        }

        let candidate_digest = candidate.digest()?;
        let before_digest = world.digest()?;
        let expected_digest = canonical_digest(&expected_postconditions)?;
        let reservation_seed = canonical_digest(&(
            &candidate_digest,
            &grant.digest,
            &before_digest,
            &expected_digest,
            &candidate.idempotency_key,
        ))?;
        let reservation_id = reservation_seed.strip_prefix("blake3:").map_or_else(
            || "receipt:invalid".to_owned(),
            |hex| format!("receipt:{}", &hex[..32]),
        );
        let mut reservation = ReceiptReservation {
            id: reservation_id,
            subject: candidate.subject.clone(),
            candidate_digest,
            grant_digest: grant.digest.clone(),
            before_digest,
            expected_digest,
            idempotency_key: candidate.idempotency_key.clone(),
            digest: String::new(),
        };
        reservation.seal()?;
        reservation.verify()?;

        Ok(Self {
            candidate,
            grant,
            expected_postconditions,
            projected_dimensions,
            reservation,
        })
    }

    /// Re-verifies the prepared DO carrier before the runtime reserves it.
    ///
    /// # Errors
    /// Returns a typed refusal when any binding has drifted.
    pub fn verify(&self) -> Result<(), Error> {
        self.candidate
            .subject
            .validate()
            .map_err(|error| refused(RefusalCode::InvalidSubject, error.to_string()))?;
        self.grant.verify_for(&self.candidate)?;
        self.reservation.verify()?;
        if self.reservation.subject != self.candidate.subject
            || self.reservation.candidate_digest != self.candidate.digest()?
            || self.reservation.grant_digest != self.grant.digest
            || self.reservation.expected_digest
                != canonical_digest(&normalize_constraints(&self.expected_postconditions))?
            || self.reservation.idempotency_key != self.candidate.idempotency_key
        {
            return Err(refused(
                RefusalCode::InvalidReservation,
                "prepared DO bindings drifted",
            ));
        }
        if !constraints_hold(&self.expected_postconditions, &self.projected_dimensions)
            || !constraints_hold(&self.grant.consequence_bound, &self.projected_dimensions)
        {
            return Err(refused(
                RefusalCode::ConstraintClosure,
                "prepared projected world no longer closes",
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ActuationSignal {
    Acknowledged { token: String },
    Refused { reason: String },
    Ambiguous { reason: String },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DoOutcome {
    Done,
    Blocked,
    Ambiguous,
    Refused,
}

impl DoOutcome {
    #[must_use]
    pub const fn standing(self) -> Standing {
        match self {
            Self::Done => Standing::Alive,
            Self::Blocked | Self::Ambiguous => Standing::Blocked,
            Self::Refused => Standing::Rejected,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DoReceipt {
    pub reservation_id: String,
    pub reservation_digest: String,
    pub subject: ExactSubject,
    pub candidate_digest: String,
    pub grant_digest: String,
    pub before_digest: String,
    pub expected_postconditions: Vec<Constraint>,
    pub admitted_consequence_bound: Vec<Constraint>,
    pub actuation: ActuationSignal,
    pub observed_digest: Option<String>,
    pub verified: Vec<String>,
    pub outcome: DoOutcome,
    pub replay_key: String,
    #[serde(default)]
    pub digest: String,
}

impl DoReceipt {
    fn unsigned(&self) -> Self {
        let mut copy = self.clone();
        copy.digest.clear();
        copy.expected_postconditions = normalize_constraints(&copy.expected_postconditions);
        copy.admitted_consequence_bound = normalize_constraints(&copy.admitted_consequence_bound);
        copy
    }

    fn seal(&mut self) -> Result<(), Error> {
        self.expected_postconditions = normalize_constraints(&self.expected_postconditions);
        self.admitted_consequence_bound = normalize_constraints(&self.admitted_consequence_bound);
        self.digest = canonical_digest(&self.unsigned())?;
        Ok(())
    }

    /// Verifies receipt integrity and the rule `ACTUATED != DONE`.
    ///
    /// # Errors
    /// Returns a typed refusal when the receipt is malformed or claims DONE
    /// without acknowledged actuation, observed consequence, and verification.
    pub fn verify(&self) -> Result<(), Error> {
        if !valid_digest(&self.digest) || self.digest != canonical_digest(&self.unsigned())? {
            return Err(refused(
                RefusalCode::ReceiptIntegrity,
                "DO receipt digest mismatch",
            ));
        }
        for digest in [
            &self.reservation_digest,
            &self.candidate_digest,
            &self.grant_digest,
            &self.before_digest,
        ] {
            if !valid_digest(digest) {
                return Err(refused(
                    RefusalCode::ReceiptIntegrity,
                    format!("invalid bound digest `{digest}`"),
                ));
            }
        }
        if self.replay_key.trim().is_empty() {
            return Err(refused(
                RefusalCode::ReceiptIntegrity,
                "replay key is empty",
            ));
        }
        if self.outcome == DoOutcome::Done
            && (!matches!(self.actuation, ActuationSignal::Acknowledged { .. })
                || self
                    .observed_digest
                    .as_ref()
                    .is_none_or(|digest| !valid_digest(digest))
                || self.verified.is_empty())
        {
            return Err(refused(
                RefusalCode::ReceiptIntegrity,
                "DONE requires acknowledged actuation, observed digest, and verification",
            ));
        }
        Ok(())
    }
}

#[async_trait]
pub trait ReceiptJournal: Send + Sync {
    /// Durably reserves a receipt before any consequential actuation.
    async fn reserve(&self, reservation: &ReceiptReservation) -> Result<(), String>;

    /// Persists the reconciled outcome against an existing reservation.
    async fn finalize(&self, receipt: &DoReceipt) -> Result<(), String>;
}

#[async_trait]
pub trait Actuator: Send + Sync {
    /// Executes one already-admitted consequential operation.
    async fn actuate(&self, prepared: &PreparedDo) -> ActuationSignal;

    /// Observes the exact subject after the actuation attempt.
    async fn observe(&self, subject: &ExactSubject) -> Result<World, String>;
}

#[derive(Debug)]
pub struct BrceExecutor<J, A> {
    journal: J,
    actuator: A,
}

impl<J, A> BrceExecutor<J, A>
where
    J: ReceiptJournal,
    A: Actuator,
{
    #[must_use]
    pub const fn new(journal: J, actuator: A) -> Self {
        Self { journal, actuator }
    }

    /// Executes the exclusive DO path.
    ///
    /// Order is fixed:
    /// PREPARE -> durable reservation -> ACTUATE -> OBSERVE -> RECONCILE ->
    /// final receipt. There is no human fallback edge and no automatic retry
    /// after an ambiguous actuation.
    ///
    /// # Errors
    /// Returns before actuation if reservation persistence fails. If final
    /// persistence fails after actuation, the error carries the durable
    /// reservation identity so reconciliation can continue without blind retry.
    pub async fn execute(&self, prepared: PreparedDo) -> Result<DoReceipt, Error> {
        prepared.verify()?;
        self.journal
            .reserve(&prepared.reservation)
            .await
            .map_err(Error::Journal)?;

        let actuation = self.actuator.actuate(&prepared).await;
        let observation = self.actuator.observe(&prepared.candidate.subject).await;

        let (observed_digest, observed_world, observation_error) = match observation {
            Ok(world) => {
                let digest = world.digest()?;
                (Some(digest), Some(world), None)
            }
            Err(error) => (None, None, Some(error)),
        };

        let acknowledged = matches!(actuation, ActuationSignal::Acknowledged { .. });
        let explicitly_refused = matches!(actuation, ActuationSignal::Refused { .. });
        let actuation_ambiguous = matches!(actuation, ActuationSignal::Ambiguous { .. });

        let reconciled = observed_world.as_ref().is_some_and(|world| {
            world.subject == prepared.candidate.subject
                && world.validate().is_ok()
                && world.knows(&constraint_dimensions(&prepared.expected_postconditions))
                && world.knows(&constraint_dimensions(&prepared.grant.consequence_bound))
                && constraints_hold(&prepared.expected_postconditions, &world.dimensions)
                && constraints_hold(&prepared.grant.consequence_bound, &world.dimensions)
        });

        let outcome = if explicitly_refused {
            DoOutcome::Refused
        } else if actuation_ambiguous || observation_error.is_some() {
            DoOutcome::Ambiguous
        } else if acknowledged && reconciled {
            DoOutcome::Done
        } else {
            DoOutcome::Blocked
        };

        let mut verified = Vec::new();
        if acknowledged {
            verified.push("actuation_acknowledged".to_owned());
        }
        if reconciled {
            verified.push("postconditions_observed".to_owned());
            verified.push("authority_bound_observed".to_owned());
            verified.push("exact_subject_reconciled".to_owned());
        }
        if observation_error.is_some() {
            verified.push("post_actuation_observation_failed".to_owned());
        }

        let replay_key =
            canonical_digest(&(&prepared.reservation.digest, &observed_digest, outcome))?;
        let mut receipt = DoReceipt {
            reservation_id: prepared.reservation.id.clone(),
            reservation_digest: prepared.reservation.digest.clone(),
            subject: prepared.candidate.subject.clone(),
            candidate_digest: prepared.reservation.candidate_digest.clone(),
            grant_digest: prepared.reservation.grant_digest.clone(),
            before_digest: prepared.reservation.before_digest.clone(),
            expected_postconditions: prepared.expected_postconditions.clone(),
            admitted_consequence_bound: prepared.grant.consequence_bound.clone(),
            actuation,
            observed_digest,
            verified,
            outcome,
            replay_key,
            digest: String::new(),
        };
        receipt.seal()?;
        receipt.verify()?;

        self.journal
            .finalize(&receipt)
            .await
            .map_err(|detail| Error::FinalizeAfterActuation {
                reservation: receipt.reservation_id.clone(),
                detail,
            })?;
        Ok(receipt)
    }
}

/// Re-verifies a completed DO receipt against a fresh observation.
///
/// Replay is verification-only and has no actuator argument, so replay cannot
/// acquire ambient execution authority.
///
/// # Errors
/// Returns a replay error if the receipt, exact subject, observed digest, or
/// admitted postconditions no longer match.
pub fn replay(receipt: &DoReceipt, observed: &World) -> Result<Standing, Error> {
    receipt.verify()?;
    observed.validate()?;
    if receipt.outcome != DoOutcome::Done {
        return Err(Error::Replay(format!(
            "receipt outcome {:?} has no ALIVE replay standing",
            receipt.outcome
        )));
    }
    if observed.subject != receipt.subject {
        return Err(Error::Replay("exact subject changed".into()));
    }
    let observed_digest = observed.digest()?;
    if receipt.observed_digest.as_deref() != Some(observed_digest.as_str()) {
        return Err(Error::Replay("observed world digest changed".into()));
    }
    let known = constraint_dimensions(&receipt.expected_postconditions)
        .union(&constraint_dimensions(&receipt.admitted_consequence_bound))
        .cloned()
        .collect::<BTreeSet<_>>();
    if !observed.knows(&known)
        || !constraints_hold(&receipt.expected_postconditions, &observed.dimensions)
        || !constraints_hold(&receipt.admitted_consequence_bound, &observed.dimensions)
    {
        return Err(Error::Replay("replay postcondition closure failed".into()));
    }
    Ok(Standing::Alive)
}

#[derive(Debug, Default)]
pub struct MemoryReceiptJournal {
    reservations: Mutex<BTreeMap<String, ReceiptReservation>>,
    receipts: Mutex<BTreeMap<String, DoReceipt>>,
}

impl MemoryReceiptJournal {
    pub async fn reservation_count(&self) -> usize {
        self.reservations.lock().await.len()
    }

    pub async fn receipt_count(&self) -> usize {
        self.receipts.lock().await.len()
    }
}

#[async_trait]
impl ReceiptJournal for MemoryReceiptJournal {
    async fn reserve(&self, reservation: &ReceiptReservation) -> Result<(), String> {
        reservation.verify().map_err(|error| error.to_string())?;
        let mut reservations = self.reservations.lock().await;
        if let Some(existing) = reservations.get(&reservation.id) {
            if existing == reservation {
                return Ok(());
            }
            return Err("reservation id collision".into());
        }
        reservations.insert(reservation.id.clone(), reservation.clone());
        Ok(())
    }

    async fn finalize(&self, receipt: &DoReceipt) -> Result<(), String> {
        receipt.verify().map_err(|error| error.to_string())?;
        let reservations = self.reservations.lock().await;
        let Some(reservation) = reservations.get(&receipt.reservation_id) else {
            return Err("finalize without reservation".into());
        };
        if reservation.digest != receipt.reservation_digest {
            return Err("receipt does not bind reserved digest".into());
        }
        drop(reservations);

        let mut receipts = self.receipts.lock().await;
        if let Some(existing) = receipts.get(&receipt.reservation_id) {
            if existing == receipt {
                return Ok(());
            }
            return Err("non-idempotent final receipt".into());
        }
        receipts.insert(receipt.reservation_id.clone(), receipt.clone());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{
        Arc,
        atomic::{AtomicBool, AtomicUsize, Ordering},
    };

    fn subject() -> Result<ExactSubject, Error> {
        let repository = ecosystem_core::RepositoryId::parse("repository:fixture")
            .map_err(|error| refused(RefusalCode::InvalidSubject, error.to_string()))?;
        Ok(ExactSubject::GitCommit {
            repository,
            sha: "0123456789abcdef0123456789abcdef01234567".into(),
        })
    }

    fn evidence() -> String {
        format!("blake3:{}", "0".repeat(64))
    }

    fn world(state: &str) -> Result<World, Error> {
        Ok(World {
            subject: subject()?,
            dimensions: BTreeMap::from([
                ("service.state".into(), state.into()),
                ("blast.radius".into(), "bounded".into()),
            ]),
            critical_unknown: BTreeSet::new(),
            evidence_digests: BTreeSet::from([evidence()]),
        })
    }

    fn candidate(id: &str, reversible: bool, preservation: u64) -> Result<Candidate, Error> {
        Ok(Candidate {
            id: id.into(),
            subject: subject()?,
            command: "set service.state=ready".into(),
            idempotency_key: format!("idem-{id}"),
            required_authority: Authority::ModifyExternalObject,
            reversible,
            option_preservation: preservation,
            information_gain_millibits: 1_000,
            cost_microunits: 10,
            requires_known: BTreeSet::from(["service.state".into()]),
            mutations: vec![Mutation {
                dimension: "service.state".into(),
                before: Some("pending".into()),
                after: Some("ready".into()),
            }],
            construction_constraints: vec![Constraint::Equals {
                dimension: "blast.radius".into(),
                value: "bounded".into(),
            }],
        })
    }

    fn grant() -> Result<AuthorityGrant, Error> {
        let mut grant = AuthorityGrant {
            id: "authority:hditc-fixture".into(),
            subject: subject()?,
            authority: Authority::ModifyExternalObject,
            consequence_bound: vec![
                Constraint::Equals {
                    dimension: "service.state".into(),
                    value: "ready".into(),
                },
                Constraint::Equals {
                    dimension: "blast.radius".into(),
                    value: "bounded".into(),
                },
            ],
            nonce: "nonce-1".into(),
            issued_at: "2026-08-19T23:00:00Z".into(),
            digest: String::new(),
        };
        grant.seal()?;
        Ok(grant)
    }

    fn prepare() -> Result<PreparedDo, Error> {
        PreparedDo::prepare(
            &world("pending")?,
            candidate("best", true, 100)?,
            grant()?,
            vec![Constraint::Equals {
                dimension: "service.state".into(),
                value: "ready".into(),
            }],
        )
    }

    #[test]
    fn dfcm_preserves_lawful_frontier_and_fences_irreversible_edges() -> Result<(), Error> {
        let frontier = dfcm_frontier(
            &world("pending")?,
            vec![
                candidate("low", true, 10)?,
                candidate("high", true, 100)?,
                candidate("irreversible", false, 10_000)?,
            ],
        );
        assert_eq!(frontier.lawful.len(), 2);
        assert_eq!(frontier.best().map(|item| item.id.as_str()), Some("high"));
        assert_eq!(frontier.excluded.len(), 1);
        assert_eq!(
            frontier.excluded[0].reason,
            RefusalCode::IrreversibleCandidate
        );
        Ok(())
    }

    #[test]
    fn critical_unknown_refuses_admission() -> Result<(), Error> {
        let mut observed = world("pending")?;
        observed.critical_unknown.insert("service.state".into());
        let outcome = PreparedDo::prepare(
            &observed,
            candidate("unknown", true, 10)?,
            grant()?,
            vec![Constraint::Equals {
                dimension: "service.state".into(),
                value: "ready".into(),
            }],
        );
        assert!(matches!(
            outcome,
            Err(Error::Refused {
                code: RefusalCode::CriticalUnknown,
                ..
            })
        ));
        Ok(())
    }

    #[test]
    fn exact_authority_and_subject_are_not_inferred() -> Result<(), Error> {
        let mut wrong = grant()?;
        wrong.authority = Authority::Draft;
        wrong.seal()?;
        let outcome = PreparedDo::prepare(
            &world("pending")?,
            candidate("authority", true, 10)?,
            wrong,
            vec![Constraint::Equals {
                dimension: "service.state".into(),
                value: "ready".into(),
            }],
        );
        assert!(matches!(
            outcome,
            Err(Error::Refused {
                code: RefusalCode::AuthorityMismatch,
                ..
            })
        ));
        Ok(())
    }

    #[derive(Debug)]
    struct ScriptedActuator {
        signal: ActuationSignal,
        observed: Result<World, String>,
        calls: Arc<AtomicUsize>,
        reserved: Option<Arc<AtomicBool>>,
    }

    #[async_trait]
    impl Actuator for ScriptedActuator {
        async fn actuate(&self, _prepared: &PreparedDo) -> ActuationSignal {
            self.calls.fetch_add(1, Ordering::SeqCst);
            if self
                .reserved
                .as_ref()
                .is_some_and(|flag| !flag.load(Ordering::SeqCst))
            {
                return ActuationSignal::Ambiguous {
                    reason: "actuated before reservation".into(),
                };
            }
            self.signal.clone()
        }

        async fn observe(&self, _subject: &ExactSubject) -> Result<World, String> {
            self.observed.clone()
        }
    }

    #[derive(Debug)]
    struct FlagJournal {
        reserved: Arc<AtomicBool>,
        fail_reserve: bool,
        finalized: Arc<AtomicUsize>,
    }

    #[async_trait]
    impl ReceiptJournal for FlagJournal {
        async fn reserve(&self, reservation: &ReceiptReservation) -> Result<(), String> {
            reservation.verify().map_err(|error| error.to_string())?;
            if self.fail_reserve {
                return Err("durable reservation unavailable".into());
            }
            self.reserved.store(true, Ordering::SeqCst);
            Ok(())
        }

        async fn finalize(&self, receipt: &DoReceipt) -> Result<(), String> {
            receipt.verify().map_err(|error| error.to_string())?;
            self.finalized.fetch_add(1, Ordering::SeqCst);
            Ok(())
        }
    }

    #[tokio::test]
    async fn zero_unreceipted_actuation_is_executed_not_documented() -> Result<(), Error> {
        let reserved = Arc::new(AtomicBool::new(false));
        let calls = Arc::new(AtomicUsize::new(0));
        let finalized = Arc::new(AtomicUsize::new(0));
        let executor = BrceExecutor::new(
            FlagJournal {
                reserved: Arc::clone(&reserved),
                fail_reserve: false,
                finalized: Arc::clone(&finalized),
            },
            ScriptedActuator {
                signal: ActuationSignal::Acknowledged {
                    token: "ack-1".into(),
                },
                observed: Ok(world("ready")?),
                calls: Arc::clone(&calls),
                reserved: Some(Arc::clone(&reserved)),
            },
        );
        let receipt = executor.execute(prepare()?).await?;
        assert_eq!(receipt.outcome, DoOutcome::Done);
        assert_eq!(receipt.outcome.standing(), Standing::Alive);
        assert_eq!(calls.load(Ordering::SeqCst), 1);
        assert_eq!(finalized.load(Ordering::SeqCst), 1);
        assert!(reserved.load(Ordering::SeqCst));
        Ok(())
    }

    #[tokio::test]
    async fn reservation_failure_means_zero_actuation() -> Result<(), Error> {
        let reserved = Arc::new(AtomicBool::new(false));
        let calls = Arc::new(AtomicUsize::new(0));
        let executor = BrceExecutor::new(
            FlagJournal {
                reserved: Arc::clone(&reserved),
                fail_reserve: true,
                finalized: Arc::new(AtomicUsize::new(0)),
            },
            ScriptedActuator {
                signal: ActuationSignal::Acknowledged {
                    token: "should-not-run".into(),
                },
                observed: Ok(world("ready")?),
                calls: Arc::clone(&calls),
                reserved: Some(Arc::clone(&reserved)),
            },
        );
        let outcome = executor.execute(prepare()?).await;
        assert!(matches!(outcome, Err(Error::Journal(_))));
        assert_eq!(calls.load(Ordering::SeqCst), 0);
        assert!(!reserved.load(Ordering::SeqCst));
        Ok(())
    }

    #[tokio::test]
    async fn actuator_acknowledgement_is_not_done() -> Result<(), Error> {
        let executor = BrceExecutor::new(
            MemoryReceiptJournal::default(),
            ScriptedActuator {
                signal: ActuationSignal::Acknowledged {
                    token: "ack-with-wrong-world".into(),
                },
                observed: Ok(world("pending")?),
                calls: Arc::new(AtomicUsize::new(0)),
                reserved: None,
            },
        );
        let receipt = executor.execute(prepare()?).await?;
        assert_eq!(receipt.outcome, DoOutcome::Blocked);
        assert_ne!(receipt.outcome.standing(), Standing::Alive);
        Ok(())
    }

    #[tokio::test]
    async fn ambiguous_actuation_is_not_retried_or_promoted() -> Result<(), Error> {
        let calls = Arc::new(AtomicUsize::new(0));
        let executor = BrceExecutor::new(
            MemoryReceiptJournal::default(),
            ScriptedActuator {
                signal: ActuationSignal::Ambiguous {
                    reason: "transport timeout after dispatch".into(),
                },
                observed: Ok(world("ready")?),
                calls: Arc::clone(&calls),
                reserved: None,
            },
        );
        let receipt = executor.execute(prepare()?).await?;
        assert_eq!(receipt.outcome, DoOutcome::Ambiguous);
        assert_eq!(calls.load(Ordering::SeqCst), 1);
        assert_ne!(receipt.outcome.standing(), Standing::Alive);
        Ok(())
    }

    #[tokio::test]
    async fn replay_is_pure_verification_of_the_exact_observed_world() -> Result<(), Error> {
        let executor = BrceExecutor::new(
            MemoryReceiptJournal::default(),
            ScriptedActuator {
                signal: ActuationSignal::Acknowledged {
                    token: "ack-replay".into(),
                },
                observed: Ok(world("ready")?),
                calls: Arc::new(AtomicUsize::new(0)),
                reserved: None,
            },
        );
        let receipt = executor.execute(prepare()?).await?;
        assert_eq!(replay(&receipt, &world("ready")?)?, Standing::Alive);
        assert!(replay(&receipt, &world("pending")?).is_err());
        Ok(())
    }
}
