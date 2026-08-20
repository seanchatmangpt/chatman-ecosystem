#![allow(dead_code, clippy::doc_markdown, clippy::missing_errors_doc)]

//! DfCM commercial control plane around the pinned external Agent Lightning workload.
//! The module owns no Agent Lightning implementation code. It admits identity, deployment,
//! cost, metering, settlement, persistence, and replay boundaries around the external subject.

use crate::agent_lightning_service::{
    ActuationPermit, Error as ServiceError, Grant, JobRequest, Meter, Mode, Policy, Principal,
    Reservation, Service, VerificationReport as ServiceVerificationReport, Workload,
    verify_fixtures as verify_service_fixtures,
};
use crate::commerce::{
    CommerceContext, CommerceError, CommerceLedger, CommercialReceipt, Provider, ProviderEventKind,
    ProviderObservation, ReceiptKind,
};
use ecosystem_core::{Authority, Receipt, ReceiptId, Standing};
use serde::{Deserialize, Serialize};
use sqlx::{Row, SqlitePool, sqlite::SqliteConnectOptions, sqlite::SqlitePoolOptions};
use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

const SNAPSHOT_SCHEMA: &str = "chatman.agent-lightning.identity.v1";

#[derive(Debug, thiserror::Error)]
pub enum PlaneError {
    #[error("REFUSED:{0}")]
    Refused(String),
    #[error("SERVICE:{0}")]
    Service(String),
    #[error("COMMERCE:{0}")]
    Commerce(String),
    #[error("STORAGE:{0}")]
    Storage(String),
    #[error("RECEIPT:{0}")]
    Receipt(String),
    #[error("SERDE:{0}")]
    Serde(String),
}

impl From<ServiceError> for PlaneError {
    fn from(value: ServiceError) -> Self {
        Self::Service(value.to_string())
    }
}

impl From<CommerceError> for PlaneError {
    fn from(value: CommerceError) -> Self {
        Self::Commerce(value.to_string())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ApiKeyBinding {
    pub key_id: String,
    pub fingerprint: String,
    pub generation: u64,
    pub active: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IdentityRecord {
    pub organization: String,
    pub subject: String,
    pub keys: Vec<ApiKeyBinding>,
}

impl IdentityRecord {
    fn active_key(&self) -> Option<&ApiKeyBinding> {
        self.keys.iter().find(|key| key.active)
    }

    fn validate(&self) -> Result<(), PlaneError> {
        if self.organization.trim().is_empty()
            || self.subject.trim().is_empty()
            || self.keys.is_empty()
        {
            return Err(PlaneError::Refused("INVALID_IDENTITY_RECORD".into()));
        }
        let mut key_ids = BTreeSet::new();
        let mut generations = BTreeSet::new();
        let active = self.keys.iter().filter(|key| key.active).count();
        if active > 1 {
            return Err(PlaneError::Refused("MULTIPLE_ACTIVE_API_KEYS".into()));
        }
        for key in &self.keys {
            validate_fingerprint(&key.fingerprint)?;
            if key.key_id.trim().is_empty()
                || key.generation == 0
                || !key_ids.insert(key.key_id.clone())
                || !generations.insert(key.generation)
            {
                return Err(PlaneError::Refused("INVALID_API_KEY_HISTORY".into()));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Default)]
struct IdentityRegistry {
    records: BTreeMap<String, IdentityRecord>,
}

impl IdentityRegistry {
    fn identity_key(organization: &str, subject: &str) -> String {
        format!("{organization}\u{1f}{subject}")
    }

    fn validate_register(
        &self,
        organization: &str,
        subject: &str,
        key_id: &str,
        fingerprint: &str,
    ) -> Result<(), PlaneError> {
        validate_identity_fields(organization, subject, key_id, fingerprint)?;
        let identity = Self::identity_key(organization, subject);
        if self.records.contains_key(&identity) {
            return Err(PlaneError::Refused("IDENTITY_ALREADY_REGISTERED".into()));
        }
        Ok(())
    }

    fn apply_register(
        &mut self,
        organization: &str,
        subject: &str,
        key_id: &str,
        fingerprint: &str,
    ) {
        self.records.insert(
            Self::identity_key(organization, subject),
            IdentityRecord {
                organization: organization.into(),
                subject: subject.into(),
                keys: vec![ApiKeyBinding {
                    key_id: key_id.into(),
                    fingerprint: fingerprint.into(),
                    generation: 1,
                    active: true,
                }],
            },
        );
    }

    fn validate_rotate(
        &self,
        organization: &str,
        subject: &str,
        key_id: &str,
        fingerprint: &str,
    ) -> Result<u64, PlaneError> {
        validate_identity_fields(organization, subject, key_id, fingerprint)?;
        let record = self
            .records
            .get(&Self::identity_key(organization, subject))
            .ok_or_else(|| PlaneError::Refused("IDENTITY_NOT_REGISTERED".into()))?;
        record.validate()?;
        if record.active_key().is_none() {
            return Err(PlaneError::Refused("IDENTITY_HAS_NO_ACTIVE_KEY".into()));
        }
        if record
            .keys
            .iter()
            .any(|key| key.key_id == key_id || key.fingerprint.eq_ignore_ascii_case(fingerprint))
        {
            return Err(PlaneError::Refused("API_KEY_REUSE_REFUSED".into()));
        }
        Ok(record
            .keys
            .iter()
            .map(|key| key.generation)
            .max()
            .unwrap_or(0)
            .saturating_add(1))
    }

    fn apply_rotate(
        &mut self,
        organization: &str,
        subject: &str,
        key_id: &str,
        fingerprint: &str,
        generation: u64,
    ) {
        if let Some(record) = self
            .records
            .get_mut(&Self::identity_key(organization, subject))
        {
            for key in &mut record.keys {
                key.active = false;
            }
            record.keys.push(ApiKeyBinding {
                key_id: key_id.into(),
                fingerprint: fingerprint.into(),
                generation,
                active: true,
            });
        }
    }

    fn validate_revoke(&self, organization: &str, subject: &str) -> Result<(), PlaneError> {
        let record = self
            .records
            .get(&Self::identity_key(organization, subject))
            .ok_or_else(|| PlaneError::Refused("IDENTITY_NOT_REGISTERED".into()))?;
        if record.active_key().is_none() {
            return Err(PlaneError::Refused("IDENTITY_ALREADY_REVOKED".into()));
        }
        Ok(())
    }

    fn apply_revoke(&mut self, organization: &str, subject: &str) {
        if let Some(record) = self
            .records
            .get_mut(&Self::identity_key(organization, subject))
        {
            for key in &mut record.keys {
                key.active = false;
            }
        }
    }

    fn authenticate(
        &self,
        organization: &str,
        subject: &str,
        fingerprint: &str,
    ) -> Result<Principal, PlaneError> {
        validate_fingerprint(fingerprint)?;
        let record = self
            .records
            .get(&Self::identity_key(organization, subject))
            .ok_or_else(|| PlaneError::Refused("IDENTITY_NOT_REGISTERED".into()))?;
        let key = record
            .active_key()
            .filter(|key| key.fingerprint.eq_ignore_ascii_case(fingerprint))
            .ok_or_else(|| PlaneError::Refused("API_KEY_NOT_ACTIVE".into()))?;
        Ok(Principal {
            organization: record.organization.clone(),
            subject: record.subject.clone(),
            key_fingerprint: key.fingerprint.clone(),
        })
    }

    fn records(&self) -> Vec<IdentityRecord> {
        self.records.values().cloned().collect()
    }

    fn from_records(records: Vec<IdentityRecord>) -> Result<Self, PlaneError> {
        let mut registry = Self::default();
        for record in records {
            record.validate()?;
            let key = Self::identity_key(&record.organization, &record.subject);
            if registry.records.insert(key, record).is_some() {
                return Err(PlaneError::Refused("DUPLICATE_IDENTITY_RECORD".into()));
            }
        }
        Ok(registry)
    }
}

fn validate_identity_fields(
    organization: &str,
    subject: &str,
    key_id: &str,
    fingerprint: &str,
) -> Result<(), PlaneError> {
    if organization.trim().is_empty() || subject.trim().is_empty() || key_id.trim().is_empty() {
        return Err(PlaneError::Refused("INVALID_IDENTITY_FIELDS".into()));
    }
    validate_fingerprint(fingerprint)
}

fn validate_fingerprint(fingerprint: &str) -> Result<(), PlaneError> {
    if fingerprint.strip_prefix("blake3:").is_some_and(|hex| {
        hex.len() == 64 && hex.chars().all(|character| character.is_ascii_hexdigit())
    }) {
        Ok(())
    } else {
        Err(PlaneError::Refused("INVALID_API_KEY_FINGERPRINT".into()))
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum PlaneKind {
    IdentityRegistered,
    IdentityRotated,
    IdentityRevoked,
    IdentitySnapshotPersisted,
    RunAdmitted,
    MeteringConstructed,
    SettlementAccepted,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct PlaneReceipt {
    kind: PlaneKind,
    source: String,
    previous: String,
    core: Receipt,
}

impl PlaneReceipt {
    fn verify(&self) -> Result<(), PlaneError> {
        self.core
            .verify()
            .map_err(|error| PlaneError::Receipt(error.to_string()))?;
        if self.core.authority != Authority::PersistControlPlane {
            return Err(PlaneError::Receipt("PLANE_AUTHORITY_MISMATCH".into()));
        }
        if self.source.trim().is_empty() {
            return Err(PlaneError::Receipt("PLANE_RECEIPT_SOURCE_REQUIRED".into()));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IdentitySnapshot {
    schema: String,
    identities: Vec<IdentityRecord>,
    receipts: Vec<PlaneReceipt>,
}

impl IdentitySnapshot {
    fn verify(&self) -> Result<IdentityRegistry, PlaneError> {
        if self.schema != SNAPSHOT_SCHEMA {
            return Err(PlaneError::Refused(
                "IDENTITY_SNAPSHOT_SCHEMA_MISMATCH".into(),
            ));
        }
        replay_plane_receipts(&self.receipts)?;
        IdentityRegistry::from_records(self.identities.clone())
    }
}

#[derive(Debug, Clone)]
pub struct IdentityStore {
    pool: SqlitePool,
}

impl IdentityStore {
    pub async fn open(path: &Path) -> Result<Self, PlaneError> {
        let options = SqliteConnectOptions::new()
            .filename(path)
            .create_if_missing(true);
        let pool = SqlitePoolOptions::new()
            .max_connections(1)
            .connect_with(options)
            .await
            .map_err(|error| PlaneError::Storage(error.to_string()))?;
        let store = Self { pool };
        sqlx::query(
            "CREATE TABLE IF NOT EXISTS agent_lightning_identity_state(\
             tenant_key TEXT PRIMARY KEY, snapshot TEXT NOT NULL, version INTEGER NOT NULL CHECK(version > 0))",
        )
        .execute(&store.pool)
        .await
        .map_err(|error| PlaneError::Storage(error.to_string()))?;
        Ok(store)
    }

    pub async fn save(
        &self,
        tenant_key: &str,
        snapshot: &IdentitySnapshot,
        expected_version: Option<i64>,
    ) -> Result<i64, PlaneError> {
        if tenant_key.trim().is_empty() {
            return Err(PlaneError::Refused("IDENTITY_STORE_KEY_REQUIRED".into()));
        }
        snapshot.verify()?;
        let encoded = serde_json::to_string(snapshot)
            .map_err(|error| PlaneError::Serde(error.to_string()))?;
        let mut transaction = self
            .pool
            .begin()
            .await
            .map_err(|error| PlaneError::Storage(error.to_string()))?;
        let row =
            sqlx::query("SELECT version FROM agent_lightning_identity_state WHERE tenant_key = ?")
                .bind(tenant_key)
                .fetch_optional(&mut *transaction)
                .await
                .map_err(|error| PlaneError::Storage(error.to_string()))?;
        let version = match row {
            Some(row) => {
                let current: i64 = row
                    .try_get("version")
                    .map_err(|error| PlaneError::Storage(error.to_string()))?;
                if expected_version != Some(current) {
                    return Err(PlaneError::Refused(
                        "IDENTITY_STORE_VERSION_CONFLICT".into(),
                    ));
                }
                let next = current.saturating_add(1);
                sqlx::query(
                    "UPDATE agent_lightning_identity_state SET snapshot = ?, version = ? \
                     WHERE tenant_key = ? AND version = ?",
                )
                .bind(encoded)
                .bind(next)
                .bind(tenant_key)
                .bind(current)
                .execute(&mut *transaction)
                .await
                .map_err(|error| PlaneError::Storage(error.to_string()))?;
                next
            }
            None if expected_version.is_none() => {
                sqlx::query(
                    "INSERT INTO agent_lightning_identity_state(tenant_key, snapshot, version) \
                     VALUES (?, ?, 1)",
                )
                .bind(tenant_key)
                .bind(encoded)
                .execute(&mut *transaction)
                .await
                .map_err(|error| PlaneError::Storage(error.to_string()))?;
                1
            }
            None => {
                return Err(PlaneError::Refused(
                    "IDENTITY_STORE_VERSION_CONFLICT".into(),
                ));
            }
        };
        transaction
            .commit()
            .await
            .map_err(|error| PlaneError::Storage(error.to_string()))?;
        Ok(version)
    }

    pub async fn load(
        &self,
        tenant_key: &str,
    ) -> Result<Option<(IdentitySnapshot, i64)>, PlaneError> {
        let row = sqlx::query(
            "SELECT snapshot, version FROM agent_lightning_identity_state WHERE tenant_key = ?",
        )
        .bind(tenant_key)
        .fetch_optional(&self.pool)
        .await
        .map_err(|error| PlaneError::Storage(error.to_string()))?;
        row.map(|row| {
            let encoded: String = row
                .try_get("snapshot")
                .map_err(|error| PlaneError::Storage(error.to_string()))?;
            let version: i64 = row
                .try_get("version")
                .map_err(|error| PlaneError::Storage(error.to_string()))?;
            let snapshot: IdentitySnapshot = serde_json::from_str(&encoded)
                .map_err(|error| PlaneError::Serde(error.to_string()))?;
            snapshot.verify()?;
            Ok((snapshot, version))
        })
        .transpose()
    }

    pub async fn close(&self) {
        self.pool.close().await;
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DeploymentFeature {
    PrivateNetwork,
    DurableReceiptSink,
    CustomerManagedKey,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DeploymentTarget {
    pub provider: Provider,
    pub mode: Mode,
    pub region: String,
    pub zones: u8,
    pub replicas: u16,
    pub rpo_seconds: u64,
    pub rto_seconds: u64,
    pub features: BTreeSet<DeploymentFeature>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeploymentPolicy {
    pub allowed_regions: BTreeMap<String, BTreeSet<String>>,
    pub minimum_zones: u8,
    pub minimum_replicas: u16,
    pub maximum_replicas: u16,
    pub maximum_rpo_seconds: u64,
    pub maximum_rto_seconds: u64,
    pub customer_managed_key_modes: BTreeSet<Mode>,
}

impl DeploymentPolicy {
    #[must_use]
    pub fn enterprise_default() -> Self {
        Self {
            allowed_regions: BTreeMap::from([
                (
                    "aws".into(),
                    BTreeSet::from(["us-east-1".into(), "us-west-2".into()]),
                ),
                (
                    "microsoft".into(),
                    BTreeSet::from(["eastus".into(), "westus2".into()]),
                ),
                (
                    "google".into(),
                    BTreeSet::from(["us-central1".into(), "us-east1".into()]),
                ),
            ]),
            minimum_zones: 2,
            minimum_replicas: 2,
            maximum_replicas: 64,
            maximum_rpo_seconds: 300,
            maximum_rto_seconds: 900,
            customer_managed_key_modes: BTreeSet::from([Mode::Byoc, Mode::Private]),
        }
    }

    fn admit(&self, request: &JobRequest, target: &DeploymentTarget) -> Result<(), PlaneError> {
        if target.mode != request.mode {
            return Err(PlaneError::Refused(
                "DEPLOYMENT_MODE_REQUEST_MISMATCH".into(),
            ));
        }
        let allowed = self
            .allowed_regions
            .get(target.provider.as_str())
            .is_some_and(|regions| regions.contains(&target.region));
        if !allowed {
            return Err(PlaneError::Refused("DEPLOYMENT_REGION_NOT_ADMITTED".into()));
        }
        if target.zones < self.minimum_zones
            || target.replicas < self.minimum_replicas
            || target.replicas > self.maximum_replicas
            || target.rpo_seconds > self.maximum_rpo_seconds
            || target.rto_seconds > self.maximum_rto_seconds
        {
            return Err(PlaneError::Refused(
                "DEPLOYMENT_RELIABILITY_POLICY_FAILED".into(),
            ));
        }
        for feature in [
            DeploymentFeature::PrivateNetwork,
            DeploymentFeature::DurableReceiptSink,
        ] {
            if !target.features.contains(&feature) {
                return Err(PlaneError::Refused(
                    "DEPLOYMENT_REQUIRED_FEATURE_MISSING".into(),
                ));
            }
        }
        if self.customer_managed_key_modes.contains(&target.mode)
            && !target
                .features
                .contains(&DeploymentFeature::CustomerManagedKey)
        {
            return Err(PlaneError::Refused("CUSTOMER_MANAGED_KEY_REQUIRED".into()));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChargeLine {
    pub meter: Meter,
    pub units: u64,
    pub unit_price_micros: u64,
    pub amount_micros: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChargeQuote {
    pub currency: String,
    pub lines: Vec<ChargeLine>,
    pub total_micros: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateCard {
    pub currency: String,
    pub rates_micros: BTreeMap<Meter, u64>,
}

impl RateCard {
    pub fn new(
        currency: impl Into<String>,
        rates_micros: BTreeMap<Meter, u64>,
    ) -> Result<Self, PlaneError> {
        let card = Self {
            currency: currency.into(),
            rates_micros,
        };
        if card.currency.trim().is_empty()
            || [
                Meter::GpuSeconds,
                Meter::InputTokens,
                Meter::OutputTokens,
                Meter::Rollouts,
            ]
            .into_iter()
            .any(|meter| card.rates_micros.get(&meter).copied().unwrap_or(0) == 0)
        {
            return Err(PlaneError::Refused("INCOMPLETE_RATE_CARD".into()));
        }
        Ok(card)
    }

    pub fn quote(&self, units: &BTreeMap<Meter, u64>) -> Result<ChargeQuote, PlaneError> {
        if units.is_empty() {
            return Err(PlaneError::Refused("EMPTY_USAGE_VECTOR".into()));
        }
        let mut total_micros = 0_u64;
        let mut lines = Vec::new();
        for (meter, quantity) in units {
            if *quantity == 0 {
                return Err(PlaneError::Refused("ZERO_USAGE_UNIT".into()));
            }
            let rate = self
                .rates_micros
                .get(meter)
                .copied()
                .ok_or_else(|| PlaneError::Refused("METER_NOT_PRICED".into()))?;
            let amount = quantity
                .checked_mul(rate)
                .ok_or_else(|| PlaneError::Refused("CHARGE_OVERFLOW".into()))?;
            total_micros = total_micros
                .checked_add(amount)
                .ok_or_else(|| PlaneError::Refused("CHARGE_OVERFLOW".into()))?;
            lines.push(ChargeLine {
                meter: *meter,
                units: *quantity,
                unit_price_micros: rate,
                amount_micros: amount,
            });
        }
        Ok(ChargeQuote {
            currency: self.currency.clone(),
            lines,
            total_micros,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BudgetPolicy {
    pub maximum_job_micros: u64,
    pub maximum_period_micros: u64,
}

impl BudgetPolicy {
    fn admit(&self, job_micros: u64, existing_exposure: u64) -> Result<(), PlaneError> {
        if job_micros == 0
            || job_micros > self.maximum_job_micros
            || existing_exposure.saturating_add(job_micros) > self.maximum_period_micros
        {
            return Err(PlaneError::Refused("COST_BUDGET_EXCEEDED".into()));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketplaceBinding {
    pub provider: Provider,
    pub seller: String,
    pub buyer: String,
    pub product: String,
    pub sku: String,
    pub offer: String,
    pub order: String,
    pub agreement: String,
    pub subscription: String,
    pub entitlement: String,
    pub fulfillment: String,
    pub provider_buyer_ref: String,
    pub provider_product_ref: String,
    pub provider_agreement_ref: String,
    pub provider_entitlement_ref: String,
    pub provider_subscription_ref: String,
    pub dimension: String,
    pub currency: String,
}

impl MarketplaceBinding {
    pub fn context(&self) -> CommerceContext {
        CommerceContext {
            seller: self.seller.clone(),
            buyer: self.buyer.clone(),
            product: self.product.clone(),
            capability: crate::agent_lightning_service::CAPABILITY.into(),
            sku: self.sku.clone(),
            offer: self.offer.clone(),
            order: self.order.clone(),
            agreement: self.agreement.clone(),
            subscription: self.subscription.clone(),
            entitlement: self.entitlement.clone(),
            fulfillment: self.fulfillment.clone(),
            provider: self.provider,
            provider_buyer_ref: self.provider_buyer_ref.clone(),
            provider_product_ref: self.provider_product_ref.clone(),
            provider_agreement_ref: self.provider_agreement_ref.clone(),
            provider_entitlement_ref: self.provider_entitlement_ref.clone(),
            provider_subscription_ref: self.provider_subscription_ref.clone(),
            unit_price_micros: 1,
            currency: self.currency.clone(),
        }
    }

    pub fn observation(
        &self,
        kind: ProviderEventKind,
        event_ref: &str,
        units: u64,
        amount_micros: u64,
    ) -> ProviderObservation {
        ProviderObservation {
            provider: self.provider,
            kind,
            event_ref: event_ref.into(),
            buyer_ref: self.provider_buyer_ref.clone(),
            product_ref: self.provider_product_ref.clone(),
            agreement_ref: self.provider_agreement_ref.clone(),
            entitlement_ref: self.provider_entitlement_ref.clone(),
            subscription_ref: self.provider_subscription_ref.clone(),
            plan: "enterprise".into(),
            dimension: self.dimension.clone(),
            quantity: 1,
            units,
            amount_micros,
            currency: self.currency.clone(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MeteringIntent {
    pub reservation_id: String,
    pub provider: Provider,
    pub dimension: String,
    pub actual_usage: BTreeMap<Meter, u64>,
    pub billable_units: u64,
    pub amount_micros: u64,
    pub currency: String,
    pub source_usage_receipt: String,
    pub control_receipt_digest: String,
}

#[derive(Debug, Clone)]
pub struct RunAdmission {
    pub reservation: Reservation,
    pub quote: ChargeQuote,
    pub target: DeploymentTarget,
    pub receipt_digest: String,
}

#[derive(Debug, Clone)]
struct ChargeState {
    organization: String,
    reserved: ChargeQuote,
    target: DeploymentTarget,
    admission_receipt: String,
    intent: Option<MeteringIntent>,
    settlement_receipt: String,
}

#[derive(Debug)]
pub struct CommercialControlPlane {
    service: Service,
    identities: IdentityRegistry,
    deployment: DeploymentPolicy,
    rate_card: RateCard,
    budget: BudgetPolicy,
    binding: MarketplaceBinding,
    charges: BTreeMap<String, ChargeState>,
    receipts: Vec<PlaneReceipt>,
    timestamp: String,
}

impl CommercialControlPlane {
    pub fn new(
        service_policy: Policy,
        deployment: DeploymentPolicy,
        rate_card: RateCard,
        budget: BudgetPolicy,
        binding: MarketplaceBinding,
        timestamp: impl Into<String>,
    ) -> Result<Self, PlaneError> {
        let timestamp = timestamp.into();
        if timestamp.trim().is_empty() || rate_card.currency != binding.currency {
            return Err(PlaneError::Refused(
                "INVALID_COMMERCIAL_PLANE_POLICY".into(),
            ));
        }
        Ok(Self {
            service: Service::new(service_policy, timestamp.clone())?,
            identities: IdentityRegistry::default(),
            deployment,
            rate_card,
            budget,
            binding,
            charges: BTreeMap::new(),
            receipts: Vec::new(),
            timestamp,
        })
    }

    pub fn bind_entitlement(
        &mut self,
        grant: Grant,
        fulfillment: &CommercialReceipt,
        authority: Authority,
    ) -> Result<String, PlaneError> {
        Ok(self
            .service
            .bind_entitlement(grant, fulfillment, authority)?)
    }

    pub fn register_key(
        &mut self,
        organization: &str,
        subject: &str,
        key_id: &str,
        fingerprint: &str,
        authority: Authority,
    ) -> Result<String, PlaneError> {
        require_control_authority(authority)?;
        self.identities
            .validate_register(organization, subject, key_id, fingerprint)?;
        let source = format!("identity:{organization}:{subject}");
        let receipt =
            self.manufacture_receipt(PlaneKind::IdentityRegistered, &source, key_id, authority)?;
        self.identities
            .apply_register(organization, subject, key_id, fingerprint);
        self.receipts.push(receipt.clone());
        Ok(receipt.core.digest)
    }

    pub fn rotate_key(
        &mut self,
        organization: &str,
        subject: &str,
        key_id: &str,
        fingerprint: &str,
        authority: Authority,
    ) -> Result<String, PlaneError> {
        require_control_authority(authority)?;
        let generation =
            self.identities
                .validate_rotate(organization, subject, key_id, fingerprint)?;
        let source = format!("identity:{organization}:{subject}");
        let receipt = self.manufacture_receipt(
            PlaneKind::IdentityRotated,
            &source,
            &format!("{key_id}:generation:{generation}"),
            authority,
        )?;
        self.identities
            .apply_rotate(organization, subject, key_id, fingerprint, generation);
        self.receipts.push(receipt.clone());
        Ok(receipt.core.digest)
    }

    pub fn revoke_identity(
        &mut self,
        organization: &str,
        subject: &str,
        authority: Authority,
    ) -> Result<String, PlaneError> {
        require_control_authority(authority)?;
        self.identities.validate_revoke(organization, subject)?;
        let source = format!("identity:{organization}:{subject}");
        let receipt = self.manufacture_receipt(
            PlaneKind::IdentityRevoked,
            &source,
            "active-key-revoked",
            authority,
        )?;
        self.identities.apply_revoke(organization, subject);
        self.receipts.push(receipt.clone());
        Ok(receipt.core.digest)
    }

    pub async fn persist_identity_snapshot(
        &mut self,
        store: &IdentityStore,
        tenant_key: &str,
        expected_version: Option<i64>,
        authority: Authority,
    ) -> Result<i64, PlaneError> {
        require_control_authority(authority)?;
        let receipt = self.manufacture_receipt(
            PlaneKind::IdentitySnapshotPersisted,
            tenant_key,
            "identity-snapshot",
            authority,
        )?;
        let mut receipts = self.receipts.clone();
        receipts.push(receipt.clone());
        let snapshot = IdentitySnapshot {
            schema: SNAPSHOT_SCHEMA.into(),
            identities: self.identities.records(),
            receipts,
        };
        let version = store.save(tenant_key, &snapshot, expected_version).await?;
        self.receipts.push(receipt);
        Ok(version)
    }

    pub fn authenticate(
        &self,
        organization: &str,
        subject: &str,
        fingerprint: &str,
    ) -> Result<Principal, PlaneError> {
        self.identities
            .authenticate(organization, subject, fingerprint)
    }

    pub fn restore_identity_snapshot(
        snapshot: &IdentitySnapshot,
    ) -> Result<Vec<IdentityRecord>, PlaneError> {
        Ok(snapshot.verify()?.records())
    }

    pub fn admit_run(
        &mut self,
        organization: &str,
        subject: &str,
        fingerprint: &str,
        request: &JobRequest,
        target: &DeploymentTarget,
        authority: Authority,
    ) -> Result<RunAdmission, PlaneError> {
        require_control_authority(authority)?;
        let principal = self.authenticate(organization, subject, fingerprint)?;
        self.deployment.admit(request, target)?;
        if target.provider != self.binding.provider {
            return Err(PlaneError::Refused(
                "MARKETPLACE_PROVIDER_TARGET_MISMATCH".into(),
            ));
        }
        let quote = self.rate_card.quote(&request.requested)?;
        self.budget
            .admit(quote.total_micros, self.exposure_micros())?;
        let reservation = self.service.admit_job(&principal, request, authority)?;
        if let Some(existing) = self.charges.get(&reservation.id) {
            if existing.organization != organization
                || existing.reserved != quote
                || existing.target != *target
            {
                return Err(PlaneError::Refused("IDEMPOTENT_RUN_CONFLICT".into()));
            }
            return Ok(RunAdmission {
                reservation,
                quote: existing.reserved.clone(),
                target: existing.target.clone(),
                receipt_digest: existing.admission_receipt.clone(),
            });
        }
        let receipt = self.manufacture_receipt(
            PlaneKind::RunAdmitted,
            &reservation.id,
            &format!("reserved:{}", quote.total_micros),
            authority,
        )?;
        self.charges.insert(
            reservation.id.clone(),
            ChargeState {
                organization: organization.into(),
                reserved: quote.clone(),
                target: target.clone(),
                admission_receipt: receipt.core.digest.clone(),
                intent: None,
                settlement_receipt: String::new(),
            },
        );
        self.receipts.push(receipt.clone());
        Ok(RunAdmission {
            reservation,
            quote,
            target: target.clone(),
            receipt_digest: receipt.core.digest,
        })
    }

    pub fn authorize_run(
        &mut self,
        reservation_id: &str,
        organization: &str,
        subject: &str,
        fingerprint: &str,
        authority: Authority,
    ) -> Result<ActuationPermit, PlaneError> {
        let _principal = self.authenticate(organization, subject, fingerprint)?;
        let charge = self
            .charges
            .get(reservation_id)
            .ok_or_else(|| PlaneError::Refused("RUN_NOT_ADMITTED".into()))?;
        if charge.organization != organization {
            return Err(PlaneError::Refused("RUN_TENANT_MISMATCH".into()));
        }
        Ok(self
            .service
            .authorize_actuation(reservation_id, authority)?)
    }

    pub fn reconcile_and_construct_metering(
        &mut self,
        permit: &ActuationPermit,
        actual_usage: BTreeMap<Meter, u64>,
        authority: Authority,
    ) -> Result<MeteringIntent, PlaneError> {
        require_control_authority(authority)?;
        let actual_quote = self.rate_card.quote(&actual_usage)?;
        let existing = self
            .charges
            .get(&permit.reservation_id)
            .cloned()
            .ok_or_else(|| PlaneError::Refused("RUN_NOT_ADMITTED".into()))?;
        if let Some(intent) = existing.intent {
            if intent.actual_usage != actual_usage {
                return Err(PlaneError::Refused("USAGE_REPLAY_CONFLICT".into()));
            }
            return Ok(intent);
        }
        if actual_quote.total_micros > existing.reserved.total_micros
            || actual_quote.total_micros > self.budget.maximum_job_micros
        {
            return Err(PlaneError::Refused(
                "ACTUAL_COST_EXCEEDS_RESERVATION".into(),
            ));
        }
        let usage_receipt =
            self.service
                .reconcile_usage(permit, actual_usage.clone(), authority)?;
        let receipt = self.manufacture_receipt(
            PlaneKind::MeteringConstructed,
            &usage_receipt,
            &format!("billable-micros:{}", actual_quote.total_micros),
            authority,
        )?;
        let intent = MeteringIntent {
            reservation_id: permit.reservation_id.clone(),
            provider: self.binding.provider,
            dimension: self.binding.dimension.clone(),
            actual_usage,
            billable_units: actual_quote.total_micros,
            amount_micros: actual_quote.total_micros,
            currency: actual_quote.currency,
            source_usage_receipt: usage_receipt,
            control_receipt_digest: receipt.core.digest.clone(),
        };
        let charge = self
            .charges
            .get_mut(&permit.reservation_id)
            .ok_or_else(|| PlaneError::Receipt("RUN_DISAPPEARED".into()))?;
        charge.intent = Some(intent.clone());
        self.receipts.push(receipt);
        Ok(intent)
    }

    pub fn accept_settlement(
        &mut self,
        intent: &MeteringIntent,
        meter: &CommercialReceipt,
        settlement: &CommercialReceipt,
        authority: Authority,
    ) -> Result<String, PlaneError> {
        require_control_authority(authority)?;
        meter.verify()?;
        settlement.verify()?;
        if meter.kind != ReceiptKind::MeterAccepted
            || settlement.kind != ReceiptKind::SettlementReconciled
            || meter.units != intent.billable_units
            || settlement.units != intent.billable_units
            || settlement.amount_micros != intent.amount_micros
        {
            return Err(PlaneError::Refused(
                "PROVIDER_SETTLEMENT_DOES_NOT_MATCH_INTENT".into(),
            ));
        }
        let existing = self
            .charges
            .get(&intent.reservation_id)
            .cloned()
            .ok_or_else(|| PlaneError::Refused("RUN_NOT_ADMITTED".into()))?;
        if existing.intent.as_ref() != Some(intent) {
            return Err(PlaneError::Refused("METERING_INTENT_NOT_ADMITTED".into()));
        }
        if !existing.settlement_receipt.is_empty() {
            return Ok(existing.settlement_receipt);
        }
        let receipt = self.manufacture_receipt(
            PlaneKind::SettlementAccepted,
            &settlement.core.digest,
            &format!("settled:{}", intent.amount_micros),
            authority,
        )?;
        let charge = self
            .charges
            .get_mut(&intent.reservation_id)
            .ok_or_else(|| PlaneError::Receipt("RUN_DISAPPEARED".into()))?;
        charge.settlement_receipt.clone_from(&receipt.core.digest);
        self.receipts.push(receipt.clone());
        Ok(receipt.core.digest)
    }

    pub fn replay_verify(&self) -> Result<usize, PlaneError> {
        replay_plane_receipts(&self.receipts)
    }

    fn exposure_micros(&self) -> u64 {
        self.charges
            .values()
            .map(|charge| {
                charge
                    .intent
                    .as_ref()
                    .map_or(charge.reserved.total_micros, |intent| intent.amount_micros)
            })
            .fold(0_u64, u64::saturating_add)
    }

    fn manufacture_receipt(
        &self,
        kind: PlaneKind,
        source: &str,
        change: &str,
        authority: Authority,
    ) -> Result<PlaneReceipt, PlaneError> {
        require_control_authority(authority)?;
        if source.trim().is_empty() || change.trim().is_empty() {
            return Err(PlaneError::Refused(
                "PLANE_RECEIPT_EVIDENCE_REQUIRED".into(),
            ));
        }
        let previous = self
            .receipts
            .last()
            .map_or_else(String::new, |receipt| receipt.core.digest.clone());
        let mut core = Receipt {
            id: ReceiptId::parse(format!(
                "receipt:agent-lightning-commercial-plane-{}",
                self.receipts.len() + 1
            ))
            .map_err(|error| PlaneError::Receipt(error.to_string()))?,
            subject: "service:agent-lightning-commercial".into(),
            actor: "chatman-agent-lightning-commercial-plane".into(),
            authority,
            intention: format!("{kind:?}"),
            observed: vec![source.into()],
            executed: vec![format!("{kind:?}")],
            changed: vec![change.into()],
            verified: vec![
                "admission authority identity cost and receipt boundary verified".into(),
            ],
            excluded: vec!["direct unreceipted external actuation".into()],
            replay: vec!["agent-lightning-commercial verify-fixtures".into()],
            standing_before: Standing::PartialAlive,
            standing_after: Standing::PartialAlive,
            timestamp: self.timestamp.clone(),
            digest: String::new(),
        };
        core.sign()
            .map_err(|error| PlaneError::Receipt(error.to_string()))?;
        let receipt = PlaneReceipt {
            kind,
            source: source.into(),
            previous,
            core,
        };
        receipt.verify()?;
        Ok(receipt)
    }
}

fn replay_plane_receipts(receipts: &[PlaneReceipt]) -> Result<usize, PlaneError> {
    let mut previous = String::new();
    for receipt in receipts {
        receipt.verify()?;
        if receipt.previous != previous {
            return Err(PlaneError::Receipt("PLANE_RECEIPT_CHAIN_MISMATCH".into()));
        }
        previous.clone_from(&receipt.core.digest);
    }
    Ok(receipts.len())
}

fn require_control_authority(authority: Authority) -> Result<(), PlaneError> {
    if authority == Authority::PersistControlPlane {
        Ok(())
    } else {
        Err(PlaneError::Refused("CONTROL_PLANE_AUTHORITY_DENIED".into()))
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct FullVerificationReport {
    pub implementation_standing: String,
    pub service_standing: String,
    pub repository: String,
    pub sha: String,
    pub providers_verified: Vec<String>,
    pub modes_verified: Vec<String>,
    pub service_receipts_verified: usize,
    pub commerce_receipts_verified: usize,
    pub control_receipts_verified: usize,
    pub negative_fixtures_verified: usize,
    pub durable_identity_reopens_verified: usize,
    pub invariants: Vec<String>,
    pub blockers: Vec<String>,
}

fn verification_rate_card() -> Result<RateCard, PlaneError> {
    RateCard::new(
        "USD",
        BTreeMap::from([
            (Meter::GpuSeconds, 1_000),
            (Meter::InputTokens, 2),
            (Meter::OutputTokens, 8),
            (Meter::Rollouts, 50_000),
        ]),
    )
}

fn verification_budget() -> BudgetPolicy {
    BudgetPolicy {
        maximum_job_micros: 10_000_000,
        maximum_period_micros: 30_000_000,
    }
}

fn fixture_binding(provider: Provider) -> MarketplaceBinding {
    let name = provider.as_str();
    MarketplaceBinding {
        provider,
        seller: "seller:chatman".into(),
        buyer: format!("buyer:{name}"),
        product: "product:agent-lightning-managed".into(),
        sku: "sku:enterprise".into(),
        offer: "offer:managed-rl".into(),
        order: format!("order:{name}"),
        agreement: format!("agreement:{name}"),
        subscription: format!("subscription:{name}"),
        entitlement: format!("entitlement:{name}"),
        fulfillment: format!("fulfillment:{name}"),
        provider_buyer_ref: format!("{name}-buyer"),
        provider_product_ref: format!("{name}-product"),
        provider_agreement_ref: format!("{name}-agreement"),
        provider_entitlement_ref: format!("{name}-agreement"),
        provider_subscription_ref: format!("{name}-agreement"),
        dimension: "agent-lightning-charge-micro-usd".into(),
        currency: "USD".into(),
    }
}

fn fixture_grant(organization: &str) -> Grant {
    Grant {
        organization: organization.into(),
        plan: "enterprise".into(),
        modes: BTreeSet::from([Mode::Hosted, Mode::Byoc, Mode::Private]),
        quota: BTreeMap::from([
            (Meter::GpuSeconds, 20_000),
            (Meter::InputTokens, 2_000_000),
            (Meter::OutputTokens, 1_000_000),
            (Meter::Rollouts, 100),
        ]),
    }
}

fn fixture_request(organization: &str, mode: Mode, suffix: &str) -> JobRequest {
    JobRequest {
        id: format!("job-{suffix}"),
        organization: organization.into(),
        workload: Workload::pinned(),
        mode,
        requested: BTreeMap::from([
            (Meter::GpuSeconds, 3_600),
            (Meter::InputTokens, 100_000),
            (Meter::OutputTokens, 20_000),
            (Meter::Rollouts, 1),
        ]),
        idempotency_key: format!("idem-{suffix}"),
    }
}

fn fixture_target(provider: Provider, mode: Mode) -> DeploymentTarget {
    let region = match provider {
        Provider::Aws => "us-east-1",
        Provider::Microsoft => "eastus",
        Provider::Google => "us-central1",
    };
    let mut features = BTreeSet::from([
        DeploymentFeature::PrivateNetwork,
        DeploymentFeature::DurableReceiptSink,
    ]);
    if matches!(mode, Mode::Byoc | Mode::Private) {
        features.insert(DeploymentFeature::CustomerManagedKey);
    }
    DeploymentTarget {
        provider,
        mode,
        region: region.into(),
        zones: 3,
        replicas: 3,
        rpo_seconds: 60,
        rto_seconds: 300,
        features,
    }
}

fn fixture_commerce(
    binding: &MarketplaceBinding,
) -> Result<(CommerceLedger, CommercialReceipt), PlaneError> {
    let context = binding.context();
    let mut ledger = CommerceLedger::new(context)?;
    ledger.observe(&binding.observation(ProviderEventKind::Agreement, "agreement-event", 0, 0))?;
    ledger.observe(&binding.observation(
        ProviderEventKind::Entitlement,
        "entitlement-event",
        0,
        0,
    ))?;
    let fulfillment = ledger.authorize_fulfillment("agent-lightning-commercial-fulfillment")?;
    Ok((ledger, fulfillment))
}

fn negative(value: bool) -> usize {
    usize::from(value)
}

async fn verify_provider(
    index: usize,
    provider: Provider,
) -> Result<(String, String, usize, usize, usize), PlaneError> {
    let binding = fixture_binding(provider);
    let (mut commerce, fulfillment) = fixture_commerce(&binding)?;
    let organization = format!("organization:{}-customer", provider.as_str());
    let subject = format!("service-account:{}", provider.as_str());
    let old_fingerprint = format!("blake3:{}", "1".repeat(64));
    let active_fingerprint = format!("blake3:{}", "2".repeat(64));
    let mut plane = CommercialControlPlane::new(
        Policy::agent_lightning(),
        DeploymentPolicy::enterprise_default(),
        verification_rate_card()?,
        verification_budget(),
        binding.clone(),
        "2026-08-19T00:00:00Z",
    )?;
    plane.bind_entitlement(
        fixture_grant(&organization),
        &fulfillment,
        Authority::PersistControlPlane,
    )?;
    plane.register_key(
        &organization,
        &subject,
        "key-1",
        &old_fingerprint,
        Authority::PersistControlPlane,
    )?;

    let path = std::env::temp_dir().join(format!(
        "chatman-agent-lightning-{}-{}.sqlite",
        provider.as_str(),
        std::process::id()
    ));
    let _ = std::fs::remove_file(&path);
    let store = IdentityStore::open(&path).await?;
    let tenant_key = format!("{organization}:{subject}");
    let version_one = plane
        .persist_identity_snapshot(&store, &tenant_key, None, Authority::PersistControlPlane)
        .await?;
    plane.rotate_key(
        &organization,
        &subject,
        "key-2",
        &active_fingerprint,
        Authority::PersistControlPlane,
    )?;
    let version_two = plane
        .persist_identity_snapshot(
            &store,
            &tenant_key,
            Some(version_one),
            Authority::PersistControlPlane,
        )
        .await?;

    let mut negatives = 0;
    negatives += negative(
        plane
            .authenticate(&organization, &subject, &old_fingerprint)
            .is_err(),
    );
    negatives += negative(
        plane
            .persist_identity_snapshot(
                &store,
                &tenant_key,
                Some(version_one),
                Authority::PersistControlPlane,
            )
            .await
            .is_err(),
    );
    store.close().await;
    drop(store);
    let reopened = IdentityStore::open(&path).await?;
    let (snapshot, restored_version) = reopened
        .load(&tenant_key)
        .await?
        .ok_or_else(|| PlaneError::Storage("IDENTITY_SNAPSHOT_MISSING_AFTER_REOPEN".into()))?;
    if restored_version != version_two {
        return Err(PlaneError::Storage(
            "IDENTITY_VERSION_DIVERGED_AFTER_REOPEN".into(),
        ));
    }
    let restored = snapshot.verify()?;
    restored.authenticate(&organization, &subject, &active_fingerprint)?;
    negatives += negative(
        restored
            .authenticate(&organization, &subject, &old_fingerprint)
            .is_err(),
    );
    reopened.close().await;
    drop(reopened);
    let _ = std::fs::remove_file(&path);

    let mode = [Mode::Hosted, Mode::Byoc, Mode::Private][index];
    let request = fixture_request(&organization, mode, provider.as_str());
    let target = fixture_target(provider, mode);
    let admission = plane.admit_run(
        &organization,
        &subject,
        &active_fingerprint,
        &request,
        &target,
        Authority::PersistControlPlane,
    )?;
    let replay = plane.admit_run(
        &organization,
        &subject,
        &active_fingerprint,
        &request,
        &target,
        Authority::PersistControlPlane,
    )?;
    if replay.reservation.id != admission.reservation.id
        || replay.receipt_digest != admission.receipt_digest
    {
        return Err(PlaneError::Receipt("RUN_IDEMPOTENCY_DIVERGED".into()));
    }

    let mut weak_target = target.clone();
    weak_target.zones = 1;
    negatives += negative(
        plane
            .admit_run(
                &organization,
                &subject,
                &active_fingerprint,
                &fixture_request(&organization, mode, "weak-target"),
                &weak_target,
                Authority::PersistControlPlane,
            )
            .is_err(),
    );
    let mut expensive = fixture_request(&organization, mode, "cost-fence");
    expensive.requested.insert(Meter::GpuSeconds, 11_000);
    negatives += negative(
        plane
            .admit_run(
                &organization,
                &subject,
                &active_fingerprint,
                &expensive,
                &target,
                Authority::PersistControlPlane,
            )
            .is_err(),
    );
    negatives += negative(
        plane
            .authorize_run(
                &admission.reservation.id,
                &organization,
                &subject,
                &active_fingerprint,
                Authority::Observe,
            )
            .is_err(),
    );
    let permit = plane.authorize_run(
        &admission.reservation.id,
        &organization,
        &subject,
        &active_fingerprint,
        Authority::ModifyExternalObject,
    )?;
    let actual_usage = BTreeMap::from([
        (Meter::GpuSeconds, 3_000),
        (Meter::InputTokens, 90_000),
        (Meter::OutputTokens, 15_000),
        (Meter::Rollouts, 1),
    ]);
    let intent = plane.reconcile_and_construct_metering(
        &permit,
        actual_usage.clone(),
        Authority::PersistControlPlane,
    )?;
    let replayed_intent = plane.reconcile_and_construct_metering(
        &permit,
        actual_usage,
        Authority::PersistControlPlane,
    )?;
    if replayed_intent != intent {
        return Err(PlaneError::Receipt("USAGE_REPLAY_DIVERGED".into()));
    }

    let artifact_digest = format!("blake3:{}", "a".repeat(64));
    commerce.bind_manufacture(&permit.receipt_digest)?;
    commerce.bind_delivery(&artifact_digest)?;
    commerce.verify_delivery(&artifact_digest)?;
    commerce.derive_usage(&intent.source_usage_receipt, intent.billable_units)?;
    let meter = commerce.observe(&binding.observation(
        ProviderEventKind::MeterAccepted,
        "meter-event",
        intent.billable_units,
        0,
    ))?;
    let mut wrong_settlement = binding.observation(
        ProviderEventKind::Settlement,
        "wrong-settlement",
        intent.billable_units,
        intent.amount_micros.saturating_add(1),
    );
    wrong_settlement.currency.clone_from(&intent.currency);
    negatives += negative(commerce.observe(&wrong_settlement).is_err());
    let settlement = commerce.observe(&binding.observation(
        ProviderEventKind::Settlement,
        "settlement-event",
        intent.billable_units,
        intent.amount_micros,
    ))?;
    plane.accept_settlement(&intent, &meter, &settlement, Authority::PersistControlPlane)?;

    Ok((
        provider.as_str().into(),
        format!("{mode:?}").to_ascii_lowercase(),
        commerce.replay_verify()?,
        plane.replay_verify()?,
        negatives,
    ))
}

pub async fn verify_full_fixtures() -> Result<FullVerificationReport, PlaneError> {
    let ServiceVerificationReport {
        receipts_verified: service_receipts_verified,
        negative_fixtures_verified: service_negatives,
        ..
    } = verify_service_fixtures()?;
    let mut providers = Vec::new();
    let mut modes = BTreeSet::new();
    let mut commerce_receipts = 0_usize;
    let mut control_receipts = 0_usize;
    let mut negatives = service_negatives;
    let mut durable_reopens = 0_usize;
    for (index, provider) in [Provider::Aws, Provider::Microsoft, Provider::Google]
        .into_iter()
        .enumerate()
    {
        let (provider_name, mode, commerce_count, control_count, provider_negatives) =
            verify_provider(index, provider).await?;
        providers.push(provider_name);
        modes.insert(mode);
        commerce_receipts = commerce_receipts.saturating_add(commerce_count);
        control_receipts = control_receipts.saturating_add(control_count);
        negatives = negatives.saturating_add(provider_negatives);
        durable_reopens = durable_reopens.saturating_add(1);
    }
    Ok(FullVerificationReport {
        implementation_standing: "ALIVE".into(),
        service_standing: "PARTIAL_ALIVE".into(),
        repository: crate::agent_lightning_service::REPOSITORY.into(),
        sha: crate::agent_lightning_service::SHA.into(),
        providers_verified: providers,
        modes_verified: modes.into_iter().collect(),
        service_receipts_verified,
        commerce_receipts_verified: commerce_receipts,
        control_receipts_verified: control_receipts,
        negative_fixtures_verified: negatives,
        durable_identity_reopens_verified: durable_reopens,
        invariants: vec![
            "exact Agent Lightning Git SHA remains the admitted workload identity".into(),
            "raw API key material is excluded; only BLAKE3 fingerprints enter control state".into(),
            "API key registration rotation revocation and stale-key refusal are receipted".into(),
            "identity state survives file-backed SQLite close and reopen with optimistic version fencing".into(),
            "deployment admission fences region mode zones replicas RPO RTO private network receipt durability and CMK requirements".into(),
            "reserved multi-dimensional usage is priced before DO and fenced by per-job and period budgets".into(),
            "Agent Lightning actuation still requires the prior service actuation receipt".into(),
            "actual usage cannot exceed reservation and deterministically manufactures a provider-neutral metering intent".into(),
            "provider meter and settlement receipts must exactly match the admitted billing intent".into(),
            "service commerce and commercial-plane receipt chains replay independently".into(),
        ],
        blockers: vec![
            "BLOCKED:LIVE_GPU_RL_TRAINING_JOB_AT_PINNED_AGENT_LIGHTNING_SHA_NOT_OBSERVED".into(),
            "BLOCKED:LIVE_MARKETPLACE_PURCHASE_METER_SETTLEMENT_ROUNDTRIP_NOT_OBSERVED".into(),
            "BLOCKED:PRODUCTION_KMS_SECRET_BACKEND_AND_ROTATION_POSTCONDITIONS_NOT_OBSERVED".into(),
            "BLOCKED:PRODUCTION_MULTI_ZONE_HA_DR_POSTCONDITIONS_NOT_OBSERVED".into(),
        ],
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn full_commercial_plane_replays() -> Result<(), PlaneError> {
        let report = verify_full_fixtures().await?;
        assert_eq!(report.implementation_standing, "ALIVE");
        assert_eq!(report.service_standing, "PARTIAL_ALIVE");
        assert_eq!(report.providers_verified.len(), 3);
        assert_eq!(report.modes_verified.len(), 3);
        assert_eq!(report.durable_identity_reopens_verified, 3);
        assert!(report.negative_fixtures_verified >= 36);
        Ok(())
    }

    #[test]
    fn byoc_requires_customer_managed_key() {
        let policy = DeploymentPolicy::enterprise_default();
        let organization = "organization:test";
        let request = fixture_request(organization, Mode::Byoc, "cmk");
        let mut target = fixture_target(Provider::Aws, Mode::Byoc);
        target
            .features
            .remove(&DeploymentFeature::CustomerManagedKey);
        assert!(policy.admit(&request, &target).is_err());
    }

    #[test]
    fn rate_card_rejects_unpriced_or_overflowing_usage() -> Result<(), PlaneError> {
        let card = verification_rate_card()?;
        let huge = BTreeMap::from([(Meter::GpuSeconds, u64::MAX)]);
        assert!(card.quote(&huge).is_err());
        Ok(())
    }
}
