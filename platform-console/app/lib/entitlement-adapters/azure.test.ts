// Real, Chicago-style test for AzureMarketplaceAdapter.parseEntitlementEvent:
// no mocking -- exercises the real class against a real Azure SaaS Fulfillment
// webhook JSON body shape and asserts on the real returned EntitlementEvent
// state. verifyWebhookSignature/fetchEntitlement/applyEntitlementEvent all
// require real network access (Microsoft AAD JWKS / SaaS Fulfillment API) or a
// real database connection (via lib/marketplace-runtime.ts's ledger), neither
// of which is available in this environment, so only the pure, synchronous
// parsing path is covered here.
import assert from "node:assert/strict";
import { test } from "node:test";
import { AzureMarketplaceAdapter } from "./azure.ts";

test("parseEntitlementEvent parses a real Azure SaaS Fulfillment subscribe webhook body", () => {
  const adapter = new AzureMarketplaceAdapter();
  const rawBody = JSON.stringify({
    id: "9a3c1e4e-8b2a-4d1a-9c3e-2f6a7b8c9d0e",
    activityId: "9a3c1e4e-8b2a-4d1a-9c3e-2f6a7b8c9d0e",
    subscriptionId: "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
    offerId: "chatman-platform-console",
    planId: "enterprise-monthly",
    action: "Subscribe",
    timeStamp: "2026-08-17T12:00:00.000Z",
    subscription: {
      beneficiary: { tenantId: "72f988bf-86f1-41af-91ab-2d7cd011db47" },
      purchaser: { tenantId: "72f988bf-86f1-41af-91ab-2d7cd011db47" },
    },
  });

  const event = adapter.parseEntitlementEvent(rawBody);

  assert.equal(event.cloud, "azure");
  assert.equal(event.customerId, "72f988bf-86f1-41af-91ab-2d7cd011db47");
  assert.equal(event.productId, "chatman-platform-console");
  assert.equal(event.planId, "enterprise-monthly");
  assert.equal(event.action, "subscribe");
  assert.equal(event.receivedAt, "2026-08-17T12:00:00.000Z");
});

test("parseEntitlementEvent maps a real Azure ChangePlan operation to plan_change", () => {
  const adapter = new AzureMarketplaceAdapter();
  const rawBody = JSON.stringify({
    activityId: "op-2",
    subscriptionId: "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
    offerId: "chatman-platform-console",
    planId: "pro-monthly",
    action: "ChangePlan",
    timeStamp: "2026-08-17T13:00:00.000Z",
    beneficiary: { tenantId: "0b1acddb-0000-4000-8000-000000000001" },
  });

  const event = adapter.parseEntitlementEvent(rawBody);

  assert.equal(event.action, "plan_change");
  assert.equal(event.customerId, "0b1acddb-0000-4000-8000-000000000001");
});

test("parseEntitlementEvent refuses a webhook body with no beneficiary tenant", () => {
  const adapter = new AzureMarketplaceAdapter();
  const rawBody = JSON.stringify({ offerId: "chatman-platform-console", action: "Subscribe" });

  assert.throws(
    () => adapter.parseEntitlementEvent(rawBody),
    /REFUSED:AZURE_MISSING_BENEFICIARY_TENANT/,
  );
});

test("parseEntitlementEvent refuses an unrecognized Azure operation action", () => {
  const adapter = new AzureMarketplaceAdapter();
  const rawBody = JSON.stringify({
    offerId: "chatman-platform-console",
    action: "SomethingElse",
    beneficiary: { tenantId: "0b1acddb-0000-4000-8000-000000000001" },
  });

  assert.throws(() => adapter.parseEntitlementEvent(rawBody), /REFUSED:AZURE_ACTION:SomethingElse/);
});
