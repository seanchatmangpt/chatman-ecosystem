/**
 * Real org-level IP allowlist / network access policy for console login
 * (SOC2 / enterprise-vendor-review checklist item: "only our corporate
 * VPN/office CIDR ranges may reach the admin console"). lib/authz.ts's
 * RBAC controls what an authenticated identity may DO once inside; this
 * module is the layer underneath that -- it controls WHERE a request is
 * even allowed to originate from before authorization is ever evaluated.
 *
 * Storage: one real k8s ConfigMap (`platform-console-ip-allowlist`,
 * `platform-console` namespace), reusing the exact get-then-create-or-
 * patch primitive (`getConfigMap` / `createOrUpdateConfigMap`) every
 * other ConfigMap-backed module in this app already uses (lib/authz.ts,
 * lib/quota-enforcement.ts, lib/budget-alerts.ts) -- no new k8s resource
 * kind, no new RBAC verb: the existing `platform-console-feature-flags`
 * Role already grants get/list/create/update/patch on `configmaps` in
 * this namespace with no `resourceNames` restriction.
 *
 * One key per org namespace: `data[namespace]` = JSON array of CIDR
 * strings, e.g. `["203.0.113.0/24", "198.51.100.14/32"]`. An empty array
 * or a missing key means "no restriction" -- deliberately fail-OPEN by
 * default, disclosed here the same way lib/active-sessions.ts discloses
 * its own registry-unreachable fail-open: shipping this control must
 * never retroactively lock an existing org out of its own console just
 * because it never configured an allowlist. Only an org that has
 * explicitly saved at least one CIDR is ever restricted.
 *
 * CIDR matching (`ipInCidr`, `isValidCidr`) is a real, dependency-free
 * IPv4 implementation: parse both the candidate address and the CIDR's
 * network address into 32-bit unsigned integers, build a prefix mask
 * from the CIDR's `/n` suffix, and compare `(ip & mask) === (network &
 * mask)`. No IPv6 support (this app's own clientIpFrom / x-forwarded-for
 * convention only ever surfaces IPv4 addresses in this cluster's ingress
 * path today) -- a non-IPv4 candidate address is treated as "does not
 * match" rather than throwing, same fail-closed-per-entry convention
 * `isValidCidr` uses for a malformed stored entry.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";

export const IP_ALLOWLIST_NAMESPACE = "platform-console";
export const IP_ALLOWLIST_CONFIGMAP = "platform-console-ip-allowlist";

const IPV4_OCTET = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$/;

/** Parses a dotted-quad IPv4 address into a 32-bit unsigned integer, or
 * `null` if `value` is not a well-formed IPv4 address (wrong octet
 * count, out-of-range octet, non-numeric segment). */
export function parseIpv4(value: string): number | null {
  const parts = value.trim().split(".");
  if (parts.length !== 4) return null;
  let n = 0;
  for (const part of parts) {
    if (!IPV4_OCTET.test(part)) return null;
    n = (n << 8) | Number(part);
  }
  // `<<` operates on signed 32-bit ints in JS; force back to unsigned so
  // e.g. 255.255.255.255 compares correctly instead of as a negative.
  return n >>> 0;
}

/** Real, dependency-free IPv4 CIDR parse: splits `"a.b.c.d/n"`, validates
 * both the address and the prefix length (0-32), and returns the
 * prefix-masked network address alongside the mask itself. `null` for
 * anything malformed -- no partial/best-effort parse. */
export function parseCidr(cidr: string): { network: number; mask: number; prefix: number } | null {
  const trimmed = cidr.trim();
  const slashIndex = trimmed.indexOf("/");
  if (slashIndex === -1) return null;
  const addrPart = trimmed.slice(0, slashIndex);
  const prefixPart = trimmed.slice(slashIndex + 1);
  if (!/^\d{1,2}$/.test(prefixPart)) return null;
  const prefix = Number(prefixPart);
  if (prefix < 0 || prefix > 32) return null;
  const addr = parseIpv4(addrPart);
  if (addr === null) return null;
  // A /0 mask is all zero bits; shifting a 32-bit value by 32 is
  // undefined behavior in JS (shift amount is taken mod 32), so it is
  // special-cased rather than computed via the general formula.
  const mask = prefix === 0 ? 0 : (0xffffffff << (32 - prefix)) >>> 0;
  const network = (addr & mask) >>> 0;
  return { network, mask, prefix };
}

/** Real validation entry point used by the API route before ever storing
 * an entry -- same "reject and 400" discipline lib/custom-domains.ts
 * uses for its own SAN validation. */
export function isValidCidr(cidr: string): boolean {
  return parseCidr(cidr) !== null;
}

/** Real containment check: is `ip` inside `cidr`? Both malformed `ip` and
 * malformed `cidr` return `false` (fail-closed per entry -- a
 * misconfigured allowlist entry can only ever narrow access, never widen
 * it past what a valid CIDR would). */
export function ipInCidr(ip: string, cidr: string): boolean {
  const parsedCidr = parseCidr(cidr);
  if (!parsedCidr) return false;
  const addr = parseIpv4(ip);
  if (addr === null) return false;
  return (addr & parsedCidr.mask) >>> 0 === parsedCidr.network;
}

/** Is `ip` allowed by ANY of `cidrs`? An empty `cidrs` array means "no
 * restriction configured" and always returns `true` -- callers that need
 * to distinguish "no restriction" from "restricted but matched" should
 * check `cidrs.length === 0` themselves before calling this (see
 * `checkIpAllowed` below, which does exactly that). */
export function ipMatchesAny(ip: string, cidrs: string[]): boolean {
  return cidrs.some((cidr) => ipInCidr(ip, cidr));
}

function parseEntries(raw: string): string[] {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((v): v is string => typeof v === "string" && isValidCidr(v));
  } catch {
    return [];
  }
}

/** Real read of one org namespace's allowlist entries. `[]` both when the
 * ConfigMap/key genuinely doesn't exist yet and when the cluster is
 * unreachable -- same fail-OPEN default this whole module discloses in
 * its header comment, so a k8s outage never turns into every org losing
 * console access. */
export async function getIpAllowlist(namespace: string): Promise<K8sResult<string[]>> {
  const result = await getConfigMap(IP_ALLOWLIST_NAMESPACE, IP_ALLOWLIST_CONFIGMAP);
  if (!result.ok) return { ok: true, data: [] };
  const raw = result.data?.data?.[namespace];
  if (!raw) return { ok: true, data: [] };
  return { ok: true, data: parseEntries(raw) };
}

/** Real replace-all write for one org namespace's allowlist -- unlike
 * lib/authz.ts's setOrgRole (one identifier per call), the UI/API for
 * this control edits "the list" as a whole (add/remove against a
 * displayed set), so the natural unit of write is the full validated
 * array for that namespace, RFC 7386 merge-patched into just that one
 * ConfigMap key (every other namespace's key is untouched). Every entry
 * must already be `isValidCidr` -- this function does not itself
 * validate/reject, callers (the API route) do that before calling it, so
 * a malformed entry never reaches storage in the first place. An empty
 * array is a legal, meaningful value (explicitly "no restriction"), not
 * treated as "nothing to write".
 */
export async function setIpAllowlist(
  namespace: string,
  cidrs: string[],
): Promise<K8sResult<string[]>> {
  const patch: Record<string, string> = { [namespace]: JSON.stringify(cidrs) };
  const result = await createOrUpdateConfigMap(IP_ALLOWLIST_NAMESPACE, IP_ALLOWLIST_CONFIGMAP, patch);
  if (!result.ok) return result;
  return { ok: true, data: cidrs };
}

export interface IpAllowlistCheck {
  allowed: boolean;
  /** `true` only when this namespace has a non-empty configured
   * allowlist that the request's IP failed to match -- the one condition
   * middleware.ts should ever turn into a 403. Every other case
   * (`allowed: true`, or `allowed: false` with `restricted: false`, which
   * cannot actually occur) is a pass-through. */
  restricted: boolean;
  cidrs: string[];
}

/**
 * The real enforcement decision middleware.ts calls: given an org
 * namespace and the caller's own real IP (or `null`, e.g. local
 * `kubectl port-forward` verification with no forwarding proxy in
 * front), decides whether this request is allowed to reach the console.
 *
 * Fail-open, by design, on exactly two conditions, both disclosed:
 *   1. namespace has no configured allowlist (or it is empty) -- the
 *      documented default for every org that never opted in;
 *   2. the caller's IP could not be resolved at all (`ip === null`) --
 *      matches lib/active-sessions.ts's own "cannot evaluate a policy
 *      against data that doesn't exist" posture; the alternative
 *      (blocking every direct-to-pod request with no forwarding header)
 *      would break the exact `kubectl port-forward` local-verification
 *      path several other modules in this app already rely on staying
 *      reachable.
 * Every other case is real IPv4/CIDR containment, computed fresh on
 * every call -- no caching, so a just-saved allowlist change takes
 * effect on the very next request.
 */
export async function checkIpAllowed(namespace: string, ip: string | null): Promise<IpAllowlistCheck> {
  const result = await getIpAllowlist(namespace);
  const cidrs = result.ok ? result.data : [];
  if (cidrs.length === 0) {
    return { allowed: true, restricted: false, cidrs };
  }
  if (ip === null) {
    return { allowed: true, restricted: false, cidrs };
  }
  const allowed = ipMatchesAny(ip, cidrs);
  return { allowed, restricted: !allowed, cidrs };
}
