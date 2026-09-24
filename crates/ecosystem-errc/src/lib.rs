//! ERRC production innovations for the Chatman Ecosystem.
//!
//! The crate is deliberately non-actuating. It provides governed capability
//! validation, MuStar SELECT, receipt→OCEL projection, and evidence-bounded SLA
//! aggregation. Authority and DO remain in their existing owners.

pub mod governance;
pub mod mustar;
pub mod sla;

pub use governance::{
    CapabilityClass, CapabilityGovernance, ExternalServiceStanding, GovernanceRefusal,
    OcelEvent, ReceiptOcelProjection,
};
pub use mustar::{
    select as mustar_select, MuStarCandidate, MuStarCandidateRefusal, MuStarDecision,
    MuStarRefusal, MuStarRejectedCandidate,
};
pub use sla::{
    aggregate as aggregate_benchmarks, BenchmarkDisposition, BenchmarkRefusal,
    BenchmarkReport, BenchmarkSample,
};
