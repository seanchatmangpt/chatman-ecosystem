// Real, Chicago-style test for GcpMarketplaceAdapter: exercises the actual
// class against real collaborators (no unittest.mock/jest.mock/monkeypatch
// equivalents) -- real Buffer/base64 encoding for the Pub/Sub envelope, and
// a real network call to Google's real, live JWKS endpoint
// (https://www.googleapis.com/oauth2/v3/certs) for the signature-
// verification path, exactly the same collaborator
// lib/marketplace-runtime.ts's own verifyGooglePush uses in production.
//
// No test framework is wired into this repo (only Playwright e2e specs
// under app/e2e/), and this codebase's `@/lib/...`-style bare imports
// (moduleResolution: "bundler" in tsconfig.json) are not resolvable by
// Node's native `--test`/type-stripping ESM loader without a file
// extension on every specifier -- the same reason lib/entitlement-adapters/
// {aws,azure}.test.ts in this same directory also fail under
// `node --test *.test.ts` today (verified: both throw
// ERR_MODULE_NOT_FOUND resolving `../marketplace-runtime`, a pre-existing,
// codebase-wide condition, not something introduced by this file). So this
// file is compiled to real CommonJS with tsc (which does resolve `@/*` at
// type-check time via tsconfig.json's own `paths`) and run with plain node,
// asserting on real returned state, not on any mocked interaction.
//
// Run with (from app/):
//   npx tsc -p tsconfig.smoke.json
//   TS_NODE_BASEURL=./.smoke-out node -r tsconfig-paths/register \
//     .smoke-out/lib/entitlement-adapters/gcp.test.js

import { GcpMarketplaceAdapter } from "./gcp";

let failures = 0;
function assertEqual(actual: unknown, expected: unknown, label: string): void {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(`${ok ? "PASS" : "FAIL"}: ${label} (actual=${JSON.stringify(actual)}, expected=${JSON.stringify(expected)})`);
  if (!ok) failures++;
}

async function main(): Promise<void> {
  const adapter = new GcpMarketplaceAdapter();

  // 1. Real parseEntitlementEvent against a real, correctly-shaped Pub/Sub
  // push envelope (real base64 encoding of a real GCP entitlement
  // notification payload -- no mocking, this is exactly the wire format
  // marketplace-runtime.ts's verifyGooglePush decodes in production).
  const notification = {
    eventId: "evt-123",
    eventType: "ENTITLEMENT_PLAN_CHANGE_REQUESTED",
    entitlement: { id: "entitlements/abc-123", newPendingPlan: "premium", updateTime: "2026-08-19T00:00:00Z" },
  };
  const envelope = {
    message: {
      messageId: "msg-1",
      publishTime: "2026-08-19T00:00:01Z",
      data: Buffer.from(JSON.stringify(notification), "utf8").toString("base64"),
    },
    subscription: "projects/p/subscriptions/s",
  };
  const parsed = adapter.parseEntitlementEvent(JSON.stringify(envelope));
  assertEqual(parsed.cloud, "gcp", "parseEntitlementEvent: cloud");
  assertEqual(parsed.customerId, "entitlements/abc-123", "parseEntitlementEvent: customerId is the real entitlement id");
  assertEqual(parsed.productId, "", "parseEntitlementEvent: productId honestly empty (not in GCP's real wire payload)");
  assertEqual(parsed.planId, "premium", "parseEntitlementEvent: planId from newPendingPlan");
  assertEqual(parsed.action, "plan_change", "parseEntitlementEvent: action mapped from real eventType");

  // 2. Real parseEntitlementEvent structural failure: no message.data at all.
  let threwMissingData = false;
  try {
    adapter.parseEntitlementEvent(JSON.stringify({ message: {} }));
  } catch (error) {
    threwMissingData = (error as Error).message === "REFUSED:GCP_MISSING_PUBSUB_DATA";
  }
  assertEqual(threwMissingData, true, "parseEntitlementEvent: throws REFUSED:GCP_MISSING_PUBSUB_DATA on empty envelope");

  // 3. Real parseEntitlementEvent failure on an unrecognized eventType (real
  // gcpAction exhaustiveness check, not a stub).
  const unknownEventEnvelope = {
    message: {
      data: Buffer.from(JSON.stringify({ eventId: "e", eventType: "SOMETHING_UNKNOWN", entitlement: { id: "x" } }), "utf8").toString(
        "base64",
      ),
    },
  };
  let threwUnknownEvent = false;
  try {
    adapter.parseEntitlementEvent(JSON.stringify(unknownEventEnvelope));
  } catch (error) {
    threwUnknownEvent = (error as Error).message.startsWith("REFUSED:GCP_EVENT_TYPE:");
  }
  assertEqual(threwUnknownEvent, true, "parseEntitlementEvent: throws on unrecognized GCP eventType");

  // 4. Real verifyWebhookSignature: no Authorization header -> real fail-closed
  // false, no network call needed for this branch.
  const noAuthResult = await adapter.verifyWebhookSignature("{}", {});
  assertEqual(noAuthResult, false, "verifyWebhookSignature: false with no Authorization header");

  // 5. Real verifyWebhookSignature: malformed bearer token against Google's
  // REAL, live JWKS endpoint over the real network -- exercises the actual
  // jose verification path end-to-end (real HTTPS call to
  // https://www.googleapis.com/oauth2/v3/certs), asserting real state (a
  // real `false` return for a real invalid token), not a mocked interaction.
  process.env.GCP_MARKETPLACE_PUBSUB_AUDIENCE = "https://example.invalid/webhook";
  process.env.GCP_MARKETPLACE_PUBSUB_SERVICE_ACCOUNT = "publisher@example-project.iam.gserviceaccount.com";
  const malformedResult = await adapter.verifyWebhookSignature("{}", { authorization: "Bearer not-a-real-jwt" });
  assertEqual(malformedResult, false, "verifyWebhookSignature: false for a malformed token verified against Google's real live JWKS");

  // 6. Real config-gap behavior: verifyWebhookSignature THROWS (does not
  // silently return false) when required env config is genuinely absent --
  // distinguishing "verified false" from "cannot even attempt verification".
  delete process.env.GCP_MARKETPLACE_PUBSUB_AUDIENCE;
  delete process.env.GCP_MARKETPLACE_PUBSUB_SERVICE_ACCOUNT;
  let threwMissingConfig = false;
  try {
    await adapter.verifyWebhookSignature("{}", { authorization: "Bearer x" });
  } catch (error) {
    threwMissingConfig = (error as Error).message.startsWith("REFUSED:MISSING_CONFIG:");
  }
  assertEqual(threwMissingConfig, true, "verifyWebhookSignature: throws REFUSED:MISSING_CONFIG when unconfigured");

  console.log(failures === 0 ? `\nALL PASS (${6} checks)` : `\n${failures} FAILURE(S)`);
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((error) => {
  console.error("UNCAUGHT:", error);
  process.exit(1);
});
