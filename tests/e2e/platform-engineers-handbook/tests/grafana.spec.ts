import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const GRAFANA_URL = 'http://localhost:18300';
const password = readFileSync('/tmp/grafana-pw.txt', 'utf-8').trim();

test('JTBD: log into Grafana and view a live dashboard with real data', async ({ page }) => {
  await page.goto(GRAFANA_URL, { waitUntil: 'domcontentloaded' });

  // Log in
  const userInput = page.locator('input[name="user"]');
  await expect(userInput).toBeVisible({ timeout: 15000 });
  await userInput.fill('admin');
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole('button', { name: /log in/i }).click();

  // Skip "change password" prompt if shown
  const skipBtn = page.getByRole('button', { name: /skip/i });
  if (await skipBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await skipBtn.click();
  }

  // Confirm logged in: home/dashboard chrome should be visible
  await expect(page).not.toHaveURL(/login/i, { timeout: 15000 });

  // Navigate to Dashboards list
  await page.goto(`${GRAFANA_URL}/dashboards`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('a[href*="/d/"]', { timeout: 15000 });

  const dashboardLinks = page.locator('a[href*="/d/"]');
  const count = await dashboardLinks.count();
  expect(count).toBeGreaterThan(0);

  // Open the first real dashboard
  const href = await dashboardLinks.first().getAttribute('href');
  await page.goto(`${GRAFANA_URL}${href}`, { waitUntil: 'domcontentloaded' });

  // A real dashboard should render panel containers
  await page.waitForSelector('[data-testid*="panel"], .panel-container, [class*="panel"]', { timeout: 20000 });
  const panelCount = await page.locator('[data-testid*="panel"], .panel-container, [class*="panel"]').count();
  expect(panelCount).toBeGreaterThan(0);

  await page.screenshot({ path: '/tmp/peh-playwright/grafana-dashboard.png', fullPage: true });
});
