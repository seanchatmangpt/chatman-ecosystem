//! MuStar deterministic portfolio-level implementation selection.

use crate::CapabilityClass;
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MuStarCandidate {
    pub capability_id: String,
    pub capability_class: CapabilityClass,
    pub implementation_id: String,
    pub source_repository: String,
    pub observed: bool,
    pub build_verified: bool,
    pub positive_execution: bool,
    pub negative_refusal: bool,
    pub receipt_replay: bool,
    pub authority_fenced: bool,
    pub irreversible: bool,
    pub independent_verifier: bool,
    pub p95_latency_ns: u64,
    pub throughput_per_second: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MuStarCandidateRefusal {
    NotObserved,
    BuildUnverified,
    MissingPositiveExecution,
    MissingNegativeRefusal,
    MissingReceiptReplay,
    AuthorityNotFenced,
    IrreversibleWithoutIndependentVerifier,
    EmptyImplementationIdentity,
    EmptySourceRepository,
}

impl MuStarCandidate {
    #[must_use]
    pub fn refusals(&self) -> Vec<MuStarCandidateRefusal> {
        let mut out = Vec::new();
        if self.implementation_id.trim().is_empty() { out.push(MuStarCandidateRefusal::EmptyImplementationIdentity); }
        if self.source_repository.trim().is_empty() { out.push(MuStarCandidateRefusal::EmptySourceRepository); }
        if !self.observed { out.push(MuStarCandidateRefusal::NotObserved); }
        if !self.build_verified { out.push(MuStarCandidateRefusal::BuildUnverified); }
        if !self.positive_execution { out.push(MuStarCandidateRefusal::MissingPositiveExecution); }
        if !self.negative_refusal { out.push(MuStarCandidateRefusal::MissingNegativeRefusal); }
        if !self.receipt_replay { out.push(MuStarCandidateRefusal::MissingReceiptReplay); }
        if !self.authority_fenced { out.push(MuStarCandidateRefusal::AuthorityNotFenced); }
        if self.irreversible && !self.independent_verifier { out.push(MuStarCandidateRefusal::IrreversibleWithoutIndependentVerifier); }
        out
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MuStarRejectedCandidate {
    pub implementation_id: String,
    pub refusals: Vec<MuStarCandidateRefusal>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MuStarDecision {
    pub capability_id: String,
    pub capability_class: CapabilityClass,
    pub selected_implementation: String,
    pub selected_repository: String,
    pub rejected: Vec<MuStarRejectedCandidate>,
    pub selection_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MuStarRefusal {
    EmptyCandidateSet,
    EmptyCapabilityIdentity,
    MixedCapabilityIdentity,
    MixedCapabilityClass,
    NoAdmittedImplementation,
    Serialization(String),
}

#[derive(Serialize)]
struct DecisionDigestInput<'a> {
    capability_id: &'a str,
    capability_class: CapabilityClass,
    selected_implementation: &'a str,
    selected_repository: &'a str,
    rejected: &'a [MuStarRejectedCandidate],
}

pub fn select(candidates: &[MuStarCandidate]) -> Result<MuStarDecision, MuStarRefusal> {
    let first = candidates.first().ok_or(MuStarRefusal::EmptyCandidateSet)?;
    if first.capability_id.trim().is_empty() { return Err(MuStarRefusal::EmptyCapabilityIdentity); }
    if candidates.iter().any(|x| x.capability_id != first.capability_id) { return Err(MuStarRefusal::MixedCapabilityIdentity); }
    if candidates.iter().any(|x| x.capability_class != first.capability_class) { return Err(MuStarRefusal::MixedCapabilityClass); }

    let mut admitted = Vec::new();
    let mut rejected = Vec::new();
    for candidate in candidates {
        let refusals = candidate.refusals();
        if refusals.is_empty() { admitted.push(candidate); } else {
            rejected.push(MuStarRejectedCandidate { implementation_id: candidate.implementation_id.clone(), refusals });
        }
    }
    admitted.sort_by(|left, right| compare_admitted(left, right));
    let selected = admitted.first().copied().ok_or(MuStarRefusal::NoAdmittedImplementation)?;
    rejected.sort_by(|a, b| a.implementation_id.cmp(&b.implementation_id));
    let input = DecisionDigestInput {
        capability_id: &first.capability_id,
        capability_class: first.capability_class,
        selected_implementation: &selected.implementation_id,
        selected_repository: &selected.source_repository,
        rejected: &rejected,
    };
    let bytes = serde_json::to_vec(&input).map_err(|e| MuStarRefusal::Serialization(e.to_string()))?;
    Ok(MuStarDecision {
        capability_id: first.capability_id.clone(),
        capability_class: first.capability_class,
        selected_implementation: selected.implementation_id.clone(),
        selected_repository: selected.source_repository.clone(),
        rejected,
        selection_digest: format!("blake3:{}", blake3::hash(&bytes).to_hex()),
    })
}

fn compare_admitted(left: &MuStarCandidate, right: &MuStarCandidate) -> Ordering {
    left.p95_latency_ns.cmp(&right.p95_latency_ns)
        .then_with(|| right.throughput_per_second.cmp(&left.throughput_per_second))
        .then_with(|| left.implementation_id.cmp(&right.implementation_id))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn candidate(id: &str, latency: u64, throughput: u64) -> MuStarCandidate {
        MuStarCandidate {
            capability_id: "capability:catalog-projection".into(), capability_class: CapabilityClass::Construct,
            implementation_id: id.into(), source_repository: "ggen".into(), observed: true,
            build_verified: true, positive_execution: true, negative_refusal: true, receipt_replay: true,
            authority_fenced: true, irreversible: false, independent_verifier: false,
            p95_latency_ns: latency, throughput_per_second: throughput,
        }
    }

    #[test]
    fn proof_incomplete_fast_candidate_cannot_win() {
        let mut unsafe_fast = candidate("unsafe-fast", 1, 1_000_000);
        unsafe_fast.negative_refusal = false;
        let decision = select(&[unsafe_fast, candidate("safe", 100, 100)]);
        assert!(matches!(decision, Ok(MuStarDecision { selected_implementation, .. }) if selected_implementation == "safe"));
    }

    #[test]
    fn irreversible_without_verifier_is_refused() {
        let mut item = candidate("irreversible", 10, 10);
        item.irreversible = true;
        assert_eq!(select(&[item]), Err(MuStarRefusal::NoAdmittedImplementation));
    }
}
