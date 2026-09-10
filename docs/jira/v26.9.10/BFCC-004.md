# BFCC-004 — BFCC Ephemeralization Benchmark

Ticket Key: BFCC-004
Owning repo: seanchatmangpt/chatman-ecosystem
Exact base ref/SHA: main @ 83204ee38a518311d9c9fc128d69c517a99257f4
Standing: BFCC-CANDIDATE
Depends on: BFCC-003

## Problem

BFCC-E (ephemeralization) and BFCC-T (trimtab leverage) are longitudinal claims —
"capability per resource increases over time" — that a single point-in-time verifier
cannot check. No existing script in this repo tracks a metric across repeated
receipts over time (confirmed by exploration: `grep -ril benchmark scripts/ docs/
catalog/` finds only unrelated prose, no metric-over-time tracker to reuse).

## Customer/system need

Anyone claiming "this system is getting more BFCC-compatible over time" needs a real
computation, not an assertion — per BFCC-S (Science), a longitudinal claim needs an
observable trend, and per BFCC's own "never round up" rule, insufficient data must
report `INSUFFICIENT_DATA`, never a false `IMPROVING`.

## Scope

`scripts/bfcc_benchmark.py`:

- Input: a JSONL ledger of past BFCC receipts, `--receipts <path>` (default
  `.artifacts/bfcc/receipts.jsonl`). Each line is a receipt dict carrying `subject`,
  `problem_class`, `resource_vector` (dict of the six resource dimensions from the
  doctrine: `human_reasoning`, `model_tokens`, `novel_code`, `compute`, `time`,
  `dependencies`), and `verified_capability_delta` (a number the receipt's own
  `evidence_per_gate`/`eta_evidence` fields must justify — this benchmark aggregates
  what verified receipts already declared, it does not compute capability itself).
- For each `problem_class` with ≥2 receipts: compute η per receipt
  (`verified_capability_delta / sum(resource_vector.values())`), fit a least-squares
  linear trend (pure Python, no external dependency), and classify `direction` as one
  of exactly four values — `IMPROVING` (slope > 0), `DEGRADING` (slope < 0), `FLAT`
  (|slope| below a stated epsilon), `INSUFFICIENT_DATA` (<2 points). Never a silent
  fifth state, never omitted from the report.
- Same computation for λ (trimtab leverage) using `canonical_information_delta` when
  present in receipts.
- `main()`: same `--json`/exit-code convention as BFCC-003.

`tests/test_bfcc_benchmark.py`:

- Real, on-disk JSONL fixture files written to a tempdir per test (actual file I/O,
  not mocked reads) covering `IMPROVING`/`DEGRADING`/`FLAT`/`INSUFFICIENT_DATA`, each
  with a hand-computed expected slope the test asserts against exactly.

## Non-goals

- No automatic receipt generation or capability-delta measurement — this benchmark
  only aggregates pre-existing, independently-verified receipts.
- No claim this repo currently has any real receipts to benchmark — the ledger starts
  empty; this ticket only builds the aggregator.

## Dependencies

BFCC-003 (the receipt shape this benchmark's input rows must match).

## Risks

A benchmark with too few real data points will report `INSUFFICIENT_DATA` for a long
time — this is the correct, honest behavior per BFCC-S, not a defect to work around by
loosening the ≥2-point threshold.

## Authority boundary

`OBSERVE` only — a pure aggregation/reporting tool, no DO action, no mutation of any
receipt it reads.

## Rollback

Delete `scripts/bfcc_benchmark.py` and `tests/test_bfcc_benchmark.py`; the receipts
ledger path (`.artifacts/bfcc/receipts.jsonl`) is not written by any other script yet.

## Acceptance commands

```
python3 -m unittest discover -s tests -p test_bfcc_benchmark.py -v
python3 scripts/bfcc_benchmark.py --receipts /dev/null --json
```

## Observable Definition of Done

- `python3 -m unittest discover -s tests -p test_bfcc_benchmark.py -v` — all green,
  covering all four `direction` states with hand-verified expected slopes.
- Running against an empty or missing ledger reports `INSUFFICIENT_DATA` for every
  problem class, never a crash and never a false trend.
- `grep -rn "unittest.mock\|Mock(\|MagicMock\|patch(\|monkeypatch"
  tests/test_bfcc_benchmark.py` returns zero matches.
