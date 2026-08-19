import { NextRequest, NextResponse } from "next/server";
import { requireRole } from "@/lib/authz";
import { reportMarketplaceUsage, type MarketplaceProvider, type MarketplaceUsage } from "@/lib/marketplace-runtime";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";

function providerOf(value: string): MarketplaceProvider | null {
  return value === "aws" || value === "azure" || value === "gcp" ? value : null;
}

function failure(error: unknown): NextResponse {
  const message = error instanceof Error ? error.message : String(error);
  if (message.startsWith("REFUSED:")) return NextResponse.json({ error: message }, { status: 400 });
  if (message.startsWith("BLOCKED:")) return NextResponse.json({ error: message }, { status: 503 });
  return NextResponse.json({ error: "BLOCKED:MARKETPLACE_USAGE_FAILURE" }, { status: 500 });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ provider: string }> },
) {
  const provider = providerOf((await params).provider);
  if (!provider) return NextResponse.json({ error: "REFUSED:UNKNOWN_PROVIDER" }, { status: 404 });
  const sessionToken = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = sessionToken ? await verifySessionToken(sessionToken) : null;
  if (!session) return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  const access = await requireRole(session, "owner");
  if (!access.ok) return access.response!;
  const body = (await request.json().catch(() => null)) as Partial<MarketplaceUsage> | null;
  if (!body) return NextResponse.json({ error: "REFUSED:INVALID_JSON" }, { status: 400 });
  const usage: MarketplaceUsage = {
    provider,
    eventId: String(body.eventId ?? ""),
    buyerRef: String(body.buyerRef ?? ""),
    agreementRef: String(body.agreementRef ?? ""),
    subscriptionRef: String(body.subscriptionRef ?? ""),
    planRef: String(body.planRef ?? ""),
    dimension: String(body.dimension ?? ""),
    units: Number(body.units ?? 0),
    startTime: String(body.startTime ?? ""),
    endTime: String(body.endTime ?? ""),
    sourceReceipt: String(body.sourceReceipt ?? ""),
    ...(body.usageReportingId ? { usageReportingId: String(body.usageReportingId) } : {}),
  };
  try {
    const result = await reportMarketplaceUsage(usage);
    return NextResponse.json({ status: result.duplicate ? "replayed" : "accepted", ...result });
  } catch (error) {
    return failure(error);
  }
}
