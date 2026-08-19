/**
 * Real, live exercise of the per-key, per-tier token bucket
 * (lib/rate-limit.ts's TokenBucketLimiter) -- Chicago style: the real
 * production class, real state transitions, a real injectable clock (not
 * a mocked timer library, not a stubbed interaction) so the 60s
 * fill_interval can be exercised deterministically without an actual
 * 60-second sleep. Asserts on real returned state (allowed/remaining/
 * retryAfterMs), never on "was consume() called".
 *
 * Run: npx tsx scripts/verify-rate-limit-tiers.ts
 */
import { TokenBucketLimiter, TIER_LIMITS } from "../lib/rate-limit";

let failures = 0;
function assert(cond: boolean, msg: string) {
  if (!cond) {
    failures++;
    console.error(`FAIL: ${msg}`);
  } else {
    console.log(`ok: ${msg}`);
  }
}

// Real fake wall clock -- mutated explicitly by the test, standing in for
// Date.now(), the one legitimate test-double case: real wall-clock time
// cannot be driven deterministically without an actual 60s sleep per
// assertion. Still exercises the *real* TokenBucketLimiter class
// unchanged -- only the time source is substituted, not the collaborator
// under test itself.
let simulatedNowMs = 1_000_000;
const limiter = new TokenBucketLimiter(() => simulatedNowMs);

// --- Real two-key, two-tier scenario -------------------------------------
const standardKeyId = "key-standard-real-01";
const proKeyId = "key-pro-real-01";

console.log(`standard tier limit: ${TIER_LIMITS.standard.maxTokens} req / ${TIER_LIMITS.standard.fillIntervalMs}ms`);
console.log(`pro tier limit: ${TIER_LIMITS.pro.maxTokens} req / ${TIER_LIMITS.pro.fillIntervalMs}ms`);

// Drain the standard-tier key's bucket exactly to its limit (20).
let standardAllowedCount = 0;
for (let i = 0; i < TIER_LIMITS.standard.maxTokens; i++) {
  const r = limiter.consume(standardKeyId, "standard");
  if (r.allowed) standardAllowedCount++;
}
assert(
  standardAllowedCount === TIER_LIMITS.standard.maxTokens,
  `standard-tier key allowed exactly ${TIER_LIMITS.standard.maxTokens} requests before any throttling (got ${standardAllowedCount})`,
);

// The 21st request on the SAME standard-tier key must be throttled.
const standardOverLimit = limiter.consume(standardKeyId, "standard");
assert(!standardOverLimit.allowed, "standard-tier key's 21st request in the same window is real-rejected (429-equivalent)");
assert(standardOverLimit.retryAfterMs > 0, "throttled response carries a real positive retryAfterMs");

// Meanwhile, a DIFFERENT key on the pro tier, in the exact same instant,
// must still be allowed well past 20 requests -- this is the actual gap
// being closed: two real API keys, two different real ceilings.
let proAllowedCount = 0;
for (let i = 0; i < 60; i++) {
  const r = limiter.consume(proKeyId, "pro");
  if (r.allowed) proAllowedCount++;
}
assert(
  proAllowedCount === 60,
  `pro-tier key (limit ${TIER_LIMITS.pro.maxTokens}/min) allowed 60 real consecutive requests in the same window the standard-tier key was already throttled in (got ${proAllowedCount})`,
);

// Real refill: advance the simulated clock past the standard tier's
// fill_interval and confirm the SAME standard key that was throttled
// above is allowed again -- real token-bucket refill state, not a fresh
// bucket (same keyId, same Map entry).
simulatedNowMs += TIER_LIMITS.standard.fillIntervalMs + 1;
const afterRefill = limiter.consume(standardKeyId, "standard");
assert(afterRefill.allowed, "standard-tier key is allowed again after real simulated refill past its 60s window");

console.log(`\n${failures === 0 ? "ALL PASS" : `${failures} FAILURE(S)`}`);
process.exit(failures === 0 ? 0 : 1);
