import { test as base, expect, request, type APIRequestContext } from "@playwright/test";
import fs from "fs";
import path from "path";

/**
 * Real authenticated fixture -- performs a real POST /api/login against the
 * live gateway (the exact request app/app/login/page.tsx's AdminLoginForm
 * itself issues) and reuses the resulting `platform_console_session`
 * cookie across tests via Playwright's storageState pattern. No auth
 * mocking: every test run does a real login against the real deployed pod.
 *
 * Host routing: unlike browser navigation (see playwright.config.ts's long
 * comment on why `--host-resolver-rules` is used there), a plain
 * `APIRequestContext` request DOES accept a real `Host` header override
 * via `extraHTTPHeaders` -- confirmed live -- so this fixture takes the
 * simpler path of hitting the NodePort IP directly with an explicit Host
 * header, no browser/DNS trick needed.
 */

const nodePortIp = `${process.env.E2E_BASE_HOST ?? "127.0.0.1"}:${process.env.E2E_BASE_PORT ?? "31594"}`;
const hostHeader = process.env.E2E_HOST_HEADER ?? "platform.local";
const adminUsername = process.env.E2E_ADMIN_USERNAME ?? "admin";
const adminPassword = process.env.E2E_ADMIN_PASSWORD;

async function realAdminLogin(): Promise<APIRequestContext> {
  if (!adminPassword) {
    throw new Error(
      "E2E_ADMIN_PASSWORD is not set. Set it in the gitignored .env.local " +
        "(see playwright.config.ts's header comment) -- this fixture never " +
        "hardcodes a real credential.",
    );
  }
  const context = await request.newContext({
    baseURL: `http://${nodePortIp}`,
    extraHTTPHeaders: { Host: hostHeader },
  });
  const res = await context.post("/api/login", {
    data: { username: adminUsername, password: adminPassword },
  });
  if (!res.ok()) {
    throw new Error(
      `Real login against http://${nodePortIp}/api/login failed: ${res.status()} ${await res.text()}`,
    );
  }
  return context;
}

export const test = base.extend<object, { authedStorageState: string }>({
  // Worker-scoped: one real login per worker (workers: 1 in this config,
  // so effectively one real login per whole run), then every test in the
  // worker reuses the resulting cookie via storageState.
  authedStorageState: [
    async ({}, use) => {
      const context = await realAdminLogin();
      // The real login happened against the bare NodePort IP (see
      // realAdminLogin's own comment on why), so the cookie
      // Playwright records is domain-scoped to that IP. Browser tests
      // navigate to http://platform.local:<port>/ instead (Chromium's
      // --host-resolver-rules trick, see playwright.config.ts), so the
      // cookie's domain is rewritten here to match -- otherwise a real
      // browser navigation to platform.local would never send it.
      const state = await context.storageState();
      for (const cookie of state.cookies) {
        cookie.domain = hostHeader;
      }
      const storageStatePath = path.resolve(__dirname, "../.auth/admin-storage-state.json");
      fs.mkdirSync(path.dirname(storageStatePath), { recursive: true });
      fs.writeFileSync(storageStatePath, JSON.stringify(state, null, 2));
      await context.dispose();
      await use(storageStatePath);
    },
    { scope: "worker" },
  ],

  storageState: async ({ authedStorageState }, use) => {
    await use(authedStorageState);
  },
});

export { expect };
