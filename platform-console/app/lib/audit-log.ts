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
