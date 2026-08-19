import { NextResponse } from "next/server";
import { getTrustPageData } from "@/lib/trust-page";

// Deliberately no session check -- this route backs the public Trust page
// (app/app/trust/page.tsx), listed in middleware.ts's PUBLIC_PATHS the
// same way app/app/status/route.ts already is. It reports only aggregate
// CVE-severity counts, aggregate cert-expiry posture, and uptime
// percentages -- lib/trust-page.ts's own module doc comment states exactly
// which per-record fields (secretName, hostname, per-finding CVE detail)
// are deliberately never included here. No secrets, no per-request
// audit-log-worthy admin action. Also includes `egressIpPosture` --
// lib/egress-ips.ts's static, versioned outbound-IP allowlist -- since a
// buyer's InfoSec team needs it during the same procurement review that
// asks for the rest of this page, not gated behind a login.
export const dynamic = "force-dynamic";

export async function GET() {
  const data = await getTrustPageData();
  return NextResponse.json(data, {
    headers: { "cache-control": "no-store" },
  });
}
