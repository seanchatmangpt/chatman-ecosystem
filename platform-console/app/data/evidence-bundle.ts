/**
 * Static evidence-bundle entries for the /compliance page.
 *
 * Doctrine (adopted from ggen-marketplace/packs/soc2-audit-pack/ontology.ttl,
 * line 24's comment): no field or string here is ever named "compliant" or
 * "soc2_ready". Every entry states a specific, checkable technical fact
 * ("evidence_gathered") -- never a verdict about compliance status, which
 * only a licensed CPA firm can issue after an independent audit.
 *
 * evidence_type distinguishes what kind of fact each entry is:
 * - "source_control_definition": the control is defined in this repo's
 *   source and can be read directly at source_reference.
 * - "runtime_observation": the control's live state was directly observed
 *   (e.g. via kubectl) at last_verified_at -- see notes for how.
 */
export interface EvidenceEntry {
  id: string;
  control: string;
  description: string;
  evidence_type: "source_control_definition" | "runtime_observation";
  source_reference: string;
  last_verified_at: string;
  notes?: string;
}

export const evidenceBundle: EvidenceEntry[] = [
  {
    id: "auth-session-gating",
    control: "Session-based authentication on every dashboard route",
    description:
      "middleware.ts verifies a signed session JWT (jose, HS256) on every " +
      "request outside the public allowlist (/login, /api/login) and " +
      "redirects to /login when absent or invalid.",
    evidence_type: "source_control_definition",
    source_reference: "platform-console/app/middleware.ts",
    last_verified_at: "2026-08-17T00:00:00Z",
  },
  {
    id: "audit-log-emission",
    control: "Structured access logging",
    description:
      "Every authenticated request causes exactly one JSON line " +
      "(timestamp, actor, method, path, status, requestId) to be written " +
      "to stdout via lib/audit-log.ts, called from middleware.ts.",
    evidence_type: "source_control_definition",
    source_reference: "platform-console/app/lib/audit-log.ts",
    last_verified_at: "2026-08-17T00:00:00Z",
  },
  {
    id: "audit-log-durable-and-queryable",
    control: "Durable, queryable audit trail",
    description:
      "Every /api/* route additionally INSERTs the same audit entry into " +
      "a real platform_console.audit_log table on the live demo-project " +
      "Postgres (lib/audit-db.ts), and /audit (owner-gated) provides a " +
      "real filter/pagination query UI over it -- closing the prior gap " +
      "that the stdout line above does not survive a pod restart. Live-" +
      "verified: 7 real requests cross-matched byte-for-byte across " +
      "stdout, the app's own API, and a direct psql SELECT, then a pod " +
      "deletion showed the stdout record gone while the DB row survived.",
    evidence_type: "runtime_observation",
    source_reference: "platform-console/app/lib/audit-db.ts",
    last_verified_at: "2026-08-18T08:15:00Z",
    notes:
      "See audit-log-durable-and-queryable in evidence/control-evidence-bundle.json for the full requestId cross-match and the pod-deletion durability proof.",
  },
  {
    id: "password-hash-only",
    control: "No plaintext credentials in source",
    description:
      "The seeded admin account is authenticated against " +
      "ADMIN_PASSWORD_HASH (a bcrypt hash supplied via environment " +
      "variable) using bcryptjs.compare -- no plaintext password appears " +
      "in source or version control.",
    evidence_type: "source_control_definition",
    source_reference: "platform-console/app/lib/credentials.ts",
    last_verified_at: "2026-08-17T00:00:00Z",
  },
  {
    id: "network-default-deny",
    control: "Per-namespace default-deny NetworkPolicy",
    description:
      "Each project namespace (autofde-lab, gymact, ggen, " +
      "ggen-marketplace) is designed with a <project>-default-deny " +
      "NetworkPolicy (podSelector: {}, policyTypes: [Ingress, Egress]) " +
      "plus a single scoped allow rule from platform-console.",
    evidence_type: "source_control_definition",
    source_reference: "docs/platform-engineers-handbook-colima-runtime.md",
    last_verified_at: "2026-08-17T00:00:00Z",
    notes:
      "This describes the namespace design this console was built " +
      "against. It is not a live kubectl observation from this app -- " +
      "the app does not have cluster-admin credentials to enumerate " +
      "NetworkPolicy objects, and does not claim to.",
  },
  {
    id: "mtls-strict",
    control: "Istio mTLS STRICT mode",
    description:
      "The application namespace's live PeerAuthentication object " +
      "(application-mtls) and the mesh-wide default in istio-system are " +
      "both observed with mode: STRICT.",
    evidence_type: "runtime_observation",
    source_reference: "kubectl get peerauthentication -A",
    last_verified_at: "2026-08-17T00:00:00Z",
    notes:
      "Observed directly against the running kind-platform-eng-colima " +
      "cluster during the design pass that preceded this console.",
  },
  {
    id: "status-endpoints-no-fabrication",
    control: "Project status pages fail closed",
    description:
      "Each of the four per-project dashboard pages fetches its " +
      "cluster-internal status endpoint at request time and renders " +
      "'unreachable' on any fetch failure -- no fallback or cached data " +
      "is substituted.",
    evidence_type: "source_control_definition",
    source_reference: "platform-console/app/lib/status.ts",
    last_verified_at: "2026-08-17T00:00:00Z",
  },
];
