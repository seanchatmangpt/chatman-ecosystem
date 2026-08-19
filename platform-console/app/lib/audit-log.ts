/**
 * The real, mechanical "access is logged" control: one JSON line per
 * authenticated request, written to stdout via console.log, in a fixed
 * schema. This is a log line, not a compliance claim -- see app/compliance
 * for the honest framing of what evidence this actually constitutes.
 */
export interface AuditLogEntry {
  timestamp: string; // RFC3339
  actor: string; // session subject (username), or "anonymous"
  method: string;
  path: string;
  status: number;
  requestId: string;
  /**
   * Cross-reference to castle's own independent chain: the BLAKE3
   * `receipt_digest` (castle.rs's `Receipt.receipt_digest`, castle.rs:513-522)
   * of a `ReceiptedOcelLog` (castle.rs:683-687) produced by a GymAct-invoking
   * castle run, when one was found in that run's Job output. Optional and
   * absent for every non-GymAct verb (today, every verb in
   * `ALLOWED_CASTLE_VERBS` -- see lib/castle.ts) and for every non-castle
   * audit entry. Recording this field never merges the two chains: castle's
   * BLAKE3 receipt chain and this table's own sha256 row-hash chain remain
   * independently verifiable end to end; this field only lets a reviewer
   * walk from one to the other.
   */
  castleReceiptDigest?: string;
  /**
   * Impersonation actor-tagging (SOC2/ISO27001 "prove exactly what an
   * engineer touched while impersonating", not just "we logged the
   * start/end of the session"): set by middleware.ts on every request
   * made while an active lib/impersonation.ts session's targetOrgId
   * matches the org this request is scoped to. `impersonatedBy` is the
   * real admin identity that started the session (never the target
   * org's own actor -- `actor` above stays whatever it already was, this
   * field is additive, not a replacement, so existing readers of `actor`
   * are unaffected); `impersonationSessionId` cross-references the exact
   * row in `platform_console.impersonation_sessions` this action
   * happened under. Both absent for every normal, non-impersonated
   * request -- the overwhelming majority of rows.
   */
  impersonatedBy?: string;
  impersonationSessionId?: string;
  /**
   * Custom RBAC (lib/custom-roles.ts) cross-reference: the fine-grained
   * Permission a request was gated on when the decision came from
   * lib/authz.ts's hasPermission fallback (a custom-role grant) rather
   * than the built-in viewer/member/owner rank -- lets a reviewer see
   * exactly which narrower, least-privilege grant authorized (or denied)
   * an action, on top of the existing role-rank audit trail. Absent for
   * every request gated purely by the built-in rank.
   */
  requiredPermission?: string;
  /**
   * Per-org tenant scope (SIEM export org-scoping): the org this action was
   * performed against, when the request resolved to one (most routes have
   * it via getProject/getOrg/session context). Absent for genuinely
   * unscoped/platform-wide actions (e.g. a route with no single-org
   * subject). Nullable at the storage layer for backward compatibility
   * with rows written before this field existed -- see audit-db.ts's
   * ensureAuditLogChainColumns and computeRowHash.
   */
  orgId?: string;
  /**
   * Customer-facing API key usage analytics (queryApiKeyUsage in
   * lib/audit-db.ts): the real join key from an audit row back to the
   * specific `pk_live_...` key that authenticated it (lib/api-keys.ts's
   * ResolvedApiKeyAuth.keyId). Set by middleware.ts only on requests
   * authenticated via `Authorization: Bearer pk_live_...` -- absent for
   * every session-cookie-authenticated request, since a browser session
   * isn't bound to any one key. `actor` alone can't disambiguate between
   * two keys minted for the same bound identity; `keyId` can.
   */
  keyId?: string;
  /**
   * Customer-facing API key usage analytics: wall-clock request latency
   * in whole milliseconds, measured by middleware.ts from the start of
   * this request's own middleware invocation to the point the response
   * was ready to forward. Optional and absent for any row written before
   * this field existed -- queryApiKeyUsage's p50/p95 latency aggregation
   * skips NULLs rather than treating them as zero.
   */
  durationMs?: number;
}

export function writeAuditLogEntry(entry: AuditLogEntry): void {
  // Deliberately a single console.log call producing exactly one JSON line
  // per entry -- straightforward to grep/parse/ship from stdout in any
  // container log pipeline (kubectl logs, Fluent Bit, etc.).
  console.log(JSON.stringify(entry));
}

export function newRequestId(): string {
  return crypto.randomUUID();
}
