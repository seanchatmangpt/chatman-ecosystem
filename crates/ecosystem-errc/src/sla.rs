//! Evidence-bounded benchmark/SLA aggregation.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub enum BenchmarkDisposition {
    Executed,
    Refused { code: String },
    NamedSkip { reason: String },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkSample {
    pub latency_ns: u64,
    pub operations: u64,
    pub elapsed_ns: u64,
    pub disposition: BenchmarkDisposition,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkReport {
    pub sample_count: usize,
    pub executed_count: usize,
    pub refused_count: usize,
    pub named_skip_count: usize,
    pub measured_operations: u128,
    pub measured_elapsed_ns: u128,
    pub throughput_per_second: u128,
    pub p50_latency_ns: u64,
    pub p95_latency_ns: u64,
    pub p99_latency_ns: u64,
    pub refusal_codes: BTreeMap<String, usize>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BenchmarkRefusal {
    NoSamples,
    NoExecutedSamples,
    ZeroExecutedElapsed,
    ExecutedSampleHasZeroOperations,
    RefusalCodeEmpty,
    NamedSkipReasonEmpty,
}

pub fn aggregate(samples: &[BenchmarkSample]) -> Result<BenchmarkReport, BenchmarkRefusal> {
    if samples.is_empty() { return Err(BenchmarkRefusal::NoSamples); }
    let mut latencies = Vec::new();
    let mut operations = 0_u128;
    let mut elapsed = 0_u128;
    let mut executed_count = 0_usize;
    let mut refused_count = 0_usize;
    let mut named_skip_count = 0_usize;
    let mut refusal_codes = BTreeMap::new();

    for sample in samples {
        match &sample.disposition {
            BenchmarkDisposition::Executed => {
                if sample.operations == 0 { return Err(BenchmarkRefusal::ExecutedSampleHasZeroOperations); }
                executed_count += 1;
                latencies.push(sample.latency_ns);
                operations += u128::from(sample.operations);
                elapsed += u128::from(sample.elapsed_ns);
            }
            BenchmarkDisposition::Refused { code } => {
                if code.trim().is_empty() { return Err(BenchmarkRefusal::RefusalCodeEmpty); }
                refused_count += 1;
                *refusal_codes.entry(code.clone()).or_insert(0) += 1;
            }
            BenchmarkDisposition::NamedSkip { reason } => {
                if reason.trim().is_empty() { return Err(BenchmarkRefusal::NamedSkipReasonEmpty); }
                named_skip_count += 1;
            }
        }
    }
    if executed_count == 0 { return Err(BenchmarkRefusal::NoExecutedSamples); }
    if elapsed == 0 { return Err(BenchmarkRefusal::ZeroExecutedElapsed); }
    latencies.sort_unstable();
    Ok(BenchmarkReport {
        sample_count: samples.len(), executed_count, refused_count, named_skip_count,
        measured_operations: operations, measured_elapsed_ns: elapsed,
        throughput_per_second: operations.saturating_mul(1_000_000_000) / elapsed,
        p50_latency_ns: percentile(&latencies, 50),
        p95_latency_ns: percentile(&latencies, 95),
        p99_latency_ns: percentile(&latencies, 99),
        refusal_codes,
    })
}

fn percentile(sorted: &[u64], percent: usize) -> u64 {
    let last = sorted.len().saturating_sub(1);
    let index = last.saturating_mul(percent).saturating_add(99) / 100;
    sorted[index.min(last)]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn named_skip_cannot_manufacture_throughput() {
        let sample = BenchmarkSample { latency_ns: 0, operations: 0, elapsed_ns: 0,
            disposition: BenchmarkDisposition::NamedSkip { reason: "real server unavailable".into() } };
        assert_eq!(aggregate(&[sample]), Err(BenchmarkRefusal::NoExecutedSamples));
    }

    #[test]
    fn execution_and_refusal_share_one_report() {
        let samples = [
            BenchmarkSample { latency_ns: 100, operations: 10, elapsed_ns: 1_000, disposition: BenchmarkDisposition::Executed },
            BenchmarkSample { latency_ns: 0, operations: 0, elapsed_ns: 0, disposition: BenchmarkDisposition::Refused { code: "AUTHORITY_REFUSED".into() } },
        ];
        assert!(matches!(aggregate(&samples), Ok(BenchmarkReport { executed_count: 1, refused_count: 1, .. })));
    }
}
