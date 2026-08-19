#![allow(dead_code, clippy::doc_markdown, clippy::missing_errors_doc)]

//! Receipted paid-service admission for the external Agent Lightning runtime.

use crate::commerce::{
    CommerceContext, CommerceError, CommerceLedger, CommercialReceipt, Provider, ProviderEventKind,
    ProviderObservation, ReceiptKind,
};
use ecosystem_core::{Authority, Receipt, ReceiptId, Standing};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const REPOSITORY: &str = "https://github.com/seanchatmangpt/agent-lightning";
pub const SHA: &str = "bd80905120affc576eb383f3b4bcc35cacc0e1d0";
pub const CAPABILITY: &str = "capability:agentic-rl-training";

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("REFUSED:{0}")]
    Refused(String),
    #[error("COMMERCE:{0}")]
    Commerce(String),
    #[error("RECEIPT:{0}")]
    Receipt(String),
}
impl From<CommerceError> for Error {
    fn from(value: CommerceError) -> Self { Self::Commerce(value.to_string()) }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Mode { Hosted, Byoc, Private }

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Meter { GpuSeconds, InputTokens, OutputTokens, Rollouts }

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Workload { pub repository: String, pub sha: String, pub capability: String }
impl Workload {
    #[must_use]
    pub fn pinned() -> Self {
        Self { repository: REPOSITORY.into(), sha: SHA.into(), capability: CAPABILITY.into() }
    }
    fn admitted(&self) -> bool { self == &Self::pinned() }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Policy {
    pub workload: Workload,
    pub modes: BTreeSet<Mode>,
    pub max_per_job: BTreeMap<Meter, u64>,
}
impl Policy {
    #[must_use]
    pub fn agent_lightning() -> Self {
        Self {
            workload: Workload::pinned(),
            modes: BTreeSet::from([Mode::Hosted, Mode::Byoc, Mode::Private]),
            max_per_job: BTreeMap::from([
                (Meter::GpuSeconds, 604_800), (Meter::InputTokens, 100_000_000),
                (Meter::OutputTokens, 100_000_000), (Meter::Rollouts, 100_000),
            ]),
        }
    }
}

#[derive(Debug, Clone)]
pub struct Principal { pub organization: String, pub subject: String, pub key_fingerprint: String }
impl Principal {
    fn admitted(&self) -> bool {
        self.key_fingerprint.strip_prefix("blake3:").is_some_and(|hash| {
            !self.organization.trim().is_empty() && !self.subject.trim().is_empty()
                && hash.len() == 64 && hash.chars().all(|c| c.is_ascii_hexdigit())
        })
    }
}

#[derive(Debug, Clone)]
pub struct Grant {
    pub organization: String,
    pub plan: String,
    pub modes: BTreeSet<Mode>,
    pub quota: BTreeMap<Meter, u64>,
}

#[derive(Debug, Clone)]
pub struct JobRequest {
    pub id: String,
    pub organization: String,
    pub workload: Workload,
    pub mode: Mode,
    pub requested: BTreeMap<Meter, u64>,
    pub idempotency_key: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ReservationState { Reserved, Authorized, Reconciled }
#[derive(Debug, Clone)]
pub struct Reservation {
    pub id: String,
    pub job_id: String,
    pub workload: Workload,
    pub mode: Mode,
    pub units: BTreeMap<Meter, u64>,
    state: ReservationState,
    reserve_receipt: String,
    actuation_receipt: String,
}
#[derive(Debug, Clone)]
pub struct ActuationPermit {
    pub reservation_id: String,
    pub job_id: String,
    pub workload: Workload,
    pub mode: Mode,
    pub receipt_digest: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Kind { EntitlementBound, EntitlementSuspended, EntitlementReinstated, EntitlementRevoked, UsageReserved, ActuationAuthorized, UsageReconciled }
impl Kind {
    const fn authority(self) -> Authority {
        if matches!(self, Self::ActuationAuthorized) { Authority::ModifyExternalObject }
        else { Authority::PersistControlPlane }
    }
}
#[derive(Debug, Clone)]
struct ControlReceipt { kind: Kind, source: String, previous: String, core: Receipt }
impl ControlReceipt {
    fn verify(&self) -> Result<(), Error> {
        self.core.verify().map_err(|error| Error::Receipt(error.to_string()))?;
        if self.core.authority != self.kind.authority() { return Err(Error::Receipt("AUTHORITY_KIND_MISMATCH".into())); }
        Ok(())
    }
}
#[derive(Debug, Clone)]
struct BoundGrant { grant: Grant, commercial_subject: String, active: bool }

#[derive(Debug)]
pub struct Service {
    policy: Policy,
    timestamp: String,
    entitlement: Option<BoundGrant>,
    consumed: BTreeMap<Meter, u64>,
    reservations: BTreeMap<String, Reservation>,
    idempotency: BTreeMap<String, (String, String)>,
    receipts: Vec<ControlReceipt>,
}
impl Service {
    pub fn new(policy: Policy, timestamp: impl Into<String>) -> Result<Self, Error> {
        let timestamp = timestamp.into();
        if !policy.workload.admitted() || policy.modes.is_empty() || timestamp.trim().is_empty()
            || policy.max_per_job.values().any(|value| *value == 0)
        { return Err(Error::Refused("INVALID_SERVICE_POLICY".into())); }
        Ok(Self { policy, timestamp, entitlement: None, consumed: BTreeMap::new(), reservations: BTreeMap::new(), idempotency: BTreeMap::new(), receipts: Vec::new() })
    }

    pub fn bind_entitlement(&mut self, grant: Grant, commercial: &CommercialReceipt, authority: Authority) -> Result<String, Error> {
        commercial.verify()?;
        if commercial.kind != ReceiptKind::FulfillmentAuthorized || grant.organization.trim().is_empty()
            || grant.plan.trim().is_empty() || grant.modes.is_empty() || !grant.modes.is_subset(&self.policy.modes)
            || grant.quota.is_empty() || grant.quota.values().any(|value| *value == 0)
        { return Err(Error::Refused("INVALID_ENTITLEMENT_GRANT".into())); }
        if self.entitlement.as_ref().is_some_and(|bound| bound.grant.organization != grant.organization) {
            return Err(Error::Refused("TENANT_REBIND_REFUSED".into()));
        }
        let digest = self.emit(Kind::EntitlementBound, authority, &commercial.core.digest, "entitlement")?.core.digest;
        self.entitlement = Some(BoundGrant { grant, commercial_subject: commercial.core.subject.clone(), active: true });
        Ok(digest)
    }

    pub fn apply_entitlement_event(&mut self, commercial: &CommercialReceipt, authority: Authority) -> Result<(), Error> {
        commercial.verify()?;
        let bound = self.entitlement.as_ref().ok_or_else(|| Error::Refused("NO_BOUND_ENTITLEMENT".into()))?;
        if commercial.core.subject != bound.commercial_subject { return Err(Error::Refused("COMMERCIAL_SUBJECT_MISMATCH".into())); }
        let (kind, active) = match commercial.kind {
            ReceiptKind::EntitlementSuspended => (Kind::EntitlementSuspended, false),
            ReceiptKind::EntitlementReinstated => (Kind::EntitlementReinstated, true),
            ReceiptKind::EntitlementRevoked => (Kind::EntitlementRevoked, false),
            _ => return Err(Error::Refused("UNSUPPORTED_ENTITLEMENT_EVENT".into())),
        };
        self.emit(kind, authority, &commercial.core.digest, "entitlement")?;
        if let Some(bound) = &mut self.entitlement { bound.active = active; }
        Ok(())
    }

    pub fn admit_job(&mut self, principal: &Principal, request: &JobRequest, authority: Authority) -> Result<Reservation, Error> {
        if authority != Authority::PersistControlPlane || !principal.admitted() || request.id.trim().is_empty()
            || request.idempotency_key.trim().is_empty() || request.requested.is_empty()
            || request.requested.values().any(|value| *value == 0)
        { return Err(Error::Refused("INVALID_JOB_ADMISSION".into())); }
        let grant = self.entitlement.as_ref().filter(|bound| bound.active).map(|bound| &bound.grant)
            .ok_or_else(|| Error::Refused("ENTITLEMENT_NOT_ACTIVE".into()))?;
        if principal.organization != grant.organization || request.organization != grant.organization { return Err(Error::Refused("TENANT_IDENTITY_MISMATCH".into())); }
        if !request.workload.admitted() || request.workload != self.policy.workload { return Err(Error::Refused("WORKLOAD_IDENTITY_MISMATCH".into())); }
        if !grant.modes.contains(&request.mode) { return Err(Error::Refused("DEPLOYMENT_MODE_NOT_ENTITLED".into())); }
        if request.requested.iter().any(|(meter, units)| *units > self.policy.max_per_job.get(meter).copied().unwrap_or(0)) {
            return Err(Error::Refused("JOB_LIMIT_EXCEEDED".into()));
        }
        let fingerprint = format!("{}|{}|{}|{:?}|{:?}", request.id, request.organization, request.workload.sha, request.mode, request.requested);
        if let Some((existing, reservation_id)) = self.idempotency.get(&request.idempotency_key) {
            if existing != &fingerprint { return Err(Error::Refused("IDEMPOTENCY_KEY_CONFLICT".into())); }
            return self.reservations.get(reservation_id).cloned().ok_or_else(|| Error::Receipt("RESERVATION_INDEX_MISSING".into()));
        }
        self.check_quota(grant, &request.requested)?;
        let id = format!("reservation:agent-lightning-{}", self.reservations.len() + 1);
        let source = self.receipts.last().map_or_else(String::new, |receipt| receipt.core.digest.clone());
        let reserve_receipt = self.emit(Kind::UsageReserved, authority, &source, &request.id)?.core.digest;
        let reservation = Reservation { id: id.clone(), job_id: request.id.clone(), workload: request.workload.clone(), mode: request.mode, units: request.requested.clone(), state: ReservationState::Reserved, reserve_receipt, actuation_receipt: String::new() };
        self.reservations.insert(id.clone(), reservation.clone());
        self.idempotency.insert(request.idempotency_key.clone(), (fingerprint, id));
        Ok(reservation)
    }

    pub fn authorize_actuation(&mut self, reservation_id: &str, authority: Authority) -> Result<ActuationPermit, Error> {
        if authority != Authority::ModifyExternalObject || !self.entitlement.as_ref().is_some_and(|bound| bound.active) {
            return Err(Error::Refused("ACTUATION_NOT_AUTHORIZED".into()));
        }
        let reservation = self.reservations.get(reservation_id).cloned().ok_or_else(|| Error::Refused("UNKNOWN_RESERVATION".into()))?;
        if reservation.state == ReservationState::Reconciled { return Err(Error::Refused("RESERVATION_ALREADY_RECONCILED".into())); }
        if reservation.state == ReservationState::Authorized { return Ok(Self::permit(&reservation)); }
        let digest = self.emit(Kind::ActuationAuthorized, authority, &reservation.reserve_receipt, &reservation.job_id)?.core.digest;
        let stored = self.reservations.get_mut(reservation_id).ok_or_else(|| Error::Receipt("RESERVATION_DISAPPEARED".into()))?;
        stored.state = ReservationState::Authorized;
        stored.actuation_receipt = digest;
        Ok(Self::permit(stored))
    }

    pub fn reconcile_usage(&mut self, permit: &ActuationPermit, actual: BTreeMap<Meter, u64>, authority: Authority) -> Result<String, Error> {
        if authority != Authority::PersistControlPlane || actual.is_empty() || actual.values().any(|value| *value == 0) {
            return Err(Error::Refused("INVALID_USAGE_RECONCILIATION".into()));
        }
        let reservation = self.reservations.get(&permit.reservation_id).cloned().ok_or_else(|| Error::Refused("UNKNOWN_RESERVATION".into()))?;
        if reservation.state != ReservationState::Authorized || reservation.actuation_receipt != permit.receipt_digest
            || reservation.job_id != permit.job_id || reservation.workload != permit.workload || reservation.mode != permit.mode
        { return Err(Error::Refused("INVALID_ACTUATION_PERMIT".into())); }
        if actual.iter().any(|(meter, units)| *units > reservation.units.get(meter).copied().unwrap_or(0)) {
            return Err(Error::Refused("ACTUAL_USAGE_EXCEEDS_RESERVATION".into()));
        }
        let digest = self.emit(Kind::UsageReconciled, authority, &permit.receipt_digest, &permit.job_id)?.core.digest;
        for (meter, units) in actual { let value = self.consumed.entry(meter).or_default(); *value = value.saturating_add(units); }
        let stored = self.reservations.get_mut(&permit.reservation_id).ok_or_else(|| Error::Receipt("RESERVATION_DISAPPEARED".into()))?;
        stored.state = ReservationState::Reconciled;
        Ok(digest)
    }

    pub fn replay_verify(&self) -> Result<usize, Error> {
        let mut previous = String::new();
        let mut known = BTreeSet::new();
        for receipt in &self.receipts {
            receipt.verify()?;
            if receipt.previous != previous { return Err(Error::Receipt("RECEIPT_CHAIN_MISMATCH".into())); }
            if matches!(receipt.kind, Kind::ActuationAuthorized | Kind::UsageReconciled) && !known.contains(&receipt.source) {
                return Err(Error::Receipt("SOURCE_RECEIPT_NOT_PRIOR".into()));
            }
            previous.clone_from(&receipt.core.digest);
            known.insert(receipt.core.digest.clone());
        }
        Ok(self.receipts.len())
    }

    fn permit(reservation: &Reservation) -> ActuationPermit {
        ActuationPermit { reservation_id: reservation.id.clone(), job_id: reservation.job_id.clone(), workload: reservation.workload.clone(), mode: reservation.mode, receipt_digest: reservation.actuation_receipt.clone() }
    }
    fn check_quota(&self, grant: &Grant, requested: &BTreeMap<Meter, u64>) -> Result<(), Error> {
        for (meter, units) in requested {
            let reserved = self.reservations.values().filter(|r| r.state != ReservationState::Reconciled)
                .map(|r| r.units.get(meter).copied().unwrap_or(0)).fold(0_u64, u64::saturating_add);
            let used = self.consumed.get(meter).copied().unwrap_or(0);
            if used.saturating_add(reserved).saturating_add(*units) > grant.quota.get(meter).copied().unwrap_or(0) {
                return Err(Error::Refused("ENTITLEMENT_QUOTA_EXCEEDED".into()));
            }
        }
        Ok(())
    }
    fn emit(&mut self, kind: Kind, authority: Authority, source: &str, change: &str) -> Result<ControlReceipt, Error> {
        if authority != kind.authority() { return Err(Error::Refused("AUTHORITY_DENIED".into())); }
        let previous = self.receipts.last().map_or_else(String::new, |receipt| receipt.core.digest.clone());
        let mut core = Receipt {
            id: ReceiptId::parse(format!("receipt:agent-lightning-service-{}", self.receipts.len() + 1)).map_err(|error| Error::Receipt(error.to_string()))?,
            subject: "service:agent-lightning".into(), actor: "agent-lightning-commercial-control-plane".into(), authority,
            intention: format!("{kind:?}"), observed: vec![source.into()], executed: vec![format!("{kind:?}")], changed: vec![change.into()],
            verified: vec!["identity authority entitlement and receipt preconditions admitted".into()], excluded: vec!["direct unreceipted Agent Lightning actuation".into()],
            replay: vec!["agent-lightning-commercial verify-fixtures".into()], standing_before: Standing::PartialAlive, standing_after: Standing::PartialAlive,
            timestamp: self.timestamp.clone(), digest: String::new(),
        };
        core.sign().map_err(|error| Error::Receipt(error.to_string()))?;
        let receipt = ControlReceipt { kind, source: source.into(), previous, core };
        receipt.verify()?;
        self.receipts.push(receipt.clone());
        Ok(receipt)
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct VerificationReport {
    pub standing: String, pub repository: String, pub sha: String,
    pub providers_verified: Vec<String>, pub modes_verified: Vec<String>,
    pub receipts_verified: usize, pub negative_fixtures_verified: usize,
    pub invariants: Vec<String>, pub blockers: Vec<String>,
}

fn observation(c: &CommerceContext, kind: ProviderEventKind, event: &str, quantity: u64) -> ProviderObservation {
    ProviderObservation { provider: c.provider, kind, event_ref: event.into(), buyer_ref: c.provider_buyer_ref.clone(), product_ref: c.provider_product_ref.clone(), agreement_ref: c.provider_agreement_ref.clone(), entitlement_ref: c.provider_entitlement_ref.clone(), subscription_ref: c.provider_subscription_ref.clone(), plan: "enterprise".into(), dimension: "agentic-rl-training".into(), quantity, units: 0, amount_micros: 0, currency: "USD".into() }
}
fn commerce_fixture(provider: Provider) -> Result<(CommerceLedger, CommerceContext, CommercialReceipt), Error> {
    let p = provider.as_str();
    let c = CommerceContext { seller: "seller:chatman".into(), buyer: format!("buyer:{p}"), product: "product:agent-lightning-managed".into(), capability: CAPABILITY.into(), sku: "sku:enterprise".into(), offer: "offer:managed-rl".into(), order: format!("order:{p}"), agreement: format!("agreement:{p}"), subscription: format!("subscription:{p}"), entitlement: format!("entitlement:{p}"), fulfillment: format!("fulfillment:{p}"), provider, provider_buyer_ref: format!("{p}-buyer"), provider_product_ref: format!("{p}-product"), provider_agreement_ref: format!("{p}-agreement"), provider_entitlement_ref: format!("{p}-agreement"), provider_subscription_ref: format!("{p}-agreement"), unit_price_micros: 10_000, currency: "USD".into() };
    let mut ledger = CommerceLedger::new(c.clone())?;
    ledger.observe(&observation(&c, ProviderEventKind::Agreement, "agreement", 0))?;
    ledger.observe(&observation(&c, ProviderEventKind::Entitlement, "entitlement", 1))?;
    let fulfillment = ledger.authorize_fulfillment("agent-lightning-fulfillment")?;
    Ok((ledger, c, fulfillment))
}
fn grant(org: &str) -> Grant {
    Grant { organization: org.into(), plan: "enterprise".into(), modes: BTreeSet::from([Mode::Hosted, Mode::Byoc, Mode::Private]), quota: BTreeMap::from([(Meter::GpuSeconds, 20_000), (Meter::InputTokens, 2_000_000), (Meter::OutputTokens, 1_000_000), (Meter::Rollouts, 100)]) }
}
fn request(org: &str, mode: Mode, suffix: &str) -> JobRequest {
    JobRequest { id: format!("job-{suffix}"), organization: org.into(), workload: Workload::pinned(), mode, requested: BTreeMap::from([(Meter::GpuSeconds, 3_600), (Meter::InputTokens, 100_000), (Meter::OutputTokens, 20_000), (Meter::Rollouts, 1)]), idempotency_key: format!("idem-{suffix}") }
}
fn neg(value: bool) -> usize { if value { 1 } else { 0 } }

pub fn verify_fixtures() -> Result<VerificationReport, Error> {
    let mut providers = Vec::new(); let mut modes = BTreeSet::new(); let mut receipts = 0; let mut negatives = 0;
    for (index, provider) in [Provider::Aws, Provider::Microsoft, Provider::Google].into_iter().enumerate() {
        let (mut commerce, context, fulfillment) = commerce_fixture(provider)?;
        let org = format!("organization:{}-customer", provider.as_str());
        let mut service = Service::new(Policy::agent_lightning(), "2026-08-19T00:00:00Z")?;
        service.bind_entitlement(grant(&org), &fulfillment, Authority::PersistControlPlane)?;
        let principal = Principal { organization: org.clone(), subject: format!("service-account:{}", provider.as_str()), key_fingerprint: format!("blake3:{}", "0".repeat(64)) };
        let mode = [Mode::Hosted, Mode::Byoc, Mode::Private][index]; modes.insert(format!("{mode:?}").to_ascii_lowercase());
        let job = request(&org, mode, provider.as_str());
        let reservation = service.admit_job(&principal, &job, Authority::PersistControlPlane)?;
        if service.admit_job(&principal, &job, Authority::PersistControlPlane)?.id != reservation.id { return Err(Error::Receipt("IDEMPOTENT_REPLAY_DIVERGED".into())); }
        let mut attacker = principal.clone(); attacker.organization = "organization:attacker".into();
        negatives += neg(service.admit_job(&attacker, &job, Authority::PersistControlPlane).is_err());
        let mut wrong = request(&org, mode, "wrong-sha"); wrong.workload.sha = "1".repeat(40);
        negatives += neg(service.admit_job(&principal, &wrong, Authority::PersistControlPlane).is_err());
        let mut over = request(&org, mode, "over-quota"); over.requested.insert(Meter::GpuSeconds, 20_001);
        negatives += neg(service.admit_job(&principal, &over, Authority::PersistControlPlane).is_err());
        negatives += neg(service.authorize_actuation(&reservation.id, Authority::Observe).is_err());
        let permit = service.authorize_actuation(&reservation.id, Authority::ModifyExternalObject)?;
        if permit.receipt_digest.is_empty() { return Err(Error::Receipt("UNRECEIPTED_ACTUATION_PERMIT".into())); }
        negatives += neg(service.reconcile_usage(&permit, BTreeMap::from([(Meter::GpuSeconds, 3_601)]), Authority::PersistControlPlane).is_err());
        service.reconcile_usage(&permit, BTreeMap::from([(Meter::GpuSeconds, 3_000), (Meter::InputTokens, 90_000), (Meter::OutputTokens, 15_000), (Meter::Rollouts, 1)]), Authority::PersistControlPlane)?;
        let suspended = commerce.observe(&observation(&context, ProviderEventKind::Suspended, "suspended", 1))?;
        service.apply_entitlement_event(&suspended, Authority::PersistControlPlane)?;
        negatives += neg(service.admit_job(&principal, &request(&org, mode, "suspended"), Authority::PersistControlPlane).is_err());
        receipts += service.replay_verify()?; providers.push(provider.as_str().into());
    }
    Ok(VerificationReport {
        standing: "PARTIAL_ALIVE".into(), repository: REPOSITORY.into(), sha: SHA.into(), providers_verified: providers,
        modes_verified: modes.into_iter().collect(), receipts_verified: receipts, negative_fixtures_verified: negatives,
        invariants: vec!["exact Agent Lightning Git identity admitted".into(), "tenant identity bound to commercial entitlement".into(), "quota reserved before DO".into(), "actuation permit contains a prior signed receipt digest".into(), "actual usage cannot exceed reservation".into(), "suspension blocks new admission".into(), "receipt chain and source edges replay".into()],
        blockers: vec!["BLOCKED:LIVE_AGENT_LIGHTNING_EXECUTION_AT_PINNED_SHA_NOT_OBSERVED".into(), "BLOCKED:DURABLE_TENANT_IDENTITY_API_KEY_ROTATION_NOT_WIRED".into(), "BLOCKED:LIVE_PURCHASE_METER_AND_SETTLEMENT_RECEIPTS_NOT_OBSERVED".into(), "BLOCKED:PRODUCTION_GPU_COST_LIMITS_HA_AND_DR_NOT_OBSERVED".into()],
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn paid_service_is_receipted_and_fail_closed() -> Result<(), Error> {
        let report = verify_fixtures()?;
        assert_eq!(report.providers_verified.len(), 3); assert_eq!(report.modes_verified.len(), 3);
        assert!(report.receipts_verified >= 15); assert!(report.negative_fixtures_verified >= 18);
        assert_eq!(report.sha, SHA); Ok(())
    }
}
