import { NextRequest, NextResponse } from "next/server";
import {
  acknowledgeMarketplaceEntitlement,
  applyMarketplaceEntitlementEvent,
  authenticateMarketplaceEntitlement,
  type MarketplaceProvider,
} from "@/lib/marketplace-runtime";

function providerOf(value: string): MarketplaceProvider | null {
  return value === "aws" || value === "azure" || value === "gcp" ? value : null;
}

function failure(error: unknown): NextResponse {
  const message = error instanceof Error ? error.message : String(error);
  if (message.startsWith("REFUSED:")) return NextResponse.json({ error: message }, { status: 403 });
  if (message.startsWith("BLOCKED:")) return NextResponse.json({ error: message }, { status: 503 });
  return NextResponse.json({ error: "BLOCKED:MARKETPLACE_WEBHOOK_FAILURE" }, { status: 500 });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ provider: string }> },
) {
  const provider = providerOf((await params).provider);
  if (!provider) return NextResponse.json({ error: "REFUSED:UNKNOWN_PROVIDER" }, { status: 404 });
  const rawBody = await request.text();
  let event: Awaited<ReturnType<typeof authenticateMarketplaceEntitlement>> | null = null;
  try {
    event = await authenticateMarketplaceEntitlement(provider, rawBody, request.headers);
    const result = await applyMarketplaceEntitlementEvent(event);
    await acknowledgeMarketplaceEntitlement(event, true);
    return NextResponse.json({ status: result.duplicate ? "replayed" : "applied", eventId: event.eventId });
  } catch (error) {
    if (event) {
      const reason = error instanceof Error ? error.message : String(error);
      await acknowledgeMarketplaceEntitlement(event, false, reason).catch(() => {});
    }
    return failure(error);
  }
}
