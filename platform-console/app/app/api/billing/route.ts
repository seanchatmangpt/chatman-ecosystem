import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getInvoicePreview } from "@/lib/invoice-preview";

// Same platform-namespace roster the /billing page uses.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

// Fixed allowlist of windows, not an open passthrough -- the window label
// gets interpolated straight into a PromQL range-vector selector inside
// lib/invoice-preview.ts, so an arbitrary client-supplied string is the
// same PromQL-injection surface /api/prometheus's ALLOWED_QUERIES guards
// against.
const ALLOWED_WINDOWS: Record<string, number> = {
  "1h": 1,
  "6h": 6,
  "24h": 24,
};

// Illustrative cost-preview calculation over real metered Prometheus data
// (AWS Cost Explorer "forecasted bill" equivalent) -- calculation and
// visibility only, no payment processor, no card data, no real financial
// obligation. See lib/invoice-preview.ts for the real arithmetic.
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const windowLabel = request.nextUrl.searchParams.get("window") ?? "1h";
  const windowHours = ALLOWED_WINDOWS[windowLabel];
  if (windowHours === undefined) {
    return NextResponse.json(
      { error: `window not in allowlist: ${Object.keys(ALLOWED_WINDOWS).join(", ")}` },
      { status: 400 },
    );
  }

  const preview = await getInvoicePreview(PLATFORM_NAMESPACES, windowLabel, windowHours);

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "GET",
    path: "/api/billing",
    status: 200,
    requestId,
  });

  return NextResponse.json(preview);
}
