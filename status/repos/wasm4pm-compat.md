# wasm4pm-compat — Ecosystem Status Report

> **Generated projection.** This file's facts (ref, SHA, standing, receipts) are rendered from `status/snapshot.json`, the single machine-generated source of truth. Do not hand-edit facts here; regenerate from `status/snapshot.json` instead (AGENTS.md rule 6: generated files are projections, not canonical sources).


> **Observed:** `2026-08-16T02:32:03.164547+00:00`  
> **Repository:** `seanchatmangpt/wasm4pm-compat`  
> **Constitutional role:** `process-type-law`  
> **Current evidence standing:** `PARTIAL_ALIVE`

## Executive status

| Field | Observation |
|---|---|
| Required | `true` |
| Disposition | `REQUIRED` |
| Configured ref | `main` |
| Current SHA | `577e2d1d8bdfe27d96f61c63f3ea120994e8bfda` |
| Prior manifest SHA | `577e2d1d8bdfe27d96f61c63f3ea120994e8bfda` |
| Prior manifest standing | `UNKNOWN` |
| Prior execution receipt | `none` |
| Default branch | `main` |
| Latest commit | `Merge PR #22: DFCM-complete connectors and executable DoD` |
| Latest commit date | `2026-08-14T06:27:20Z` |
| Repository pushed_at | `2026-08-14T06:27:20Z` |
| Open PRs observed | `0` |
| GitHub open issues+PRs counter | `0` |
| Dependencies | `none` |

## Standing derivation

- Exact-head CI success is observed, but generic CI is not automatically a semantic execution receipt.

The report applies the ecosystem law: `Architecture != Execution`. A repository existing, a branch resolving, or generic CI passing does not by itself establish the role-specific `ALIVE` consequence. Exact-subject execution and a replayable receipt are the crown evidence.

## Current execution evidence

- Workflow: **Build Matrix**
- Run ID: `31776342582`
- Status: `completed`
- Conclusion: `success`
- Head SHA: `577e2d1d8bdfe27d96f61c63f3ea120994e8bfda`
- Event: `push`
- Updated: `2026-08-14T06:30:22Z`

## Open pull requests

- None observed.

## Next standing-changing receipt

Execute the narrowest exact-head semantic boundary required for this role and capture a replayable receipt.

## Constitutional path

```mermaid
flowchart LR
    R["wasm4pm-compat<br/>process-type-law"] --> O["Observed ref / SHA"]
    O --> A{"Exact role execution receipt?"}
    A -->|No| P["UNKNOWN / PARTIAL / BLOCKED / BUILD_BROKEN"]
    A -->|Yes| X["Replay exact subject"]
    X -->|PASS| L["ALIVE"]
    X -->|FAIL| B["BUILD_BROKEN"]
```

## Evidence boundary

This file is an observation report for `seanchatmangpt/wasm4pm-compat@main`. It is not an actuation receipt and cannot itself promote the component. The strongest standing shown above is derived only from exact repository/ref identity, the previous admitted fleet manifest when its subject still matches, and current GitHub execution metadata.

