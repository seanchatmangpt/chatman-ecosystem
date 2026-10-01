# 81. Verified Daily Accomplishment Log

The daily accomplishment log is a measurement projection over admitted semantic evidence. It is not a narrative activity report and it does not infer accomplishment from Git volume, PR state, CI presence, or agent claims.

## 81.1 Plant target

The operational target is

\[
T = 250\ \text{verified unique semantic commits/hour}.
\]

For local hour \(h\), define

\[
V_h = \left|\{s : s\text{ is an exact Git subject with one unique semantic fingerprint and verified consequence in }h\}\right|.
\]

Progress is \(V_h/T\). The daily projection reports the peak hourly value, all observed hourly buckets, the daily verified total, and the number of hours at or above target.

## 81.2 Admission to the numerator

Ingress is versioned by `schemas/accomplishment-evidence.schema.json`; records with any other schema identity are refused before counting.

A semantic commit is countable only when the same record binds:

1. exact `owner/repo@sha` subject;
2. unique semantic fingerprint;
3. `COMPLETED` state;
4. non-empty consequence identity;
5. verified consequence;
6. repository-native verifier identity;
7. verifier outcome `PASS`;
8. receipt identity;
9. valid receipt digest.

Missing evidence does not reduce confidence by a percentage. It removes the item from the numerator.

## 81.3 Four required partitions

Every report separates:

- **Completed work** — countable exact-subject semantic commits only;
- **Receipts / evidence** — verifier and receipt bindings, including evidence that did not qualify;
- **Open gaps** — unverified, incomplete, or conflicting claims;
- **Blocked items** — typed blocked work, separately visible and never counted.

No work may disappear merely because it is unverified. It remains visible outside the target numerator.

## 81.4 Uniqueness

Both semantic and Git identity matter. Repeated observations of the same semantic fingerprint collapse to one unit. A fingerprint that names conflicting consequences is excluded. Multiple distinct fingerprints on one exact Git subject are excluded until reconciled, preventing one commit from being split into multiple plant credits.

## 81.5 User review boundary

The compiler emits `CANDIDATE` reports with `PENDING_USER_REVIEW`. Scheduled generation is therefore observation and projection, not approval. User review is a later boundary and must not be manufactured by CI.

## 81.6 Automation

`.github/workflows/daily-accomplishment-log.yml` runs after the Los Angeles day boundary, compiles `evidence/accomplishments/*.jsonl`, writes JSON and Markdown projections, publishes them as a workflow artifact, and places the Markdown projection in the run summary for review. The workflow has read-only repository permission and does not commit, merge, release, deploy, or mutate issues.

## 81.7 Falsifiers

This measurement system is invalid if any of the following can occur:

- an unverified consequence enters the target numerator;
- one exact Git subject is counted more than once;
- a conflicting semantic fingerprint is silently selected;
- a blocked item is counted as completed;
- a generated report claims user review automatically;
- the 250/hour target is computed from commits without exact consequence evidence.
