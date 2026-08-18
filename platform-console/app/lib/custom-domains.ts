/**
 * Real Custom Domain self-service (the AWS Certificate Manager + Route53
 * custom-domain binding / GCP Cloud Run custom-domain equivalent): an
 * operator names a hostname and picks one of the platform's own real
 * Services (the same list Service Discovery already reads,
 * `listAllServices` in lib/k8s.ts), and this module does the three real
 * things a hyperscaler's console does behind that one click --
 *
 *   1. issues a real TLS certificate (self-signed here -- no ACM/Let's
 *      Encrypt in this cluster -- but a REAL X.509 certificate, generated
 *      fresh per hostname via `openssl req -x509`, its SAN independently
 *      re-parsed with Node's own `crypto.X509Certificate` and checked
 *      against the requested hostname with `checkHost` before it is ever
 *      stored, so a broken/empty cert can never reach the cluster);
 *   2. stores it as a real `kubernetes.io/tls` Secret in `istio-system`
 *      (the same namespace k8s/gateway.yaml's `platform-console-tls` and
 *      k8s/mtls-gateway.yaml's `platform-backups-mtls-credential` already
 *      live in -- Istio's ingress gateway SDS only reads `credentialName`
 *      Secrets from its own workload's namespace, not the Gateway
 *      object's namespace, confirmed by both of those existing Secrets
 *      living there already); and
 *   3. creates a real `networking.istio.io/v1` Gateway + VirtualService
 *      pair bound to that hostname, on a NEW shared port (8443) reserved
 *      for exactly this feature -- reusing the multi-Gateway/SNI pattern
 *      k8s/gateway.yaml (port 443, host platform.local) and
 *      k8s/mtls-gateway.yaml (port 8444, host backups.platform.local)
 *      already establish: several Gateway objects, each scoped to its own
 *      host(s) and its own `credentialName`, all selecting the same
 *      `istio: ingressgateway` workload -- Istio's Gateway controller
 *      merges them into one Envoy listener per port with per-hostname SNI
 *      cert selection, so registering domain #2 never touches domain #1's
 *      objects. Port 8443 itself must be opened on the shared
 *      `istio-ingressgateway` Service ONCE (same one-time
 *      `kubectl patch svc` step k8s/mtls-gateway.yaml's own header
 *      comment documents for its 8444) -- see README.md's Custom Domains
 *      section for that command; it is infrastructure, not something a
 *      per-domain registration call can or should repeat.
 *
 * All three real k8s objects (Secret, Gateway, VirtualService) are named
 * deterministically from the hostname (`slugFromHostname`) and carry a
 * `platform-console.io/custom-domain: "true"` label plus
 * `platform-console.io/*` annotations recording the real target service --
 * so `listCustomDomains` never needs a side database, it just re-reads the
 * live Gateway objects, the same "the listing IS the record" convention
 * lib/scheduled-jobs.ts/lib/batch-jobs.ts already use for CronJobs/Jobs.
 *
 * Ordering matters, same "safe-failure ordering" discipline
 * lib/canary.ts's promote/rollback already documents: on register, the
 * VirtualService (the object that actually turns on live routing) is
 * created LAST, after the Secret and Gateway it depends on already exist
 * -- a failure partway through leaves, at worst, a Gateway presenting a
 * real cert with no route (a 404), never a route with a missing cert. On
 * unbind, the VirtualService is deleted FIRST, so live traffic to that
 * hostname stops before the Gateway/Secret backing it are torn down.
 * `registerCustomDomain` also rolls back whatever it already created if a
 * later step fails, so a half-registered domain is never left behind
 * silently.
 */
import { execFileSync } from "node:child_process";
import { X509Certificate } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { k8sRequest, type K8sResult } from "@/lib/k8s";

export const CUSTOM_DOMAIN_OBJECT_NAMESPACE = "platform-console";
export const CUSTOM_DOMAIN_TLS_SECRET_NAMESPACE = "istio-system";
// The Gateway CR's OWN declared `servers[].port.number` -- deliberately
// 443, the exact same declared number k8s/gateway.yaml's
// platform-console-gateway already uses, NOT the 8443 external port an
// operator actually connects to. Confirmed live via `istioctl
// proxy-config listener` before this value was picked: this cluster's
// istio-ingressgateway runs as non-root, so Istio auto-offsets any
// declared port <1024 by +8000 when binding Envoy's real listener
// (443 -> a real 0.0.0.0:8443 socket inside the pod) -- and Gateway
// objects only merge onto the SAME physical Envoy listener (splitting
// traffic by SNI) when they declare the SAME port.number. Declaring 8443
// directly here (an un-offset, >=1024 number) would instead make Envoy
// try to bind ITS OWN separate listener on that exact socket -- a real
// conflict with the listener platform-console-gateway's offset 443
// already owns, not a second usable route. Using 443 here means every
// custom domain's server merges into that one already-existing
// 0.0.0.0:8443 listener via SNI, the same mechanism k8s/gateway.yaml
// (platform.local) and every Custom Domain hostname share.
export const CUSTOM_DOMAIN_GATEWAY_DECLARED_PORT = 443;
// The REAL external port an operator/curl actually connects to --
// exposed on the shared `istio-ingressgateway` Service as a dedicated
// NodePort (`kubectl patch svc istio-ingressgateway -n istio-system
// --type=json -p '[{"op":"add","path":"/spec/ports/-","value":
// {"name":"https-custom-domains","port":8443,"targetPort":8443,
// "protocol":"TCP"}}]'`, a one-time cluster-infra step, same pattern
// k8s/mtls-gateway.yaml's own header comment documents for its 8444 --
// see README.md's Custom Domains section). `targetPort` here is 8443
// because that's the REAL container port the 443->8443 offset above
// already binds to -- this Service port is simply a second, dedicated
// external door onto the exact same physical listener, not a new one.
export const CUSTOM_DOMAIN_EXTERNAL_PORT = 8443;
export const CUSTOM_DOMAIN_LABEL = "platform-console.io/custom-domain";

const HOSTNAME_LABEL_RE = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$/;

/** RFC 1123-shaped FQDN: at least two dot-separated labels, each a valid
 * DNS label, total length <=253 -- deliberately requires a real dotted
 * hostname (never a bare label) since this feature is "bind a custom
 * DOMAIN", not "bind an unqualified name". */
export function isValidCustomDomainHostname(hostname: string): boolean {
  if (hostname.length === 0 || hostname.length > 253) return false;
  const labels = hostname.toLowerCase().split(".");
  if (labels.length < 2) return false;
  return labels.every((label) => HOSTNAME_LABEL_RE.test(label));
}

/** Deterministic, DNS-safe object-name slug for a hostname -- e.g.
 * `demo.platform.local` -> `demo-platform-local`. Every real k8s object
 * this module creates/reads/deletes for a given hostname is named from
 * this same slug, so a caller only ever needs the hostname to find them
 * all again. */
export function slugFromHostname(hostname: string): string {
  return hostname
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 200);
}

function secretName(slug: string): string {
  return `custom-domain-${slug}-tls`;
}
function gatewayName(slug: string): string {
  return `custom-domain-${slug}-gateway`;
}
function virtualServiceName(slug: string): string {
  return `custom-domain-${slug}-vs`;
}

export interface CustomDomainTarget {
  serviceName: string;
  serviceNamespace: string;
  servicePort: number;
}

export interface CustomDomainBinding {
  hostname: string;
  slug: string;
  target: CustomDomainTarget;
  secretName: string;
  gatewayName: string;
  virtualServiceName: string;
  certificateNotAfter: string | null;
  createdAt: string;
}

/**
 * Generates a real, fresh, self-signed X.509 certificate for exactly one
 * hostname via a real `openssl req -x509` subprocess (no forged/placeholder
 * PEM content, no bundled cert library) -- an ECDSA-free plain RSA-2048
 * key, matching the exact command k8s/gateway.yaml's own header comment
 * already documents for platform-console-tls, just parameterized per
 * hostname and with an explicit `subjectAltName` extension (SAN-only certs
 * are what every real browser/`curl`/`openssl s_client` actually validates
 * against today -- a bare CN match is not sufficient by itself in modern
 * TLS stacks). Runs entirely in a throwaway temp directory
 * (`fs.mkdtempSync`) that is always removed in a `finally`, so the
 * generated private key never lingers on disk past this one call.
 *
 * Before returning, the freshly-generated cert is independently re-parsed
 * with Node's OWN `crypto.X509Certificate` (not a re-read of what openssl
 * claims to have done) and `checkHost(hostname)` is required to actually
 * match -- a real, second, independent verification that the certificate
 * this function is about to hand to the caller genuinely covers the
 * requested hostname, before it is ever stored as a cluster Secret.
 *
 * Exported (not module-private) so lib/cert-lifecycle.ts's
 * `rotateCertificate` can reuse this EXACT same generation +
 * independent-re-verification path for a custom domain's renewed cert --
 * the same "one real code path, never a second driftable copy" discipline
 * lib/k8s.ts's `buildSingleDatabaseManifest` doc comment already documents
 * for `detectDrift`.
 */
export function generateSelfSignedCertificate(hostname: string): {
  certPem: string;
  keyPem: string;
  notAfter: string;
} {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "custom-domain-cert-"));
  try {
    const keyPath = path.join(dir, "key.pem");
    const certPath = path.join(dir, "cert.pem");
    execFileSync(
      "openssl",
      [
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-days",
        "365",
        "-keyout",
        keyPath,
        "-out",
        certPath,
        "-subj",
        `/CN=${hostname}`,
        "-addext",
        `subjectAltName=DNS:${hostname}`,
      ],
      { stdio: ["ignore", "pipe", "pipe"], timeout: 15_000 },
    );
    const certPem = fs.readFileSync(certPath, "utf8");
    const keyPem = fs.readFileSync(keyPath, "utf8");

    const parsed = new X509Certificate(certPem);
    const matched = parsed.checkHost(hostname);
    if (!matched) {
      throw new Error(
        `generated certificate's SAN does not cover ${hostname} ` +
          `(subjectAltName=${parsed.subjectAltName ?? "none"}) -- refusing to store it`,
      );
    }

    return { certPem, keyPem, notAfter: new Date(parsed.validTo).toISOString() };
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

interface SecretItem {
  metadata: { name: string; namespace: string; creationTimestamp?: string };
}

async function createTlsSecret(
  slug: string,
  hostname: string,
  certPem: string,
  keyPem: string,
): Promise<K8sResult<SecretItem>> {
  const manifest = {
    apiVersion: "v1",
    kind: "Secret",
    type: "kubernetes.io/tls",
    metadata: {
      name: secretName(slug),
      namespace: CUSTOM_DOMAIN_TLS_SECRET_NAMESPACE,
      labels: { [CUSTOM_DOMAIN_LABEL]: "true" },
      annotations: { "platform-console.io/hostname": hostname },
    },
    data: {
      "tls.crt": Buffer.from(certPem, "utf8").toString("base64"),
      "tls.key": Buffer.from(keyPem, "utf8").toString("base64"),
    },
  };
  return k8sRequest<SecretItem>(
    `/api/v1/namespaces/${CUSTOM_DOMAIN_TLS_SECRET_NAMESPACE}/secrets`,
    "POST",
    manifest,
  );
}

async function deleteTlsSecret(slug: string): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/api/v1/namespaces/${CUSTOM_DOMAIN_TLS_SECRET_NAMESPACE}/secrets/${encodeURIComponent(secretName(slug))}`,
    "DELETE",
  );
  if (!result.ok && !/not found/i.test(result.error)) return result;
  return { ok: true, data: null };
}

function gatewayManifest(slug: string, hostname: string, target: CustomDomainTarget) {
  return {
    apiVersion: "networking.istio.io/v1",
    kind: "Gateway",
    metadata: {
      name: gatewayName(slug),
      namespace: CUSTOM_DOMAIN_OBJECT_NAMESPACE,
      labels: { [CUSTOM_DOMAIN_LABEL]: "true" },
      annotations: {
        "platform-console.io/hostname": hostname,
        "platform-console.io/target-service": target.serviceName,
        "platform-console.io/target-namespace": target.serviceNamespace,
        "platform-console.io/target-port": String(target.servicePort),
      },
    },
    spec: {
      selector: { istio: "ingressgateway" },
      servers: [
        {
          // port.number is 443 (not the 8443 operators actually connect
          // to) -- see CUSTOM_DOMAIN_GATEWAY_DECLARED_PORT's own comment
          // above for why: this is what makes Istio merge this server
          // onto the SAME physical Envoy listener platform-console-
          // gateway's own https:443 server already owns, split by SNI.
          port: {
            name: `https-${slug}`.slice(0, 63),
            number: CUSTOM_DOMAIN_GATEWAY_DECLARED_PORT,
            protocol: "HTTPS",
          },
          hosts: [hostname],
          tls: { mode: "SIMPLE", credentialName: secretName(slug) },
        },
      ],
    },
  };
}

function virtualServiceManifest(slug: string, hostname: string, target: CustomDomainTarget) {
  return {
    apiVersion: "networking.istio.io/v1",
    kind: "VirtualService",
    metadata: {
      name: virtualServiceName(slug),
      namespace: CUSTOM_DOMAIN_OBJECT_NAMESPACE,
      labels: { [CUSTOM_DOMAIN_LABEL]: "true" },
      annotations: { "platform-console.io/hostname": hostname },
    },
    spec: {
      hosts: [hostname],
      gateways: [gatewayName(slug)],
      http: [
        {
          name: `custom-domain-${slug}`.slice(0, 63),
          route: [
            {
              destination: {
                host: `${target.serviceName}.${target.serviceNamespace}.svc.cluster.local`,
                port: { number: target.servicePort },
              },
            },
          ],
        },
      ],
    },
  };
}

async function createGateway(
  slug: string,
  hostname: string,
  target: CustomDomainTarget,
): Promise<K8sResult<unknown>> {
  return k8sRequest(
    `/apis/networking.istio.io/v1/namespaces/${CUSTOM_DOMAIN_OBJECT_NAMESPACE}/gateways`,
    "POST",
    gatewayManifest(slug, hostname, target),
  );
}

async function deleteGateway(slug: string): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/apis/networking.istio.io/v1/namespaces/${CUSTOM_DOMAIN_OBJECT_NAMESPACE}/gateways/${encodeURIComponent(gatewayName(slug))}`,
    "DELETE",
  );
  if (!result.ok && !/not found/i.test(result.error)) return result;
  return { ok: true, data: null };
}

async function createVirtualService(
  slug: string,
  hostname: string,
  target: CustomDomainTarget,
): Promise<K8sResult<unknown>> {
  return k8sRequest(
    `/apis/networking.istio.io/v1/namespaces/${CUSTOM_DOMAIN_OBJECT_NAMESPACE}/virtualservices`,
    "POST",
    virtualServiceManifest(slug, hostname, target),
  );
}

async function deleteVirtualService(slug: string): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/apis/networking.istio.io/v1/namespaces/${CUSTOM_DOMAIN_OBJECT_NAMESPACE}/virtualservices/${encodeURIComponent(virtualServiceName(slug))}`,
    "DELETE",
  );
  if (!result.ok && !/not found/i.test(result.error)) return result;
  return { ok: true, data: null };
}

/**
 * Registers one real custom hostname -> target Service binding. Fails
 * closed and rolls back (best-effort delete of whatever it already
 * created) on the first error, so a partial failure never leaves an
 * orphaned Secret/Gateway with no route, or a route with no valid cert.
 */
export async function registerCustomDomain(
  hostname: string,
  target: CustomDomainTarget,
): Promise<K8sResult<CustomDomainBinding>> {
  if (!isValidCustomDomainHostname(hostname)) {
    return {
      ok: false,
      error: `"${hostname}" is not a valid DNS hostname (need at least two dot-separated RFC 1123 labels)`,
    };
  }
  if (
    !target.serviceName ||
    !target.serviceNamespace ||
    !Number.isInteger(target.servicePort) ||
    target.servicePort <= 0
  ) {
    return { ok: false, error: "target serviceName, serviceNamespace, and a positive servicePort are required" };
  }

  const slug = slugFromHostname(hostname);

  let certPem: string;
  let keyPem: string;
  let notAfter: string;
  try {
    ({ certPem, keyPem, notAfter } = generateSelfSignedCertificate(hostname));
  } catch (err) {
    return {
      ok: false,
      error: `certificate generation failed: ${err instanceof Error ? err.message : String(err)}`,
    };
  }

  const secretResult = await createTlsSecret(slug, hostname, certPem, keyPem);
  if (!secretResult.ok) {
    if (/already exists/i.test(secretResult.error)) {
      return { ok: false, error: `hostname "${hostname}" is already registered` };
    }
    return secretResult;
  }

  const gatewayResult = await createGateway(slug, hostname, target);
  if (!gatewayResult.ok) {
    await deleteTlsSecret(slug);
    if (/already exists/i.test(gatewayResult.error)) {
      return { ok: false, error: `hostname "${hostname}" is already registered` };
    }
    return gatewayResult;
  }

  const vsResult = await createVirtualService(slug, hostname, target);
  if (!vsResult.ok) {
    await deleteGateway(slug);
    await deleteTlsSecret(slug);
    return vsResult;
  }

  return {
    ok: true,
    data: {
      hostname,
      slug,
      target: {
        serviceName: target.serviceName,
        serviceNamespace: target.serviceNamespace,
        servicePort: target.servicePort,
      },
      secretName: secretName(slug),
      gatewayName: gatewayName(slug),
      virtualServiceName: virtualServiceName(slug),
      certificateNotAfter: notAfter,
      createdAt: new Date().toISOString(),
    },
  };
}

interface GatewayListItem {
  metadata: {
    name: string;
    namespace: string;
    creationTimestamp?: string;
    annotations?: Record<string, string>;
  };
  spec?: {
    servers?: Array<{ hosts?: string[]; tls?: { credentialName?: string } }>;
  };
}
interface GatewayListResponse {
  items?: GatewayListItem[];
}

/**
 * Real, live re-read of every custom domain currently bound -- no side
 * database, the Gateway objects themselves (filtered by the
 * `platform-console.io/custom-domain=true` label this module always
 * applies) are the record, same "the listing IS the record" convention
 * lib/scheduled-jobs.ts/lib/batch-jobs.ts already use.
 */
export async function listCustomDomains(): Promise<K8sResult<CustomDomainBinding[]>> {
  const result = await k8sRequest<GatewayListResponse>(
    `/apis/networking.istio.io/v1/namespaces/${CUSTOM_DOMAIN_OBJECT_NAMESPACE}/gateways` +
      `?labelSelector=${encodeURIComponent(`${CUSTOM_DOMAIN_LABEL}=true`)}`,
  );
  if (!result.ok) return result;

  const bindings: CustomDomainBinding[] = (result.data.items ?? []).map((item) => {
    const annotations = item.metadata.annotations ?? {};
    const hostname = annotations["platform-console.io/hostname"] ?? item.spec?.servers?.[0]?.hosts?.[0] ?? "";
    const slug = slugFromHostname(hostname);
    return {
      hostname,
      slug,
      target: {
        serviceName: annotations["platform-console.io/target-service"] ?? "",
        serviceNamespace: annotations["platform-console.io/target-namespace"] ?? "",
        servicePort: Number(annotations["platform-console.io/target-port"] ?? 0),
      },
      secretName: item.spec?.servers?.[0]?.tls?.credentialName ?? secretName(slug),
      gatewayName: item.metadata.name,
      virtualServiceName: virtualServiceName(slug),
      certificateNotAfter: null,
      createdAt: item.metadata.creationTimestamp ?? "",
    };
  });
  return { ok: true, data: bindings };
}

/**
 * Unbinds one real custom hostname: deletes the VirtualService FIRST (so
 * live routing to that hostname stops immediately), then the Gateway,
 * then the TLS Secret -- reverse of registerCustomDomain's create order.
 * Idempotent: deleting an already-absent object of any of the three kinds
 * is treated as success, same "safely re-runnable" convention
 * lib/canary.ts's deleteDeployment already documents.
 */
export async function unbindCustomDomain(hostname: string): Promise<K8sResult<null>> {
  const slug = slugFromHostname(hostname);
  const vsResult = await deleteVirtualService(slug);
  if (!vsResult.ok) return vsResult;
  const gatewayResult = await deleteGateway(slug);
  if (!gatewayResult.ok) return gatewayResult;
  return deleteTlsSecret(slug);
}
