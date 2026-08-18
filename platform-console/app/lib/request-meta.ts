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
