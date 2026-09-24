# Orthogonal Swarm Results (v26.9.23)

This is the synthesis of the swarm the operator launched at 14:20 PT (wf_2755fdff-28e).
It covers the CI pre-flight of both release subjects and the CE23-0 bootstrap. The
machine-readable form is `swarm-results.json`; the repair wave spec is `wave-R2.json` (not
launched). Gates, candidates and witness logs are in `r2/`.

## Wave R2: pre-freeze CI repair (7 lanes)

| lane | repo | defect_key | class | scan-plan id |
|---|---|---|---|---|
| R2-X-HOSTSKIP | xaas | xaas-ci-host-coupled-courts | subject defect | none (conditional) |
| R2-X-WDCS2 | xaas | xaas-wd-cs2-assets-origin | pre-existing | R2-X-WDCS2 |
| R2-X-PROD-TIMEOUT | xaas | xaas-ci-production-timeout | pre-existing | R2-X-PROD-TIMEOUT |
| R2-X-IMAGE-CARGO | xaas | xaas-image-rust-toolchain | pre-existing | R2-X-IMAGE-CARGO |
| R2-GI-CI | ggen_igniter | ggen_igniter-ci-fetch-depth+timeout | subject defect | R2-GI-CI |
| R2-GI-PROBE-ISOLATION | ggen_igniter | ggen_igniter-test-orphan-dev-beam | subject defect | none |
| R2-GI-BLOOM | ggen_igniter | ggen_igniter-test-bloom-commit-graph | subject defect | none |

- R2-X-IMAGE-CARGO waits on R2-X-PROD-TIMEOUT. The other six lanes have no dependencies.
- R2-X-HOSTSKIP is conditional. The R1c lane R1-X-PIN already carries its candidate as `3ea1cfc`.
  If that commit merges, the lane stops at its coverage check without producing a diff.
- Dropped as covered:
  - R2-X-DIALYZER: R1-X-PIN `60972f8` fixes all three warnings.
  - the r_projection guard: also in R1-X-PIN.
  - the format step: R1-GI-FMT.
  - the NIF cache failure on main: already fixed on the release branch.
- R2-GI-CACHESEED is an infrastructure accelerator, not a failure fix. It is listed with the
  environment items and is ready if the operator admits it.
- The timeout part of R2-GI-CI is reclassified from infrastructure to subject defect:
  - the budget lives in the subject;
  - main fit inside it (29m48s);
  - the subject's own growth in tests exceeded it (5 of 5 push runs cancelled at 30m0s).
- Every gate was witnessed in scratch: the base fails, the candidate passes, and mutants fail
  (`r2/witness/`). The exception is r2-gi-depth.sh, which cites the swarm's own witness.

## Gate conflicts with scan-plan R2 (the driver reconciles by defect_key)

- **PROD-TIMEOUT:** the scan gate requires exactly 30 minutes. Measured jobs ran 18m30s and 21m31s,
  so the 1.5x rule requires at least 33.
- **IMAGE-CARGO:** the scan gate requires image-check at exactly 45 minutes, which also meets this
  gate's minimum of 36. The swarm candidate uses 60 and an unverified `curl | sh`, so it fails both
  gates. Use 45 and an integrity-pinned Rust 1.97.x.
- **WDCS2:** the scan gate's websocket probe (Origin 127.0.0.1) accepts only the
  `check_origin: false` variant. The hosted-green swarm variant switches to localhost.
  This gate accepts either.
- **R2-X-TOOLCHAIN** (scan-only): R1-X-PIN already changed `courts/gi_mix.sh`. Narrow the lane to
  `bootstrap_court.sh` and the cargo-on-PATH refusal.

## Driver steps after R2, before REL-A3

1. Push `friday/gc-fri-0800` in both repos (fast-forward only).
2. ggen_igniter: the push run at the exact int head must be green. The only whole-suite green so far
   is 35938454860 at 794cb2a.
3. xaas: after the FENCE YAML proof, dispatch `ci_cd.yaml` and `wd-cs2-exact-head.yml` at the int
   head. Every job must pass; only publish-image and deploy may be skipped.

## CE23

- **CE23-0 is ALIVE,** scoped to CE23-0 alone.
  - Int branch `release/v26.9.23-int` is at a896e16c. GitHub main (c59596f5) is unchanged.
  - Court limit 1: the validator checks structure only. A forged lineage block was admitted, so the
    lineage standing rests on the replayed commands.
  - Court limit 2: replay #17 cannot reproduce after sealing.
- **CE0 wave:**
  - CE-INTAKE is PARTIAL_ALIVE (`96fb0bfb`). The cause is the driver-owned gate string, which is
    missing `--namespace ... --prefix ce`; `compile_check.sh` is the equivalent correct gate.
  - CE-LANEPLAN is blocked on CE-INTAKE.
  - The CE-INTAKE-C gate in scan-plan CE0b assumes a different layout (NAMESPACE file, `units/<u>/`
    directories, `--prefix ce23`).

## Open

- Whether R1-X-PIN keeps `3ea1cfc`.
- The duration of a WD CS2 run with a cold cache.
- Whether ggen_igniter has order-dependent tests other than the one PROBE-ISOLATION fixes (only one
  green seed so far).
- No hosted run yet covers the R1-X-PIN changes.
