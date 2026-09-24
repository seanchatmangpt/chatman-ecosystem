//! Executable ERRC governance invariants and receipt→OCEL projection.

use ecosystem_core::Receipt;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CapabilityClass {
    Observe,
    Select,
    Construct,
    Data,
    Do,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "standing", rename_all = "snake_case")]
pub enum ExternalServiceStanding {
    NotApplicable,
    RealServer { endpoint_identity: String },
    NamedSkip { reason: String },
}

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

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OcelEvent {
    pub event_id: String,
    pub activity: String,
    pub timestamp: String,
    pub object_ids: Vec<String>,
    pub attributes: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReceiptOcelProjection {
    pub object_ids: Vec<String>,
    pub events: Vec<OcelEvent>,
}

impl ReceiptOcelProjection {
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
            attributes.insert("standing_before".to_owned(), format!("{:?}", receipt.standing_before));
            attributes.insert("standing_after".to_owned(), format!("{:?}", receipt.standing_after));
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
                reason: "real service unavailable".into(),
            },
        }
    }

    #[test]
    fn irreversible_do_requires_independent_verifier() {
        let mut candidate = irreversible();
        candidate.independent_verifier = false;
        assert_eq!(candidate.validate(), Err(GovernanceRefusal::IrreversibleRequiresIndependentVerifier));
    }

    #[test]
    fn complete_irreversible_chain_admits() {
        assert_eq!(irreversible().validate(), Ok(()));
    }
}
