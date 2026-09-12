//! MuStar: deterministic portfolio-level implementation selection.
//!
//! MuStar selects one canonical implementation for one semantic capability from
//! evidence-bounded candidates. It is SELECT only: it never grants authority,
//! constructs an external artifact, or performs DO.

use crate::errc::CapabilityClass;
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;

/// Evidence required before an implementation may enter MuStar's choice set.
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

/// Why a candidate is excluded from canonical implementation selection.
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
    /// Return all falsifiers preventing this implementation from being selected.
    #[must_use]
    pub fn refusals(&self) -> Vec<MuStarCandidateRefusal> {
        let mut refusals = Vec::new();
        if self.implementation_id.trim().is_empty() {
            refusals.push(MuStarCandidateRefusal::EmptyImplementationIdentity);
        }
        if self.source_repository.trim().is_empty() {
            refusals.push(MuStarCandidateRefusal::EmptySourceRepository);
        }
        if !self.observed {
            refusals.push(MuStarCandidateRefusal::NotObserved);
        }
        if !self.build_verified {
            refusals.push(MuStarCandidateRefusal::BuildUnverified);
        }
        if !self.positive_execution {
            refusals.push(MuStarCandidateRefusal::MissingPositiveExecution);
        }
        if !self.negative_refusal {
            refusals.push(MuStarCandidateRefusal::MissingNegativeRefusal);
        }
        if !self.receipt_replay {
            refusals.push(MuStarCandidateRefusal::MissingReceiptReplay);
        }
        if !self.authority_fenced {
            refusals.push(MuStarCandidateRefusal::AuthorityNotFenced);
        }
        if self.irreversible && !self.independent_verifier {
            refusals.push(MuStarCandidateRefusal::IrreversibleWithoutIndependentVerifier);
        }
        refusals
    }
}

/// One excluded implementation and its exact refusal set.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MuStarRejectedCandidate {
    pub implementation_id: String,
    pub refusals: Vec<MuStarCandidateRefusal>,
}

/// Evidence-bounded selection result. The digest binds the choice and refusals;
/// it is not an execution receipt.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MuStarDecision {
    pub capability_id: String,
    pub capability_class: CapabilityClass,
    pub selected_implementation: String,
    pub selected_repository: String,
    pub rejected: Vec<MuStarRejectedCandidate>,
    pub selection_digest: String,
}

/// Refusal of the MuStar selection operation itself.
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

/// Select the canonical implementation for one capability.
///
/// Admissibility is hard-gated first. Among surviving candidates, MuStar chooses
/// lower p95 latency, then higher measured throughput, then lexical implementation
/// identity as a deterministic tie-breaker. Performance never compensates for a
/// missing proof surface or authority fence.
pub fn select(candidates: &[MuStarCandidate]) -> Result<MuStarDecision, MuStarRefusal> {
    let first = candidates.first().ok_or(MuStarRefusal::EmptyCandidateSet)?;
    if first.capability_id.trim().is_empty() {
        return Err(MuStarRefusal::EmptyCapabilityIdentity);
    }
    if candidates
        .iter()
        .any(|candidate| candidate.capability_id != first.capability_id)
    {
        return Err(MuStarRefusal::MixedCapabilityIdentity);
    }
    if candidates
        .iter()
        .any(|candidate| candidate.capability_class != first.capability_class)
    {
        return Err(MuStarRefusal::MixedCapabilityClass);
    }

    let mut admitted = Vec::new();
    let mut rejected = Vec::new();
    for candidate in candidates {
        let refusals = candidate.refusals();
        if refusals.is_empty() {
            admitted.push(candidate);
        } else {
            rejected.push(MuStarRejectedCandidate {
                implementation_id: candidate.implementation_id.clone(),
                refusals,
            });
        }
    }
    admitted.sort_by(|left, right| compare_admitted(left, right));
    let selected = admitted
        .first()
        .copied()
        .ok_or(MuStarRefusal::NoAdmittedImplementation)?;
    rejected.sort_by(|left, right| left.implementation_id.cmp(&right.implementation_id));

    let digest_input = DecisionDigestInput {
        capability_id: &first.capability_id,
        capability_class: first.capability_class,
        selected_implementation: &selected.implementation_id,
        selected_repository: &selected.source_repository,
        rejected: &rejected,
    };
    let bytes = serde_json::to_vec(&digest_input)
        .map_err(|error| MuStarRefusal::Serialization(error.to_string()))?;
    let selection_digest = format!("blake3:{}", blake3::hash(&bytes).to_hex());

    Ok(MuStarDecision {
        capability_id: first.capability_id.clone(),
        capability_class: first.capability_class,
        selected_implementation: selected.implementation_id.clone(),
        selected_repository: selected.source_repository.clone(),
        rejected,
        selection_digest,
    })
}

fn compare_admitted(left: &MuStarCandidate, right: &MuStarCandidate) -> Ordering {
    left.p95_latency_ns
        .cmp(&right.p95_latency_ns)
        .then_with(|| right.throughput_per_second.cmp(&left.throughput_per_second))
        .then_with(|| left.implementation_id.cmp(&right.implementation_id))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn candidate(id: &str, latency: u64, throughput: u64) -> MuStarCandidate {
        MuStarCandidate {
            capability_id: "capability:catalog-projection".into(),
            capability_class: CapabilityClass::Construct,
            implementation_id: id.into(),
            source_repository: "ggen".into(),
            observed: true,
            build_verified: true,
            positive_execution: true,
            negative_refusal: true,
            receipt_replay: true,
            authority_fenced: true,
            irreversible: false,
            independent_verifier: false,
            p95_latency_ns: latency,
            throughput_per_second: throughput,
        }
    }

    #[test]
    fn proof_incomplete_fast_candidate_cannot_win() {
        let mut unsafe_fast = candidate("unsafe-fast", 1, 1_000_000);
        unsafe_fast.negative_refusal = false;
        let safe = candidate("safe", 100, 100);
        let decision = select(&[unsafe_fast, safe]);
        match decision {
            Ok(decision) => {
                assert_eq!(decision.selected_implementation, "safe");
                assert_eq!(decision.rejected.len(), 1);
            }
            Err(error) => panic!("unexpected selection refusal: {error:?}"),
        }
    }

    #[test]
    fn lower_latency_breaks_tie_after_hard_admission() {
        let slower = candidate("slower", 20, 10_000);
        let faster = candidate("faster", 10, 9_000);
        let decision = select(&[slower, faster]);
        match decision {
            Ok(decision) => assert_eq!(decision.selected_implementation, "faster"),
            Err(error) => panic!("unexpected selection refusal: {error:?}"),
        }
    }

    #[test]
    fn irreversible_candidate_requires_independent_verifier() {
        let mut irreversible = candidate("irreversible", 10, 10);
        irreversible.irreversible = true;
        let result = select(&[irreversible]);
        assert_eq!(result, Err(MuStarRefusal::NoAdmittedImplementation));
    }
}
