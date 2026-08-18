import { NextResponse } from "next/server";
import { getStatusPageData } from "@/lib/status-page";

// Deliberately no session check -- this route backs the public status page
// (app/app/status/page.tsx), which is listed in middleware.ts's
// PUBLIC_PATHS the same way real hyperscaler status pages (AWS Service
// Health Dashboard, statuspage.io) are reachable with no login. It reports
// only aggregate up/uptime% per component, no secrets, no per-request
// audit-log-worthy admin action.
export const dynamic = "force-dynamic";

export async function GET() {
  const data = await getStatusPageData();
  return NextResponse.json(data, {
    headers: { "cache-control": "no-store" },
  });
}
