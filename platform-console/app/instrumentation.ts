/**
 * Next.js's own server-startup hook (stable, no experimental flag needed
 * on Next 15) -- `register()` runs exactly once per server process, right
 * after the Node.js process boots and before it starts serving requests.
 * Used here to start the real Outbound Webhooks background poller
 * (lib/webhook-poller.ts), which needs a persistent in-process interval,
 * not a per-request code path -- nothing else in this app currently
 * needs process-startup code, so this file exists solely for that.
 */
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { startWebhookPoller } = await import("@/lib/webhook-poller");
    startWebhookPoller();
  }
}
