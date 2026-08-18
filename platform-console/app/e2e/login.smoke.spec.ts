import { test, expect } from "@playwright/test";

/**
 * Trivial real smoke test -- navigates to the real /login page through the
 * real Istio ingress gateway (no dev server, no auth fixture: this test
 * intentionally checks the UNauthenticated page renders) and confirms real
 * heading text is present. Deliberately does not import e2e/fixtures.ts's
 * authed context, since the login page itself is what's under test here.
 * baseURL (playwright.config.ts) already resolves to platform.local via
 * Chromium's --host-resolver-rules launch flag.
 */
test("login page renders the real admin sign-in heading", async ({ page }) => {
  const response = await page.goto("/login");
  expect(response?.ok()).toBeTruthy();
  await expect(page).toHaveTitle(/Platform Console/);
  await expect(
    page.getByRole("heading", { name: "Admin sign-in" }),
  ).toBeVisible();
});
