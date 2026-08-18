/**
 * Tiny shared helper: resolves the real client IP a request arrived with,
 * used only for lib/active-sessions.ts's registry rows (`ip` is informational
 * -- shown on /sessions, never itself an authorization input). Prefers the
 * first hop in a real `x-forwarded-for` (this app always runs behind the
 * Istio Gateway -- see middleware.ts -- so the direct TCP peer is the mesh
 * sidecar, never the real client), falling back to `x-real-ip`. `null` when
 * neither header is present (e.g. a direct `kubectl port-forward` during
 * local verification) rather than fabricating a value.
 */
import type { NextRequest } from "next/server";

export function clientIpFrom(request: NextRequest): string | null {
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    const first = forwardedFor.split(",")[0]?.trim();
    if (first) return first;
  }
  return request.headers.get("x-real-ip");
}

/**
 * Whether the session cookie should carry the `Secure` attribute.
 *
 * Every session-issuing route in this app used to hardcode
 * `secure: process.env.NODE_ENV === "production"`. That is wrong for this
 * app's actual deployment shape: it runs behind the Istio Gateway (see
 * middleware.ts, k8s/gateway.yaml), and NODE_ENV is "production" in the
 * real deployed pod (a standard Next.js standalone build) regardless of
 * whether the Gateway's HTTPS:443 listener is actually usable -- and on
 * this cluster it currently isn't (k8s/gateway.yaml's own header comment:
 * no `platform-console-tls` secret exists yet, so only HTTP:80 works).
 * The result was a real, severe defect: every login (local-admin, GoTrue,
 * OIDC) issued a Secure-flagged cookie that no browser will ever send back
 * over the only currently-working plain-HTTP origin, so authenticated
 * requests always looked unauthenticated post-login -- confirmed live via
 * the Playwright E2E suite, every authed page falling back to the login
 * screen despite a real 200 from /api/login.
 *
 * Fixed to reflect the actual edge protocol instead of the build mode:
 * `x-forwarded-proto`, the header Istio's ingress gateway sets to the
 * client-facing scheme for every request it proxies (this app never sees
 * real external traffic any other way -- see clientIpFrom's identical
 * "always runs behind the Istio Gateway" reasoning above). Falls back to
 * the request's own perceived protocol for the direct
 * `kubectl port-forward` / local-dev case where no proxy sets that header.
 * This makes HTTPS-only cookies simply start working the moment
 * `platform-console-tls` exists and the Gateway's 443 listener is used,
 * with no further code change required.
 */
export function isSecureRequest(request: NextRequest): boolean {
  const forwardedProto = request.headers.get("x-forwarded-proto");
  if (forwardedProto) {
    return forwardedProto.split(",")[0]?.trim().toLowerCase() === "https";
  }
  return request.nextUrl.protocol === "https:";
}
