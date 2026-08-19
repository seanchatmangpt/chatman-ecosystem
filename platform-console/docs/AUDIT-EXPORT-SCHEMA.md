# Audit Log Export API — Schema v1

Last updated: 2026-08-19

This document is the field-by-field stability contract for `GET /api/v1/audit-export` — the
external-facing, cursor-paginated endpoint a customer's SIEM forwarder (Splunk, Datadog,
Microsoft Sentinel, or any other scheduled poller) is meant to build a connector against. It
is distinct from `GET /api/audit` (the internal, session-cookie-gated admin-UI query surface
behind the `/audit` page) and from `GET /api/audit/export` (the bulk ECS/NDJSON one-shot dump
described in `lib/audit-export.ts`) — this is the one endpoint in this console meant to be
polled unattended, forever, on a schedule, by a system with no human session behind it.

## Endpoint

```
GET /api/v1/audit-export?since=<cursor>&limit=<n>
Authorization: Bearer aet_live_...
```

| Query param | Required | Default | Max | Meaning |
|---|---|---|---|---|
| `since` | No | none (returns from the oldest row) | — | Opaque pagination cursor. Either a value this endpoint previously returned as `next_cursor`, or a bare RFC3339 timestamp (for a forwarder's very first poll, with no prior cursor in hand). |
| `limit` | No | `500` | `2000` | Maximum number of events returned in this page. |

## Authentication

A dedicated, narrowly-scoped bearer credential — an **audit export token** — distinct from
both the browser session cookie (`lib/session.ts`) and the general-purpose `pk_live_...` API
key (`lib/api-keys.ts`). This is a deliberate design choice, not an oversight: a SIEM
forwarder needs a credential that can be handed to an unattended system and revoked
independently of any human's session or general API access, scoped to nothing more than
reading the audit trail.

- **Format**: `Authorization: Bearer aet_live_<random>` — prefix `aet_live_` distinguishes
  this credential class from `pk_live_` at a glance in any log line that leaks a prefix.
- **Scope**: fixed at mint time to the single literal string `"audit:read"`. There is no
  broader scope to request today.
- **Storage**: SHA-256 hash only, in `platform_console.audit_export_tokens` (org id, token
  hash, prefix, scope, `createdBy`, `createdAt`, `revokedAt`) — the plaintext token is shown
  exactly once, in the mint response, and is never persisted or retrievable again.
- **Issuance**: `POST /api/orgs/{id}/audit-export-tokens`, owner-role-gated on that org (same
  per-org `requireRoleIn(..., "owner")` boundary `PUT /api/orgs/[id]/branding` already uses).
  `GET` lists a org's tokens (hashes never included); `DELETE ?id=<n>` revokes one.
- **Failure mode**: a missing, malformed, unknown, or revoked token returns `401
  {"error":"unauthenticated", "reason": "..."}`. There is no fallback to session-cookie auth
  on this route — it is public at the middleware layer specifically so it can be reached
  without one, and authenticates entirely on its own bearer token.

## Response shape — `schema_version: "1"`

```json
{
  "schema_version": "1",
  "events": [
    {
      "id": 4821,
      "requestId": "b1e2...",
      "ts": "2026-08-19T14:03:11.482Z",
      "actor": "admin",
      "method": "GET",
      "path": "/api/audit",
      "status": 200,
      "insertedAt": "2026-08-19T14:03:11.502Z",
      "castleReceiptDigest": "sha256:...",
      "impersonatedBy": "support@example.com",
      "impersonationSessionId": "a93f..."
    }
  ],
  "next_cursor": "2026-08-19T14:03:11.482Z|4821",
  "chain_verified": true
}
```

### Top-level fields

| Field | Type | Stability guarantee |
|---|---|---|
| `schema_version` | `"1"` (literal string, never a number) | Frozen. This exact value never changes meaning. A breaking change to this contract ships as a new literal (`"2"`) with its own, separately documented response shape — `"1"` itself is never mutated. |
| `events` | `AuditLogRow[]` (see below), oldest first | Additive-only: new optional fields may be added to a row in a future release; no field present in v1 is ever removed or repurposed while `schema_version` remains `"1"`. |
| `next_cursor` | `string \| null` | `null` exactly when this page returned zero events (nothing further to page through *yet* — poll again later with the same `since`, not a terminal state). Otherwise an opaque string; treat it as a black box and pass it back verbatim as `since` on the next call. Its current internal encoding (`"<ts>|<id>"`) is not part of the stability contract and may change — only its round-trip behavior (`next_cursor` in, `since` out, resumes correctly) is guaranteed. |
| `chain_verified` | `boolean` | Whether `lib/audit-db.ts`'s `verifyAuditChain()` — a full, live re-derivation of the append-only hash chain over `platform_console.audit_log` — found the chain intact **at the moment this request was served**. `false` means either a broken link was detected or the chain could not be verified (e.g. the audit database was unreachable for the verification pass specifically); either way, a `false` value here is a signal worth an operator's attention independent of whether `events` still returned successfully. |

### `events[]` — one `AuditLogRow` per entry (`lib/audit-db.ts`'s `AuditLogRow`)

| Field | Type | Always present? | Meaning |
|---|---|---|---|
| `id` | `number` | Yes | Monotonically increasing row id (`bigserial`) — the second half of the pagination cursor, never reused. |
| `requestId` | `string` | Yes | The request's own UUID, shared across every audit line and log entry the same request produced. |
| `ts` | `string` (RFC3339) | Yes | When the audited event occurred. Ascending-ordered within a page; the primary half of the pagination cursor. |
| `actor` | `string` | Yes | The authenticated identity that performed the action — a session subject, a `pk_live_` API key's bound identifier, or (for the export endpoint's own audit line) the literal `audit-export-token:<orgId>` string. |
| `method` | `string` | Yes | HTTP method of the audited request. |
| `path` | `string` | Yes | HTTP path of the audited request. |
| `status` | `number` | Yes | HTTP status code the audited request resolved to. |
| `insertedAt` | `string` (RFC3339) | Yes | When this row was durably written — distinct from `ts` (the event's own timestamp) only in the presence of a write-path delay; normally equal or a few milliseconds later. |
| `castleReceiptDigest` | `string` | No | Present only on rows produced by a castle GymAct run; a receipt digest cryptographically committed into this row's own position in the hash chain. |
| `impersonatedBy` | `string` | No | Present only when this action was taken during an active support-impersonation session; the admin identity that actually acted. |
| `impersonationSessionId` | `string` | No | Present only alongside `impersonatedBy`; the impersonation session's own id, for cross-referencing `GET /api/orgs/{id}/impersonation-log`. |

Optional fields follow the exact same "absent, not `null`" convention as the rest of this
codebase's JSON-in-Postgres/ConfigMap records — a consumer should check for key presence, not
assume `null` for an unset optional field.

## Versioning policy

- `schema_version: "1"` is frozen as documented above. Every field's presence, type, and
  meaning in this document is a commitment a SIEM connector may build against and expect to
  keep working indefinitely.
- A genuinely breaking change (a field removed, a type changed, a meaning redefined) ships
  under a new `schema_version` literal, returned only from a request that opts into it (the
  concrete opt-in mechanism — a query param, a header, or a separate path — is not yet
  defined, since no `"2"` exists yet; this section exists so a future breaking change has
  nowhere to hide it other than a new, distinct version).
- Adding a new optional field to `events[]`, or a new top-level response field, is **not** a
  breaking change and does not bump `schema_version` — a forwarder that ignores unknown keys
  (the correct, forward-compatible way to consume any versioned JSON contract) is unaffected.

## Disclosed scope note

`platform_console.audit_log` has no `orgId`/tenant column today — this console's audit trail
is process-wide, not yet partitioned per customer org (see `docs/SCOPE-AND-LIMITATIONS.md` for
the same single-tenant-today framing applied elsewhere in this repo). An audit export token is
issued **per org** (an owner of org A mints and can revoke their own token, independently of
org B's), and every export call is itself logged with that token's bound `orgId` in the
`actor` field for full attribution — but `events` returned by a given token today reflects the
whole console's audit trail, not a filtered, org-scoped subset. Scoping `events` itself to one
org is the natural next step once `audit_log` carries an org column; this document will be
updated (still under `schema_version: "1"`, since narrowing what rows are already-documented
fields describe — not changing the fields themselves — is not a breaking change) when that
lands.

## Self-auditing

Every call to `GET /api/v1/audit-export` — success or failure — is itself written to
`platform_console.audit_log` via `writeAuditLogEntry`, with `path: "/api/v1/audit-export"` and
`actor: "audit-export-token:<orgId>"`. Export activity against the audit trail is itself part
of the audit trail; a security team auditing who pulled audit data, and when, can do so through
the very same `/audit` page and `verifyAuditChain()` control that cover every other action in
this console.

## See also

- `docs/SOC2-CONTROL-MAPPING.md` — where audit-log durability and tamper-evidence controls are
  cataloged.
- `lib/audit-db.ts` — `AuditLogRow`, `queryAuditLogSince`, `verifyAuditChain`,
  `createAuditExportToken`/`resolveAuditExportToken`/`revokeAuditExportToken`.
- `lib/audit-export.ts` — the separate bulk ECS/NDJSON one-shot export (`/api/audit/export`),
  for a full historical dump rather than a scheduled incremental poll.
