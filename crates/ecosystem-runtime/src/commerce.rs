#![allow(
    dead_code,
    clippy::doc_markdown,
    clippy::missing_errors_doc,
    clippy::module_name_repetitions,
    clippy::similar_names,
    clippy::too_many_lines
)]

//! Canonical commercial-standing kernel for cloud marketplace commerce.
//! Provider payloads are observations. Mutating transitions require explicit authority.

use ecosystem_core::{Authority, Receipt, ReceiptId, Standing};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::collections::BTreeMap;

#[derive(Debug, thiserror::Error)]
pub enum CommerceError {
    #[error("REFUSED:{0}")]
    Refused(String),
    #[error("PROVIDER:{0}")]
    Provider(String),
    #[error("RECEIPT:{0}")]
    Receipt(String),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Provider {
    Aws,
    Microsoft,
    Google,
}

impl Provider {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Aws => "aws",
            Self::Microsoft => "microsoft",
            Self::Google => "google",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProviderEventKind {
    Agreement,
    Entitlement,
    EntitlementChanged,
    Suspended,
    Reinstated,
    Revoked,
    MeterAccepted,
    Settlement,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ReceiptKind {
    AgreementObserved,
    EntitlementAdmitted,
    EntitlementChanged,
    EntitlementSuspended,
    EntitlementReinstated,
    EntitlementRevoked,
    FulfillmentAuthorized,
    ManufactureBound,
    DeliveryBound,
    DeliveryVerified,
    UsageDerived,
    MeterAccepted,
    SettlementReconciled,
    CreditApplied,
    RefundReconciled,
}

impl ReceiptKind {
    #[must_use]
    pub const fn authority(self) -> Authority {
        match self {
            Self::AgreementObserved
            | Self::EntitlementAdmitted
            | Self::EntitlementChanged
            | Self::ManufactureBound
            | Self::DeliveryBound
            | Self::DeliveryVerified
            | Self::UsageDerived
            | Self::SettlementReconciled => Authority::PersistControlPlane,
            Self::EntitlementSuspended
            | Self::EntitlementReinstated
            | Self::EntitlementRevoked
            | Self::FulfillmentAuthorized => Authority::ModifyExternalObject,
            Self::MeterAccepted | Self::CreditApplied | Self::RefundReconciled => Authority::Spend,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum EntitlementStatus {
    Unknown,
    Active,
    Suspended,
    Revoked,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CommercialState {
    Discovered,
    AgreementObserved,
    Entitled,
    Fulfilled,
    Manufactured,
    Delivered,
    Verified,
    UsageRecorded,
    Metered,
    Reconciled,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProviderObservation {
    pub provider: Provider,
    pub kind: ProviderEventKind,
    pub event_ref: String,
    pub buyer_ref: String,
    pub product_ref: String,
    pub agreement_ref: String,
    pub entitlement_ref: String,
    pub subscription_ref: String,
    pub plan: String,
    pub dimension: String,
    pub quantity: u64,
    pub units: u64,
    pub amount_micros: u64,
    pub currency: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommerceContext {
    pub seller: String,
    pub buyer: String,
    pub product: String,
    pub capability: String,
    pub sku: String,
    pub offer: String,
    pub order: String,
    pub agreement: String,
    pub subscription: String,
    pub entitlement: String,
    pub fulfillment: String,
    pub provider: Provider,
    pub provider_buyer_ref: String,
    pub provider_product_ref: String,
    pub provider_agreement_ref: String,
    pub provider_entitlement_ref: String,
    pub provider_subscription_ref: String,
    pub unit_price_micros: u64,
    pub currency: String,
}

impl CommerceContext {
    fn validate(&self) -> Result<(), CommerceError> {
        for (name, value) in [
            ("seller", self.seller.as_str()),
            ("buyer", self.buyer.as_str()),
            ("product", self.product.as_str()),
            ("capability", self.capability.as_str()),
            ("sku", self.sku.as_str()),
            ("offer", self.offer.as_str()),
            ("order", self.order.as_str()),
            ("agreement", self.agreement.as_str()),
            ("subscription", self.subscription.as_str()),
            ("entitlement", self.entitlement.as_str()),
            ("fulfillment", self.fulfillment.as_str()),
            ("provider_buyer_ref", self.provider_buyer_ref.as_str()),
            ("provider_product_ref", self.provider_product_ref.as_str()),
            (
                "provider_agreement_ref",
                self.provider_agreement_ref.as_str(),
            ),
            (
                "provider_entitlement_ref",
                self.provider_entitlement_ref.as_str(),
            ),
            (
                "provider_subscription_ref",
                self.provider_subscription_ref.as_str(),
            ),
        ] {
            if value.trim().is_empty() {
                return Err(CommerceError::Refused(format!("MISSING_{name}")));
            }
        }
        if self.unit_price_micros == 0 || self.currency.trim().is_empty() {
            return Err(CommerceError::Refused("INVALID_PRICE".into()));
        }
        Ok(())
    }

    fn admit_observation(&self, observation: &ProviderObservation) -> Result<(), CommerceError> {
        if observation.provider != self.provider {
            return Err(CommerceError::Refused("PROVIDER_MISMATCH".into()));
        }
        for (name, observed, expected) in [
            (
                "BUYER",
                observation.buyer_ref.as_str(),
                self.provider_buyer_ref.as_str(),
            ),
            (
                "PRODUCT",
                observation.product_ref.as_str(),
                self.provider_product_ref.as_str(),
            ),
            (
                "AGREEMENT",
                observation.agreement_ref.as_str(),
                self.provider_agreement_ref.as_str(),
            ),
            (
                "ENTITLEMENT",
                observation.entitlement_ref.as_str(),
                self.provider_entitlement_ref.as_str(),
            ),
            (
                "SUBSCRIPTION",
                observation.subscription_ref.as_str(),
                self.provider_subscription_ref.as_str(),
            ),
        ] {
            if observed != expected {
                return Err(CommerceError::Refused(format!("{name}_IDENTITY_MISMATCH")));
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommercialReceipt {
    pub kind: ReceiptKind,
    pub state_before: CommercialState,
    pub state_after: CommercialState,
    pub provider_event_ref: String,
    pub source_receipt: String,
    pub previous_digest: String,
    pub units: u64,
    pub amount_micros: u64,
    pub core: Receipt,
}

impl CommercialReceipt {
    pub fn verify(&self) -> Result<(), CommerceError> {
        self.core
            .verify()
            .map_err(|error| CommerceError::Receipt(error.to_string()))?;
        if self.core.authority != self.kind.authority() {
            return Err(CommerceError::Receipt("AUTHORITY_KIND_MISMATCH".into()));
        }
        if self.provider_event_ref.trim().is_empty() {
            return Err(CommerceError::Receipt("MISSING_PROVIDER_EVENT_REF".into()));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerificationReport {
    pub standing: String,
    pub providers_verified: Vec<String>,
    pub receipts_verified: usize,
    pub negative_fixtures_verified: usize,
    pub external_blockers: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct TransitionInput {
    pub kind: ReceiptKind,
    pub authority: Authority,
    pub idempotency_key: String,
    pub event_ref: String,
    pub source_receipt: String,
    pub units: u64,
    pub amount_micros: u64,
}

#[derive(Debug)]
pub struct CommerceLedger {
    context: CommerceContext,
    state: CommercialState,
    entitlement: EntitlementStatus,
    quantity: u64,
    plan: String,
    usage_units: u64,
    metered_units: u64,
    settlement_micros: u64,
    credits_micros: u64,
    refunds_micros: u64,
    receipts: Vec<CommercialReceipt>,
    idempotency: BTreeMap<String, (String, usize)>,
}

impl CommerceLedger {
    pub fn new(context: CommerceContext) -> Result<Self, CommerceError> {
        context.validate()?;
        Ok(Self {
            context,
            state: CommercialState::Discovered,
            entitlement: EntitlementStatus::Unknown,
            quantity: 0,
            plan: String::new(),
            usage_units: 0,
            metered_units: 0,
            settlement_micros: 0,
            credits_micros: 0,
            refunds_micros: 0,
            receipts: Vec::new(),
            idempotency: BTreeMap::new(),
        })
    }

    pub fn observe(
        &mut self,
        observation: &ProviderObservation,
    ) -> Result<CommercialReceipt, CommerceError> {
        self.context.admit_observation(observation)?;
        match observation.kind {
            ProviderEventKind::Agreement => self.apply(TransitionInput {
                kind: ReceiptKind::AgreementObserved,
                authority: Authority::PersistControlPlane,
                idempotency_key: format!("agreement:{}", observation.event_ref),
                event_ref: observation.event_ref.clone(),
                source_receipt: String::new(),
                units: 0,
                amount_micros: 0,
            }),
            ProviderEventKind::Entitlement => {
                if observation.quantity == 0 {
                    return Err(CommerceError::Refused("ZERO_ENTITLEMENT_QUANTITY".into()));
                }
                self.quantity = observation.quantity;
                self.plan.clone_from(&observation.plan);
                self.entitlement = EntitlementStatus::Active;
                self.apply(TransitionInput {
                    kind: ReceiptKind::EntitlementAdmitted,
                    authority: Authority::PersistControlPlane,
                    idempotency_key: format!("entitlement:{}", observation.event_ref),
                    event_ref: observation.event_ref.clone(),
                    source_receipt: String::new(),
                    units: 0,
                    amount_micros: 0,
                })
            }
            ProviderEventKind::EntitlementChanged => {
                if observation.quantity == 0 || observation.plan.trim().is_empty() {
                    return Err(CommerceError::Refused("INVALID_ENTITLEMENT_CHANGE".into()));
                }
                self.quantity = observation.quantity;
                self.plan.clone_from(&observation.plan);
                self.apply(TransitionInput {
                    kind: ReceiptKind::EntitlementChanged,
                    authority: Authority::PersistControlPlane,
                    idempotency_key: format!("entitlement-change:{}", observation.event_ref),
                    event_ref: observation.event_ref.clone(),
                    source_receipt: String::new(),
                    units: 0,
                    amount_micros: 0,
                })
            }
            ProviderEventKind::Suspended => {
                self.entitlement = EntitlementStatus::Suspended;
                self.apply(TransitionInput {
                    kind: ReceiptKind::EntitlementSuspended,
                    authority: Authority::ModifyExternalObject,
                    idempotency_key: format!("suspend:{}", observation.event_ref),
                    event_ref: observation.event_ref.clone(),
                    source_receipt: String::new(),
                    units: 0,
                    amount_micros: 0,
                })
            }
            ProviderEventKind::Reinstated => {
                self.entitlement = EntitlementStatus::Active;
                self.apply(TransitionInput {
                    kind: ReceiptKind::EntitlementReinstated,
                    authority: Authority::ModifyExternalObject,
                    idempotency_key: format!("reinstate:{}", observation.event_ref),
                    event_ref: observation.event_ref.clone(),
                    source_receipt: String::new(),
                    units: 0,
                    amount_micros: 0,
                })
            }
            ProviderEventKind::Revoked => {
                self.entitlement = EntitlementStatus::Revoked;
                self.apply(TransitionInput {
                    kind: ReceiptKind::EntitlementRevoked,
                    authority: Authority::ModifyExternalObject,
                    idempotency_key: format!("revoke:{}", observation.event_ref),
                    event_ref: observation.event_ref.clone(),
                    source_receipt: String::new(),
                    units: 0,
                    amount_micros: 0,
                })
            }
            ProviderEventKind::MeterAccepted => self.accept_meter(observation),
            ProviderEventKind::Settlement => self.reconcile(observation),
        }
    }

    pub fn authorize_fulfillment(
        &mut self,
        idempotency_key: &str,
    ) -> Result<CommercialReceipt, CommerceError> {
        if self.entitlement != EntitlementStatus::Active || self.quantity == 0 {
            return Err(CommerceError::Refused("NO_ACTIVE_ENTITLEMENT".into()));
        }
        self.apply(TransitionInput {
            kind: ReceiptKind::FulfillmentAuthorized,
            authority: Authority::ModifyExternalObject,
            idempotency_key: idempotency_key.into(),
            event_ref: format!("{}:fulfillment", self.context.provider.as_str()),
            source_receipt: String::new(),
            units: 0,
            amount_micros: 0,
        })
    }

    pub fn bind_manufacture(
        &mut self,
        source_receipt: &str,
    ) -> Result<CommercialReceipt, CommerceError> {
        if self.state != CommercialState::Fulfilled || source_receipt.trim().is_empty() {
            return Err(CommerceError::Refused(
                "MANUFACTURE_REQUIRES_FULFILLMENT_RECEIPT".into(),
            ));
        }
        self.apply(TransitionInput {
            kind: ReceiptKind::ManufactureBound,
            authority: Authority::PersistControlPlane,
            idempotency_key: format!("manufacture:{source_receipt}"),
            event_ref: format!("{}:manufacture", self.context.provider.as_str()),
            source_receipt: source_receipt.into(),
            units: 0,
            amount_micros: 0,
        })
    }

    pub fn bind_delivery(
        &mut self,
        artifact_digest: &str,
    ) -> Result<CommercialReceipt, CommerceError> {
        if self.state != CommercialState::Manufactured || !artifact_digest.starts_with("blake3:") {
            return Err(CommerceError::Refused(
                "DELIVERY_REQUIRES_MANUFACTURED_DIGEST".into(),
            ));
        }
        self.apply(TransitionInput {
            kind: ReceiptKind::DeliveryBound,
            authority: Authority::PersistControlPlane,
            idempotency_key: format!("delivery:{artifact_digest}"),
            event_ref: format!("{}:delivery", self.context.provider.as_str()),
            source_receipt: artifact_digest.into(),
            units: 0,
            amount_micros: 0,
        })
    }

    pub fn verify_delivery(&mut self, digest: &str) -> Result<CommercialReceipt, CommerceError> {
        if self.state != CommercialState::Delivered || !digest.starts_with("blake3:") {
            return Err(CommerceError::Refused("DELIVERY_NOT_VERIFIABLE".into()));
        }
        self.apply(TransitionInput {
            kind: ReceiptKind::DeliveryVerified,
            authority: Authority::PersistControlPlane,
            idempotency_key: format!("verify:{digest}"),
            event_ref: format!("{}:verified", self.context.provider.as_str()),
            source_receipt: digest.into(),
            units: 0,
            amount_micros: 0,
        })
    }

    pub fn derive_usage(
        &mut self,
        source_receipt: &str,
        units: u64,
    ) -> Result<CommercialReceipt, CommerceError> {
        if self.state != CommercialState::Verified || units == 0 || source_receipt.trim().is_empty()
        {
            return Err(CommerceError::Refused(
                "USAGE_REQUIRES_VERIFIED_FULFILLMENT".into(),
            ));
        }
        self.usage_units = self.usage_units.saturating_add(units);
        self.apply(TransitionInput {
            kind: ReceiptKind::UsageDerived,
            authority: Authority::PersistControlPlane,
            idempotency_key: format!("usage:{source_receipt}:{units}"),
            event_ref: format!("{}:usage", self.context.provider.as_str()),
            source_receipt: source_receipt.into(),
            units,
            amount_micros: 0,
        })
    }

    pub fn apply_credit(
        &mut self,
        key: &str,
        amount_micros: u64,
    ) -> Result<CommercialReceipt, CommerceError> {
        if self.state != CommercialState::Reconciled || amount_micros == 0 {
            return Err(CommerceError::Refused(
                "CREDIT_REQUIRES_RECONCILED_SETTLEMENT".into(),
            ));
        }
        let adjusted = self
            .credits_micros
            .saturating_add(self.refunds_micros)
            .saturating_add(amount_micros);
        if adjusted > self.settlement_micros {
            return Err(CommerceError::Refused(
                "ADJUSTMENT_EXCEEDS_SETTLEMENT".into(),
            ));
        }
        self.credits_micros = self.credits_micros.saturating_add(amount_micros);
        self.apply(TransitionInput {
            kind: ReceiptKind::CreditApplied,
            authority: Authority::Spend,
            idempotency_key: key.into(),
            event_ref: format!("{}:credit", self.context.provider.as_str()),
            source_receipt: String::new(),
            units: 0,
            amount_micros,
        })
    }

    pub fn reconcile_refund(
        &mut self,
        key: &str,
        amount_micros: u64,
    ) -> Result<CommercialReceipt, CommerceError> {
        if self.state != CommercialState::Reconciled || amount_micros == 0 {
            return Err(CommerceError::Refused(
                "REFUND_REQUIRES_RECONCILED_SETTLEMENT".into(),
            ));
        }
        let adjusted = self
            .credits_micros
            .saturating_add(self.refunds_micros)
            .saturating_add(amount_micros);
        if adjusted > self.settlement_micros {
            return Err(CommerceError::Refused(
                "ADJUSTMENT_EXCEEDS_SETTLEMENT".into(),
            ));
        }
        self.refunds_micros = self.refunds_micros.saturating_add(amount_micros);
        self.apply(TransitionInput {
            kind: ReceiptKind::RefundReconciled,
            authority: Authority::Spend,
            idempotency_key: key.into(),
            event_ref: format!("{}:refund", self.context.provider.as_str()),
            source_receipt: String::new(),
            units: 0,
            amount_micros,
        })
    }

    pub fn replay_verify(&self) -> Result<usize, CommerceError> {
        let mut previous = String::new();
        for receipt in &self.receipts {
            receipt.verify()?;
            if receipt.previous_digest != previous {
                return Err(CommerceError::Receipt("RECEIPT_CHAIN_MISMATCH".into()));
            }
            previous.clone_from(&receipt.core.digest);
        }
        Ok(self.receipts.len())
    }

    fn accept_meter(
        &mut self,
        observation: &ProviderObservation,
    ) -> Result<CommercialReceipt, CommerceError> {
        if self.state != CommercialState::UsageRecorded
            || observation.units != self.usage_units
            || observation.units == 0
        {
            return Err(CommerceError::Refused(
                "METER_MUST_EQUAL_RECEIPTED_USAGE".into(),
            ));
        }
        self.metered_units = observation.units;
        self.apply(TransitionInput {
            kind: ReceiptKind::MeterAccepted,
            authority: Authority::Spend,
            idempotency_key: format!("meter:{}", observation.event_ref),
            event_ref: observation.event_ref.clone(),
            source_receipt: String::new(),
            units: observation.units,
            amount_micros: 0,
        })
    }

    fn reconcile(
        &mut self,
        observation: &ProviderObservation,
    ) -> Result<CommercialReceipt, CommerceError> {
        if self.state != CommercialState::Metered {
            return Err(CommerceError::Refused(
                "SETTLEMENT_REQUIRES_ACCEPTED_METER".into(),
            ));
        }
        let expected = self
            .context
            .unit_price_micros
            .saturating_mul(self.metered_units);
        if observation.amount_micros != expected || observation.currency != self.context.currency {
            return Err(CommerceError::Refused("SETTLEMENT_MISMATCH".into()));
        }
        self.settlement_micros = observation.amount_micros;
        self.apply(TransitionInput {
            kind: ReceiptKind::SettlementReconciled,
            authority: Authority::PersistControlPlane,
            idempotency_key: format!("settlement:{}", observation.event_ref),
            event_ref: observation.event_ref.clone(),
            source_receipt: String::new(),
            units: self.metered_units,
            amount_micros: observation.amount_micros,
        })
    }

    fn apply(&mut self, input: TransitionInput) -> Result<CommercialReceipt, CommerceError> {
        if input.idempotency_key.trim().is_empty() {
            return Err(CommerceError::Refused("IDEMPOTENCY_KEY_REQUIRED".into()));
        }
        let required = input.kind.authority();
        if input.authority != required {
            return Err(CommerceError::Refused(format!(
                "AUTHORITY_DENIED_HAVE_{:?}_REQUIRE_{required:?}",
                input.authority
            )));
        }
        let fingerprint = serde_json::to_string(&json!({
            "kind": input.kind, "event": input.event_ref, "source": input.source_receipt,
            "units": input.units, "amount": input.amount_micros
        }))
        .map_err(|error| CommerceError::Receipt(error.to_string()))?;
        if let Some((existing, index)) = self.idempotency.get(&input.idempotency_key) {
            if existing != &fingerprint {
                return Err(CommerceError::Refused("IDEMPOTENCY_KEY_CONFLICT".into()));
            }
            return self
                .receipts
                .get(*index)
                .cloned()
                .ok_or_else(|| CommerceError::Receipt("IDEMPOTENCY_INDEX_MISSING".into()));
        }
        let before = self.state;
        let after = next_state(self.state, input.kind)?;
        let previous_digest = self
            .receipts
            .last()
            .map_or_else(String::new, |receipt| receipt.core.digest.clone());
        let id = format!(
            "receipt:commerce-{}-{}",
            self.context.provider.as_str(),
            self.receipts.len() + 1
        );
        let mut core = Receipt {
            id: ReceiptId::parse(id).map_err(|error| CommerceError::Receipt(error.to_string()))?,
            subject: format!(
                "commerce:{}:{}",
                self.context.provider.as_str(),
                self.context.agreement
            ),
            actor: "marketplace-commerce".into(),
            authority: input.authority,
            intention: format!("{:?}", input.kind),
            observed: vec![input.event_ref.clone()],
            executed: vec![format!("{:?}", input.kind)],
            changed: vec![format!("{before:?}->{after:?}")],
            verified: vec!["commercial preconditions admitted".into()],
            excluded: vec![],
            replay: vec!["marketplace-commerce verify-fixtures".into()],
            standing_before: Standing::PartialAlive,
            standing_after: Standing::PartialAlive,
            timestamp: "2026-08-19T00:00:00Z".into(),
            digest: String::new(),
        };
        core.sign()
            .map_err(|error| CommerceError::Receipt(error.to_string()))?;
        let receipt = CommercialReceipt {
            kind: input.kind,
            state_before: before,
            state_after: after,
            provider_event_ref: input.event_ref,
            source_receipt: input.source_receipt,
            previous_digest,
            units: input.units,
            amount_micros: input.amount_micros,
            core,
        };
        receipt.verify()?;
        self.state = after;
        let index = self.receipts.len();
        self.receipts.push(receipt.clone());
        self.idempotency
            .insert(input.idempotency_key, (fingerprint, index));
        Ok(receipt)
    }
}

fn next_state(
    current: CommercialState,
    kind: ReceiptKind,
) -> Result<CommercialState, CommerceError> {
    let next = match kind {
        ReceiptKind::AgreementObserved if current == CommercialState::Discovered => {
            CommercialState::AgreementObserved
        }
        ReceiptKind::EntitlementAdmitted if current == CommercialState::AgreementObserved => {
            CommercialState::Entitled
        }
        ReceiptKind::EntitlementChanged
        | ReceiptKind::EntitlementSuspended
        | ReceiptKind::EntitlementReinstated
        | ReceiptKind::EntitlementRevoked => current,
        ReceiptKind::FulfillmentAuthorized if current == CommercialState::Entitled => {
            CommercialState::Fulfilled
        }
        ReceiptKind::ManufactureBound if current == CommercialState::Fulfilled => {
            CommercialState::Manufactured
        }
        ReceiptKind::DeliveryBound if current == CommercialState::Manufactured => {
            CommercialState::Delivered
        }
        ReceiptKind::DeliveryVerified if current == CommercialState::Delivered => {
            CommercialState::Verified
        }
        ReceiptKind::UsageDerived if current == CommercialState::Verified => {
            CommercialState::UsageRecorded
        }
        ReceiptKind::MeterAccepted if current == CommercialState::UsageRecorded => {
            CommercialState::Metered
        }
        ReceiptKind::SettlementReconciled if current == CommercialState::Metered => {
            CommercialState::Reconciled
        }
        ReceiptKind::CreditApplied | ReceiptKind::RefundReconciled
            if current == CommercialState::Reconciled =>
        {
            CommercialState::Reconciled
        }
        _ => {
            return Err(CommerceError::Refused(format!(
                "ILLEGAL_COMMERCIAL_TRANSITION_{current:?}_{kind:?}"
            )));
        }
    };
    Ok(next)
}

pub fn normalize(
    provider: Provider,
    kind: ProviderEventKind,
    input: &str,
) -> Result<ProviderObservation, CommerceError> {
    let value: Value =
        serde_json::from_str(input).map_err(|error| CommerceError::Provider(error.to_string()))?;
    let get = |keys: &[&str]| -> String {
        keys.iter()
            .find_map(|key| value.pointer(key).and_then(Value::as_str))
            .unwrap_or_default()
            .to_owned()
    };
    let number = |keys: &[&str]| -> u64 {
        keys.iter()
            .find_map(|key| value.pointer(key).and_then(Value::as_u64))
            .unwrap_or_default()
    };
    let mut observation = match provider {
        Provider::Aws => ProviderObservation {
            provider,
            kind,
            event_ref: get(&[
                "/EventId",
                "/MeteringRecordId",
                "/SettlementId",
                "/LicenseArn",
            ]),
            buyer_ref: get(&["/CustomerAWSAccountId"]),
            product_ref: get(&["/ProductCode"]),
            agreement_ref: get(&["/LicenseArn"]),
            entitlement_ref: get(&["/LicenseArn"]),
            subscription_ref: get(&["/LicenseArn"]),
            plan: get(&["/Dimension", "/Plan"]),
            dimension: get(&["/Dimension"]),
            quantity: number(&["/Quantity"]),
            units: number(&["/UsageQuantity", "/Units"]),
            amount_micros: number(&["/AmountMicros"]),
            currency: get(&["/Currency"]),
        },
        Provider::Microsoft => ProviderObservation {
            provider,
            kind,
            event_ref: get(&["/activityId", "/usageEventId", "/settlementId", "/id"]),
            buyer_ref: get(&[
                "/purchaser/tenantId",
                "/beneficiary/tenantId",
                "/purchaserTenantId",
            ]),
            product_ref: get(&["/offerId"]),
            agreement_ref: get(&["/subscriptionId", "/id"]),
            entitlement_ref: get(&["/subscriptionId", "/id"]),
            subscription_ref: get(&["/subscriptionId", "/id"]),
            plan: get(&["/planId"]),
            dimension: get(&["/dimension"]),
            quantity: number(&["/quantity"]),
            units: number(&["/quantity", "/units"]),
            amount_micros: number(&["/amountMicros"]),
            currency: get(&["/currency"]),
        },
        Provider::Google => ProviderObservation {
            provider,
            kind,
            event_ref: get(&["/eventId", "/operationId", "/settlementId", "/name"]),
            buyer_ref: get(&["/account", "/accountId"]),
            product_ref: get(&["/product", "/productId"]),
            agreement_ref: get(&["/entitlement", "/name", "/entitlementId"]),
            entitlement_ref: get(&["/entitlement", "/name", "/entitlementId"]),
            subscription_ref: get(&["/entitlement", "/name", "/entitlementId"]),
            plan: get(&["/plan", "/planId"]),
            dimension: get(&["/metricName", "/dimension"]),
            quantity: number(&["/quantity"]),
            units: number(&["/usage/units", "/units"]),
            amount_micros: number(&["/amountMicros"]),
            currency: get(&["/currency"]),
        },
    };
    if observation.event_ref.is_empty()
        || observation.buyer_ref.is_empty()
        || observation.product_ref.is_empty()
        || observation.agreement_ref.is_empty()
        || observation.entitlement_ref.is_empty()
        || observation.subscription_ref.is_empty()
    {
        return Err(CommerceError::Provider("MISSING_PROVIDER_IDENTITY".into()));
    }
    if observation.plan.is_empty() {
        observation.plan = "default".into();
    }
    if observation.dimension.is_empty() {
        observation.dimension = "capability".into();
    }
    if observation.currency.is_empty() {
        observation.currency = "USD".into();
    }
    Ok(observation)
}

fn fixture_context(provider: Provider) -> CommerceContext {
    let p = provider.as_str();
    CommerceContext {
        seller: "seller:chatman".into(),
        buyer: format!("buyer:{p}"),
        product: "product:ggen-saas".into(),
        capability: "capability:verified-manufacture".into(),
        sku: "sku:enterprise".into(),
        offer: "offer:private".into(),
        order: format!("order:{p}"),
        agreement: format!("agreement:{p}"),
        subscription: format!("subscription:{p}"),
        entitlement: format!("entitlement:{p}"),
        fulfillment: format!("fulfillment:{p}"),
        provider,
        provider_buyer_ref: format!("{p}-buyer"),
        provider_product_ref: format!("{p}-product"),
        provider_agreement_ref: format!("{p}-agreement"),
        provider_entitlement_ref: format!("{p}-agreement"),
        provider_subscription_ref: format!("{p}-agreement"),
        unit_price_micros: 10_000,
        currency: "USD".into(),
    }
}

fn fixture_observation(
    context: &CommerceContext,
    kind: ProviderEventKind,
    event: &str,
) -> ProviderObservation {
    ProviderObservation {
        provider: context.provider,
        kind,
        event_ref: event.into(),
        buyer_ref: context.provider_buyer_ref.clone(),
        product_ref: context.provider_product_ref.clone(),
        agreement_ref: context.provider_agreement_ref.clone(),
        entitlement_ref: context.provider_entitlement_ref.clone(),
        subscription_ref: context.provider_subscription_ref.clone(),
        plan: "enterprise".into(),
        dimension: "verified-manufacture".into(),
        quantity: 5,
        units: 3,
        amount_micros: 30_000,
        currency: "USD".into(),
    }
}

fn signed_fixture_receipt(provider: Provider) -> Result<Receipt, CommerceError> {
    let mut receipt = Receipt {
        id: ReceiptId::parse(format!("receipt:manufacture-{}", provider.as_str()))
            .map_err(|error| CommerceError::Receipt(error.to_string()))?,
        subject: "artifact:fixture".into(),
        actor: "ggen".into(),
        authority: Authority::PersistControlPlane,
        intention: "manufacture exact fixture".into(),
        observed: vec!["admitted fixture".into()],
        executed: vec!["ggen".into()],
        changed: vec!["artifact".into()],
        verified: vec!["artifact digest".into()],
        excluded: vec![],
        replay: vec!["fixture replay".into()],
        standing_before: Standing::PartialAlive,
        standing_after: Standing::PartialAlive,
        timestamp: "2026-08-19T00:00:00Z".into(),
        digest: String::new(),
    };
    receipt
        .sign()
        .map_err(|error| CommerceError::Receipt(error.to_string()))?;
    Ok(receipt)
}

pub fn verify_all_provider_fixtures() -> Result<VerificationReport, CommerceError> {
    let mut providers = Vec::new();
    let mut receipts_verified = 0usize;
    let mut negatives = 0usize;
    for provider in [Provider::Aws, Provider::Microsoft, Provider::Google] {
        let context = fixture_context(provider);
        let mut ledger = CommerceLedger::new(context.clone())?;
        ledger.observe(&fixture_observation(
            &context,
            ProviderEventKind::Agreement,
            "agreement-event",
        ))?;
        ledger.observe(&fixture_observation(
            &context,
            ProviderEventKind::Entitlement,
            "entitlement-event",
        ))?;
        let duplicate = ledger.observe(&fixture_observation(
            &context,
            ProviderEventKind::Entitlement,
            "entitlement-event",
        ))?;
        duplicate.verify()?;
        ledger.observe(&fixture_observation(
            &context,
            ProviderEventKind::EntitlementChanged,
            "change-event",
        ))?;
        ledger.authorize_fulfillment("fulfillment-authority")?;
        let manufacture = signed_fixture_receipt(provider)?;
        ledger.bind_manufacture(&manufacture.digest)?;
        ledger.bind_delivery(&manufacture.digest)?;
        ledger.verify_delivery(&manufacture.digest)?;
        ledger.derive_usage(&manufacture.digest, 3)?;
        ledger.observe(&fixture_observation(
            &context,
            ProviderEventKind::MeterAccepted,
            "meter-event",
        ))?;
        ledger.observe(&fixture_observation(
            &context,
            ProviderEventKind::Settlement,
            "settlement-event",
        ))?;
        ledger.apply_credit("credit-event", 5_000)?;
        ledger.reconcile_refund("refund-event", 5_000)?;
        receipts_verified = receipts_verified.saturating_add(ledger.replay_verify()?);

        let mut wrong =
            fixture_observation(&context, ProviderEventKind::EntitlementChanged, "tampered");
        wrong.buyer_ref = "attacker".into();
        if ledger.observe(&wrong).is_err() {
            negatives = negatives.saturating_add(1);
        }
        if ledger
            .apply(TransitionInput {
                kind: ReceiptKind::CreditApplied,
                authority: Authority::Observe,
                idempotency_key: "bad-authority".into(),
                event_ref: "bad".into(),
                source_receipt: String::new(),
                units: 0,
                amount_micros: 1,
            })
            .is_err()
        {
            negatives = negatives.saturating_add(1);
        }

        let mut revoked = CommerceLedger::new(context.clone())?;
        revoked.observe(&fixture_observation(
            &context,
            ProviderEventKind::Agreement,
            "r-agreement",
        ))?;
        revoked.observe(&fixture_observation(
            &context,
            ProviderEventKind::Entitlement,
            "r-entitlement",
        ))?;
        revoked.observe(&fixture_observation(
            &context,
            ProviderEventKind::Suspended,
            "r-suspend",
        ))?;
        if revoked.authorize_fulfillment("blocked-suspended").is_err() {
            negatives = negatives.saturating_add(1);
        }
        revoked.observe(&fixture_observation(
            &context,
            ProviderEventKind::Reinstated,
            "r-reinstate",
        ))?;
        revoked.observe(&fixture_observation(
            &context,
            ProviderEventKind::Revoked,
            "r-revoke",
        ))?;
        if revoked.authorize_fulfillment("blocked-revoked").is_err() {
            negatives = negatives.saturating_add(1);
        }
        receipts_verified = receipts_verified.saturating_add(revoked.replay_verify()?);
        providers.push(provider.as_str().to_owned());
    }
    Ok(VerificationReport {
        standing: "PARTIAL_ALIVE".into(),
        providers_verified: providers,
        receipts_verified,
        negative_fixtures_verified: negatives,
        external_blockers: vec![
            "BLOCKED:REAL_MARKETPLACE_SELLER_CREDENTIALS".into(),
            "BLOCKED:TAX_PAYOUT_AND_LEGAL_ENTITY_ENROLLMENT".into(),
            "BLOCKED:LIVE_BUYER_PURCHASE_ENTITLEMENT_METER_AND_SETTLEMENT_RECEIPTS".into(),
            "BLOCKED:CONTRACTUAL_SLA_AND_PRODUCTION_HA_DR".into(),
            "BLOCKED:INDEPENDENT_SOC2_ATTESTATION".into(),
        ],
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_provider_paths_and_negative_fixtures_replay() -> Result<(), CommerceError> {
        let report = verify_all_provider_fixtures()?;
        assert_eq!(report.providers_verified.len(), 3);
        assert!(report.receipts_verified >= 30);
        assert!(report.negative_fixtures_verified >= 10);
        assert_eq!(report.standing, "PARTIAL_ALIVE");
        Ok(())
    }

    #[test]
    fn aws_concurrent_agreement_identity_is_required() {
        let payload = r#"{"ProductCode":"p","LicenseArn":"l"}"#;
        assert!(normalize(Provider::Aws, ProviderEventKind::Agreement, payload).is_err());
    }

    #[test]
    fn fulfillment_without_entitlement_is_refused() -> Result<(), CommerceError> {
        let context = fixture_context(Provider::Google);
        let mut ledger = CommerceLedger::new(context)?;
        assert!(ledger.authorize_fulfillment("no-entitlement").is_err());
        Ok(())
    }
}
