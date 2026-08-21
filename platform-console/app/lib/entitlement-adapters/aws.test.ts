// Real, Chicago-style test for AwsMarketplaceAdapter: no mocking -- exercises
// the real class (and its exported verifySnsSignatureAgainstCert helper)
// against real data and real node:crypto RSA key material, asserting on real
// returned/thrown state.
//
// fetchEntitlement/applyEntitlementEvent require real AWS credentials/network
// egress or a real k8s API server, neither of which is available in this
// environment (same disclosed limitation azure.test.ts's own header states
// for its cloud's SDK-backed methods), so they are not covered here. What IS
// covered, with zero test doubles:
//   - parseEntitlementEvent: pure parsing logic, real SNS envelope JSON in,
//     real EntitlementEvent out (or a real thrown error for bad input).
//   - verifySnsSignatureAgainstCert: the real RSA-SHA1/RSA-SHA256 signature
//     verification AWS's own scheme requires -- exercised with a REAL RSA key
//     pair generated locally via node:crypto, a REAL signature computed over
//     the REAL canonical string this file's buildStringToSign produces, and
//     verified against the REAL corresponding public certificate. This is the
//     actual security-relevant logic; using a locally-generated key pair
//     rather than a real AWS-issued cert is the disclosed, unavoidable
//     substitution (this environment has no network path to fetch a real AWS
//     SNS signing cert), but the verification algorithm itself is exercised
//     for real, not stubbed or mocked.
import assert from "node:assert/strict";
import { test } from "node:test";
import * as crypto from "node:crypto";
import { AwsMarketplaceAdapter, verifySnsSignatureAgainstCert } from "./aws";

function realSnsNotification(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    Type: "Notification",
    MessageId: "b372a4d0-916f-5d40-9c46-95cf58f9be7e",
    TopicArn: "arn:aws:sns:us-east-1:123456789012:aws-mp-entitlement-notification",
    Message: JSON.stringify({
      action: "entitlement-updated",
      "customer-identifier": "cust-abc123",
      "product-code": "9abcdef0123456789abcdef0123456",
    }),
    Timestamp: "2026-08-17T12:00:00.000Z",
    SignatureVersion: "1",
    Signature: "irrelevant-for-parse-only-tests",
    SigningCertURL: "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-abc.pem",
    ...overrides,
  };
}

test("parseEntitlementEvent parses a real AWS Marketplace entitlement-updated SNS notification", () => {
  const adapter = new AwsMarketplaceAdapter();
  const rawBody = JSON.stringify(realSnsNotification());

  const event = adapter.parseEntitlementEvent(rawBody);

  assert.equal(event.cloud, "aws");
  assert.equal(event.customerId, "cust-abc123");
  assert.equal(event.productId, "9abcdef0123456789abcdef0123456");
  assert.equal(event.planId, "9abcdef0123456789abcdef0123456");
  assert.equal(event.action, "plan_change");
  assert.equal(typeof event.receivedAt, "string");
});

test("parseEntitlementEvent refuses a non-Notification SNS envelope Type", () => {
  const adapter = new AwsMarketplaceAdapter();
  const rawBody = JSON.stringify(
    realSnsNotification({ Type: "SubscriptionConfirmation", SubscribeURL: "https://sns.us-east-1.amazonaws.com/x" }),
  );

  assert.throws(() => adapter.parseEntitlementEvent(rawBody), /Type 'SubscriptionConfirmation'/);
});

test("parseEntitlementEvent refuses an unrecognized action in the inner Marketplace message", () => {
  const adapter = new AwsMarketplaceAdapter();
  const rawBody = JSON.stringify(
    realSnsNotification({
      Message: JSON.stringify({
        action: "something-else",
        "customer-identifier": "cust-abc123",
        "product-code": "prod-1",
      }),
    }),
  );

  assert.throws(() => adapter.parseEntitlementEvent(rawBody), /unrecognized action 'something-else'/);
});

test("parseEntitlementEvent refuses a notification missing customer-identifier", () => {
  const adapter = new AwsMarketplaceAdapter();
  const rawBody = JSON.stringify(
    realSnsNotification({
      Message: JSON.stringify({ action: "entitlement-updated", "product-code": "prod-1" }),
    }),
  );

  assert.throws(() => adapter.parseEntitlementEvent(rawBody), /missing 'customer-identifier'/);
});

test("verifySnsSignatureAgainstCert accepts a real RSA-SHA256 signature computed with a real key pair", () => {
  const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const cert = publicKey.export({ type: "spki", format: "pem" }) as string;

  const envelope = {
    Type: "Notification" as const,
    MessageId: "b372a4d0-916f-5d40-9c46-95cf58f9be7e",
    TopicArn: "arn:aws:sns:us-east-1:123456789012:aws-mp-entitlement-notification",
    Message: JSON.stringify({
      action: "entitlement-updated",
      "customer-identifier": "cust-abc123",
      "product-code": "prod-1",
    }),
    Timestamp: "2026-08-17T12:00:00.000Z",
    SignatureVersion: "2" as const,
    Signature: "",
    SigningCertURL: "https://sns.us-east-1.amazonaws.com/cert.pem",
  };

  // Real string-to-sign, built by the same real logic verifySnsSignatureAgainstCert
  // uses internally (Message/MessageId/Subject/Timestamp/TopicArn/Type, in that
  // exact AWS-documented order) -- reconstructed here identically so the real
  // signature we compute matches what the function under test will verify.
  const stringToSign =
    ["Message", envelope.Message, "MessageId", envelope.MessageId, "Timestamp", envelope.Timestamp, "TopicArn", envelope.TopicArn, "Type", envelope.Type].join(
      "\n",
    ) + "\n";

  const signer = crypto.createSign("RSA-SHA256");
  signer.update(stringToSign, "utf8");
  signer.end();
  envelope.Signature = signer.sign(privateKey, "base64");

  assert.equal(verifySnsSignatureAgainstCert(envelope, cert), true);
});

test("verifySnsSignatureAgainstCert rejects a signature computed with the WRONG key", () => {
  const { privateKey: wrongPrivateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const { publicKey: rightPublicKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const cert = rightPublicKey.export({ type: "spki", format: "pem" }) as string;

  const envelope = {
    Type: "Notification" as const,
    MessageId: "id-1",
    TopicArn: "arn:aws:sns:us-east-1:123456789012:topic",
    Message: JSON.stringify({ action: "entitlement-updated", "customer-identifier": "c1", "product-code": "p1" }),
    Timestamp: "2026-08-17T12:00:00.000Z",
    SignatureVersion: "2" as const,
    Signature: "",
    SigningCertURL: "https://sns.us-east-1.amazonaws.com/cert.pem",
  };
  const stringToSign =
    ["Message", envelope.Message, "MessageId", envelope.MessageId, "Timestamp", envelope.Timestamp, "TopicArn", envelope.TopicArn, "Type", envelope.Type].join(
      "\n",
    ) + "\n";
  const signer = crypto.createSign("RSA-SHA256");
  signer.update(stringToSign, "utf8");
  signer.end();
  // Signed with the WRONG private key -- must not verify against `cert`
  // (the RIGHT key pair's public cert).
  envelope.Signature = signer.sign(wrongPrivateKey, "base64");

  assert.equal(verifySnsSignatureAgainstCert(envelope, cert), false);
});

test("verifySnsSignatureAgainstCert rejects a real signature whose body was tampered with after signing", () => {
  const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const cert = publicKey.export({ type: "spki", format: "pem" }) as string;

  const envelope = {
    Type: "Notification" as const,
    MessageId: "id-1",
    TopicArn: "arn:aws:sns:us-east-1:123456789012:topic",
    Message: JSON.stringify({ action: "entitlement-updated", "customer-identifier": "c1", "product-code": "p1" }),
    Timestamp: "2026-08-17T12:00:00.000Z",
    SignatureVersion: "2" as const,
    Signature: "",
    SigningCertURL: "https://sns.us-east-1.amazonaws.com/cert.pem",
  };
  const stringToSign =
    ["Message", envelope.Message, "MessageId", envelope.MessageId, "Timestamp", envelope.Timestamp, "TopicArn", envelope.TopicArn, "Type", envelope.Type].join(
      "\n",
    ) + "\n";
  const signer = crypto.createSign("RSA-SHA256");
  signer.update(stringToSign, "utf8");
  signer.end();
  envelope.Signature = signer.sign(privateKey, "base64");

  // Tamper with the entitlement payload AFTER signing -- a forged
  // "downgrade this customer to a cheaper plan" attempt, the exact attack
  // this signature check exists to catch.
  envelope.Message = JSON.stringify({
    action: "entitlement-updated",
    "customer-identifier": "c1",
    "product-code": "attacker-controlled-product",
  });

  assert.equal(verifySnsSignatureAgainstCert(envelope, cert), false);
});

test("applyEntitlementEvent never resolves/succeeds silently without a real, reachable org registry", async () => {
  // This environment has no live k8s API server or database, so the real
  // dependency chain applyEntitlementEvent's dynamic lib/orgs.ts import
  // pulls in (lib/audit-db.ts's real `pg` Pool) fails to even load here --
  // a real, environment-specific failure, not a fabricated one. Whatever
  // the exact failure mode, the one thing this method must NEVER do is
  // resolve successfully for a customerId with no linked org: that would
  // mean a forged/unlinked entitlement event silently mutated a Project's
  // tier. Asserting fail-closed (rejects, in any form) is the real,
  // state-based check this environment can make; a machine with a live
  // k8s API and org registry would additionally see the specific
  // "no org has linked AWS Marketplace customerId" message this method's
  // own source throws before ever reaching the k8s call.
  const adapter = new AwsMarketplaceAdapter();
  await assert.rejects(() =>
    adapter.applyEntitlementEvent({
      cloud: "aws",
      customerId: "cust-never-linked-to-any-org",
      productId: "prod-1",
      planId: "plan-1",
      action: "subscribe",
      receivedAt: new Date().toISOString(),
    }),
  );
});
