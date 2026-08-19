import { NextRequest, NextResponse } from "next/server";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import {
  linkMarketplacePurchase,
  resolveMarketplaceRegistration,
  type MarketplaceProvider,
} from "@/lib/marketplace-runtime";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";

function providerOf(value: string): MarketplaceProvider | null {
  return value === "aws" || value === "azure" || value === "gcp" ? value : null;
}

function failure(error: unknown): NextResponse {
  const message = error instanceof Error ? error.message : String(error);
  if (message.startsWith("REFUSED:")) return NextResponse.json({ error: message }, { status: 400 });
  if (message.startsWith("BLOCKED:")) return NextResponse.json({ error: message }, { status: 503 });
  return NextResponse.json({ error: "BLOCKED:MARKETPLACE_REGISTRATION_FAILURE" }, { status: 500 });
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

  const contentType = request.headers.get("content-type") ?? "";
  let body: Record<string, unknown> = {};
  if (contentType.includes("application/x-www-form-urlencoded")) {
    const form = await request.formData();
    body = Object.fromEntries(Array.from(form.entries()).map(([key, value]) => [key, String(value)]));
  } else {
    body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  }
  const token = String(
    body.token ?? body["x-amzn-marketplace-token"] ?? body["x-ms-marketplace-token"] ?? body["x-gcp-marketplace-token"] ?? "",
  );
  try {
    const purchase = await resolveMarketplaceRegistration(provider, token);
    const binding = await linkMarketplacePurchase(purchase, {
      projectName: String(body.projectName ?? ""),
      namespace: String(body.namespace ?? ""),
      orgId: String(body.orgId ?? ""),
      linkedBy: roleIdentifierFor(session),
    });
    return NextResponse.json({
      status: "linked",
      provider: purchase.provider,
      buyerRef: purchase.buyerRef,
      productRef: purchase.productRef,
      agreementRef: purchase.agreementRef,
      subscriptionRef: purchase.subscriptionRef,
      planRef: purchase.planRef,
      quantity: purchase.quantity,
      binding,
    });
  } catch (error) {
    return failure(error);
  }
}
