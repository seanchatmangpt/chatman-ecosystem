/**
 * Real Certificate Lifecycle tracking (the AWS Certificate Manager
 * auto-renewal / GCP-managed-certificate rotation equivalent) for every TLS
 * Secret this platform actually manages -- no side database, this module
 * reads the same live Secrets the cluster's own Envoy/SDS layer already
 * reads and parses each real certificate's real `notAfter` with Node's own
 * `crypto.X509Certificate`, the same "the listing IS the record" convention
 * lib/custom-domains.ts's `listCustomDomains` and
 * lib/scheduled-jobs.ts/lib/batch-jobs.ts already use.
 *
 * All three real, known TLS-bearing Secrets in `istio-system` are covered
 * by a single namespace-wide list call, not three separate hardcoded GETs:
 *
 *   - `platform-console-tls`     (k8s/gateway.yaml's own HTTPS credential)
 *   - `platform-backups-mtls-credential` (k8s/mtls-gateway.yaml's client-CA
 *     credential -- deliberately `type: Opaque`, not `kubernetes.io/tls`,
 *     because it carries a `ca.crt` alongside `tls.crt`/`tls.key` for mTLS
 *     client verification, confirmed live via `kubectl get secret -n
 *     istio-system platform-backups-mtls-credential -o
 *     jsonpath='{.type}'` returning `Opaque` -- so this module filters on
 *     "does `data['tls.crt']` exist", never on `type`, or this credential
 *     would be silently skipped)
 *   - every `custom-domain-<slug>-tls` Secret lib/custom-domains.ts's
 *     `registerCustomDomain` creates, identified the same way
 *     `listCustomDomains` already does: the
 *     `platform-console.io/custom-domain: "true"` label.
 *
 * Only custom-domain certificates are ever `rotatable` -- rotating
 * `platform-console-tls`/the mTLS credential would need a different CA
 * story (a real client-trust chain, not a fresh self-signed leaf) and is
 * deliberately out of scope here, same "disclosed gap, not silently
 * assumed" discipline README.md's Custom Domains section already
 * documents for this feature's RBAC scope.
 */
import { X509Certificate } from "node:crypto";
import { k8sRequest, createOrUpdateSecret, type K8sResult } from "@/lib/k8s";
import {
  CUSTOM_DOMAIN_LABEL,
  CUSTOM_DOMAIN_TLS_SECRET_NAMESPACE,
  generateSelfSignedCertificate,
} from "@/lib/custom-domains";

/** Days-until-expiry threshold that flags a certificate for renewal in the
 * dashboard -- the same order of magnitude ACM/GCP-managed-certs warn at
 * (ACM auto-renews starting ~60 days out; this platform's certs are
 * self-signed 365-day leaves, so 30 days gives a real, actionable runway
 * without flagging nearly every cert nearly all the time). */
export const EXPIRY_WARNING_DAYS = 30;

export type ManagedCertificateKind = "custom-domain" | "platform-console-tls" | "mtls-backups" | "other";

export interface ManagedCertificate {
  secretName: string;
  namespace: string;
  kind: ManagedCertificateKind;
  /** From the `platform-console.io/hostname` annotation custom-domain
   * Secrets always carry, falling back to the cert's own SAN/CN for the
   * two well-known non-custom-domain Secrets, which carry no such
   * annotation. */
  hostname: string | null;
  subject: string;
  issuer: string;
  serialNumber: string;
  notBefore: string; // ISO 8601
  notAfter: string; // ISO 8601
  daysUntilExpiry: number; // real days, floor()'d, negative once expired
  expiringSoon: boolean; // daysUntilExpiry < EXPIRY_WARNING_DAYS
  expired: boolean;
  /** Only true for kind: "custom-domain" -- see module doc comment. */
  rotatable: boolean;
}

interface RawSecretItem {
  metadata: {
    name: string;
    namespace: string;
    labels?: Record<string, string>;
    annotations?: Record<string, string>;
  };
  type?: string;
  data?: Record<string, string>; // base64
}

interface RawSecretListResponse {
  items?: RawSecretItem[];
}

function classify(name: string, labels: Record<string, string>): ManagedCertificateKind {
  if (labels[CUSTOM_DOMAIN_LABEL] === "true") return "custom-domain";
  if (name === "platform-console-tls") return "platform-console-tls";
  if (name === "platform-backups-mtls-credential") return "mtls-backups";
  return "other";
}

function extractSanHost(cert: X509Certificate): string | null {
  const san = cert.subjectAltName; // e.g. "DNS:demo.platform.local"
  if (!san) return null;
  const match = san.split(",").map((s) => s.trim()).find((s) => s.startsWith("DNS:"));
  return match ? match.slice(4) : null;
}

function toManagedCertificate(item: RawSecretItem): ManagedCertificate | null {
  const certB64 = item.data?.["tls.crt"];
  if (!certB64) return null;

  let parsed: X509Certificate;
  try {
    parsed = new X509Certificate(Buffer.from(certB64, "base64").toString("utf8"));
  } catch {
    // A genuinely unparsable "tls.crt" value is a real, honest anomaly --
    // skipped rather than crashing the whole dashboard for every other
    // real cert.
    return null;
  }

  const labels = item.metadata.labels ?? {};
  const annotations = item.metadata.annotations ?? {};
  const kind = classify(item.metadata.name, labels);
  const notAfter = new Date(parsed.validTo);
  const notBefore = new Date(parsed.validFrom);
  const daysUntilExpiry = Math.floor((notAfter.getTime() - Date.now()) / (24 * 60 * 60 * 1000));

  return {
    secretName: item.metadata.name,
    namespace: item.metadata.namespace,
    kind,
    hostname: annotations["platform-console.io/hostname"] ?? extractSanHost(parsed),
    subject: parsed.subject,
    issuer: parsed.issuer,
    serialNumber: parsed.serialNumber,
    notBefore: notBefore.toISOString(),
    notAfter: notAfter.toISOString(),
    daysUntilExpiry,
    expiringSoon: daysUntilExpiry < EXPIRY_WARNING_DAYS,
    expired: daysUntilExpiry < 0,
    rotatable: kind === "custom-domain",
  };
}

/**
 * Real, live scan of every TLS-bearing Secret in `istio-system` -- one
 * namespace-wide GET, filtered client-side to Secrets that actually carry a
 * `tls.crt` key (never on `type`, per the module doc comment above), then
 * each real cert independently parsed with Node's own `X509Certificate`.
 * Sorted soonest-to-expire first, so the dashboard's most actionable rows
 * lead.
 */
export async function listManagedCertificates(): Promise<K8sResult<ManagedCertificate[]>> {
  const result = await k8sRequest<RawSecretListResponse>(
    `/api/v1/namespaces/${CUSTOM_DOMAIN_TLS_SECRET_NAMESPACE}/secrets`,
  );
  if (!result.ok) return result;

  const certs = (result.data.items ?? [])
    .map(toManagedCertificate)
    .filter((c): c is ManagedCertificate => c !== null)
    .sort((a, b) => a.daysUntilExpiry - b.daysUntilExpiry);

  return { ok: true, data: certs };
}

export interface CertificateRotationResult {
  secretName: string;
  hostname: string;
  oldSerialNumber: string;
  newSerialNumber: string;
  oldNotAfter: string;
  newNotAfter: string;
  rotatedAt: string;
}

/**
 * Rotates one custom-domain certificate IN PLACE -- same Secret name, fresh
 * cert data -- rather than delete+recreate. This is the whole point: Istio
 * SDS watches each `credentialName` Secret it already loaded and pushes new
 * key/cert material to Envoy the instant the Secret's `data` changes, with
 * no Gateway/VirtualService object touched at all, so live TLS handshakes
 * against that hostname keep being served (old cert to connections
 * already served from cache, new cert to every connection after SDS's
 * watch fires) -- a delete+recreate would instead tear down the Secret
 * object SDS is watching, a real (if brief) gap a same-name in-place PATCH
 * never introduces.
 *
 * Reuses lib/custom-domains.ts's own `generateSelfSignedCertificate` (the
 * exact same `openssl req -x509` + independent `checkHost` re-verification
 * every fresh registration already goes through) and lib/k8s.ts's own
 * `createOrUpdateSecret` (an RFC 7386 merge-patch on `data` only -- the
 * Secret's `metadata.labels`/`annotations`, including the
 * `platform-console.io/hostname` annotation this function itself reads,
 * are left completely untouched).
 */
export async function rotateCertificate(
  secretName: string,
): Promise<K8sResult<CertificateRotationResult>> {
  const existingResult = await k8sRequest<RawSecretItem>(
    `/api/v1/namespaces/${CUSTOM_DOMAIN_TLS_SECRET_NAMESPACE}/secrets/${encodeURIComponent(secretName)}`,
  );
  if (!existingResult.ok) return existingResult;

  const existing = existingResult.data;
  const labels = existing.metadata.labels ?? {};
  const annotations = existing.metadata.annotations ?? {};
  const hostname = annotations["platform-console.io/hostname"];

  if (labels[CUSTOM_DOMAIN_LABEL] !== "true" || !hostname) {
    return {
      ok: false,
      error:
        `"${secretName}" is not a rotatable custom-domain certificate ` +
        `(missing "${CUSTOM_DOMAIN_LABEL}: true" label or "platform-console.io/hostname" annotation) -- ` +
        "platform-console-tls and the mTLS backups credential are deliberately not rotatable here",
    };
  }

  const oldCertB64 = existing.data?.["tls.crt"];
  if (!oldCertB64) {
    return { ok: false, error: `"${secretName}" has no "tls.crt" key -- cannot determine its current certificate` };
  }
  const oldParsed = new X509Certificate(Buffer.from(oldCertB64, "base64").toString("utf8"));

  let certPem: string;
  let keyPem: string;
  let notAfter: string;
  try {
    ({ certPem, keyPem, notAfter } = generateSelfSignedCertificate(hostname));
  } catch (err) {
    return { ok: false, error: `certificate generation failed: ${err instanceof Error ? err.message : String(err)}` };
  }

  const updateResult = await createOrUpdateSecret(CUSTOM_DOMAIN_TLS_SECRET_NAMESPACE, secretName, {
    "tls.crt": certPem,
    "tls.key": keyPem,
  });
  if (!updateResult.ok) return updateResult;

  const newParsed = new X509Certificate(certPem);

  return {
    ok: true,
    data: {
      secretName,
      hostname,
      oldSerialNumber: oldParsed.serialNumber,
      newSerialNumber: newParsed.serialNumber,
      oldNotAfter: new Date(oldParsed.validTo).toISOString(),
      newNotAfter: notAfter,
      rotatedAt: new Date().toISOString(),
    },
  };
}
