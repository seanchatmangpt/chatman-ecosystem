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
