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
