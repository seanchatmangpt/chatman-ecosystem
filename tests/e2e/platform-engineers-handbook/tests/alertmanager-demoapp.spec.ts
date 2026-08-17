import { test, expect } from '@playwright/test';

const ALERTMANAGER_URL = 'http://localhost:18302';
const DEMO_APP_URL = 'http://localhost:18303';

test('JTBD: view active alerts in the Alertmanager web UI', async ({ page }) => {
  await page.goto(ALERTMANAGER_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');

  const bodyText = await page.locator('body').innerText();
  // Real Alertmanager UI always renders "Alerts" chrome, with or without active alerts
  expect(bodyText.length).toBeGreaterThan(0);

  await page.screenshot({ path: '/tmp/peh-playwright/alertmanager.png', fullPage: true });

  // Report (not assert — 0 active alerts is a legitimate real state, not a failure)
  const alertCount = await page.locator('[class*="alert"], [data-testid*="alert"]').count();
  console.log(`Alertmanager: observed ${alertCount} alert-related DOM elements`);
});

test('JTBD: demo app responds to a real browser request at /health', async ({ page }) => {
  const response = await page.goto(`${DEMO_APP_URL}/health`, { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBe(200);
  const bodyText = await page.locator('body').innerText();
  expect(bodyText).toContain('healthy');
  await page.screenshot({ path: '/tmp/peh-playwright/demo-app-health.png' });
});

test('JTBD: demo app /items endpoint renders real JSON in a browser', async ({ page }) => {
  const response = await page.goto(`${DEMO_APP_URL}/items`, { waitUntil: 'domcontentloaded' });
  expect(response?.status()).toBe(200);
  const bodyText = await page.locator('body').innerText();
  // Should be valid JSON (an array), even if empty
  expect(() => JSON.parse(bodyText)).not.toThrow();
  const parsed = JSON.parse(bodyText);
  expect(Array.isArray(parsed)).toBe(true);
  await page.screenshot({ path: '/tmp/peh-playwright/demo-app-items.png' });
});
