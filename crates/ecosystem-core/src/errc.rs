//! Executable ERRC production invariants.
//!
//! This module turns the Raise/Create side of the XaaS ERRC grid into typed,
//! testable contracts. It never grants authority and never actuates.

use crate::Receipt;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

/// Semantic capability classes. `Data` is intentionally distinct from `Observe`:
/// Data names a durable/read-only information product, while Observe names a bounded
/// observation operation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CapabilityClass {
    Observe,
    Select,
    Construct,
    Data,
    Do,
}

/// Test standing for an optional external service.
///
/// A mocked-success variant does not exist by design. Optional services either execute
/// against a real server or produce a named skip.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "standing", rename_all = "snake_case")]
pub enum ExternalServiceStanding {
    NotApplicable,
    RealServer { endpoint_identity: String },
    NamedSkip { reason: String },
}

/// Governance facts required to admit one capability implementation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CapabilityGovernance {
    pub capability_id: String,
    pub class: CapabilityClass,
    pub reversible: bool,
    pub broker_required: bool,
    pub receipt_required: bool,
    pub approval_required: bool,
    pub independent_verifier: bool,
    pub durable_audit: bool,
    pub ocel_projection: bool,
    pub external_service: ExternalServiceStanding,
}

/// Exact reason a capability fails the raised production bar.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GovernanceRefusal {
    EmptyCapabilityIdentity,
    DoRequiresBroker,
    DoRequiresReceipt,
    IrreversibleRequiresApproval,
    IrreversibleRequiresIndependentVerifier,
    IrreversibleRequiresDurableAudit,
    IrreversibleRequiresOcelProjection,
    EmptyRealServerIdentity,
    EmptyNamedSkipReason,
}

impl CapabilityGovernance {
    /// Verify the ERRC Raise constraints without granting execution standing.
    pub fn validate(&self) -> Result<(), GovernanceRefusal> {
        if self.capability_id.trim().is_empty() {
            return Err(GovernanceRefusal::EmptyCapabilityIdentity);
        }
        if self.class == CapabilityClass::Do && !self.broker_required {
            return Err(GovernanceRefusal::DoRequiresBroker);
        }
        if self.class == CapabilityClass::Do && !self.receipt_required {
            return Err(GovernanceRefusal::DoRequiresReceipt);
        }
        if !self.reversible {
            if !self.approval_required {
                return Err(GovernanceRefusal::IrreversibleRequiresApproval);
            }
            if !self.independent_verifier {
                return Err(GovernanceRefusal::IrreversibleRequiresIndependentVerifier);
            }
            if !self.durable_audit {
                return Err(GovernanceRefusal::IrreversibleRequiresDurableAudit);
            }
            if !self.ocel_projection {
                return Err(GovernanceRefusal::IrreversibleRequiresOcelProjection);
            }
        }
        match &self.external_service {
            ExternalServiceStanding::RealServer { endpoint_identity }
                if endpoint_identity.trim().is_empty() =>
            {
                Err(GovernanceRefusal::EmptyRealServerIdentity)
            }
            ExternalServiceStanding::NamedSkip { reason } if reason.trim().is_empty() => {
                Err(GovernanceRefusal::EmptyNamedSkipReason)
            }
            _ => Ok(()),
        }
    }
}

/// One object-centric event derived from a verified ecosystem receipt.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OcelEvent {
    pub event_id: String,
    pub activity: String,
    pub timestamp: String,
    pub object_ids: Vec<String>,
    pub attributes: BTreeMap<String, String>,
}

/// Minimal OCEL-compatible projection of the receipt ledger.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReceiptOcelProjection {
    pub object_ids: Vec<String>,
    pub events: Vec<OcelEvent>,
}

impl ReceiptOcelProjection {
    /// Project receipts into an object-centric event graph. This is a read-only
    /// evidence transformation: receipt identity and standing are not upgraded.
    #[must_use]
    pub fn from_receipts(receipts: &[Receipt]) -> Self {
        let mut objects = BTreeSet::new();
        let mut events = Vec::with_capacity(receipts.len());
        for receipt in receipts {
            objects.insert(receipt.subject.clone());
            let mut attributes = BTreeMap::new();
            attributes.insert("actor".to_owned(), receipt.actor.clone());
            attributes.insert("authority".to_owned(), format!("{:?}", receipt.authority));
            attributes.insert("digest".to_owned(), receipt.digest.clone());
            attributes.insert(
                "standing_before".to_owned(),
                format!("{:?}", receipt.standing_before),
            );
            attributes.insert(
                "standing_after".to_owned(),
                format!("{:?}", receipt.standing_after),
            );
            attributes.insert("executed".to_owned(), receipt.executed.join("|"));
            attributes.insert("changed".to_owned(), receipt.changed.join("|"));
            attributes.insert("verified".to_owned(), receipt.verified.join("|"));
            events.push(OcelEvent {
                event_id: receipt.id.0.clone(),
                activity: receipt.intention.clone(),
                timestamp: receipt.timestamp.clone(),
                object_ids: vec![receipt.subject.clone()],
                attributes,
            });
        }
        Self {
            object_ids: objects.into_iter().collect(),
            events,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn irreversible() -> CapabilityGovernance {
        CapabilityGovernance {
            capability_id: "capability:data-destruction".into(),
            class: CapabilityClass::Do,
            reversible: false,
            broker_required: true,
            receipt_required: true,
            approval_required: true,
            independent_verifier: true,
            durable_audit: true,
            ocel_projection: true,
            external_service: ExternalServiceStanding::NamedSkip {
                reason: "real service unavailable in this execution environment".into(),
            },
        }
    }

    #[test]
    fn irreversible_do_requires_the_full_governed_chain() {
        assert_eq!(irreversible().validate(), Ok(()));
        let mut candidate = irreversible();
        candidate.independent_verifier = false;
        assert_eq!(
            candidate.validate(),
            Err(GovernanceRefusal::IrreversibleRequiresIndependentVerifier)
        );
    }

    #[test]
    fn do_without_broker_is_refused() {
        let mut candidate = irreversible();
        candidate.broker_required = false;
        assert_eq!(candidate.validate(), Err(GovernanceRefusal::DoRequiresBroker));
    }

    #[test]
    fn optional_external_service_has_no_mocked_success_state() {
        let candidate = CapabilityGovernance {
            capability_id: "capability:optional-service".into(),
            class: CapabilityClass::Observe,
            reversible: true,
            broker_required: false,
            receipt_required: true,
            approval_required: false,
            independent_verifier: false,
            durable_audit: true,
            ocel_projection: true,
            external_service: ExternalServiceStanding::NamedSkip {
                reason: "server unavailable".into(),
            },
        };
        assert_eq!(candidate.validate(), Ok(()));
    }
}
