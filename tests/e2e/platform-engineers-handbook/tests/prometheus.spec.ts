import { test, expect } from '@playwright/test';

const PROM_URL = 'http://localhost:18301';

test('JTBD: run a PromQL query in the Prometheus web UI and see real results', async ({ page }) => {
  await page.goto(`${PROM_URL}/query`, { waitUntil: 'domcontentloaded' });

  // Modern Prometheus UI: query input is an ARIA role="textbox" (CodeMirror-based editor)
  const queryBox = page.getByRole('textbox').first();
  await expect(queryBox).toBeVisible({ timeout: 15000 });
  await queryBox.click();
  await queryBox.fill('up');
  await queryBox.press('Enter');

  // Wait for either the table or graph result area to populate
  await page.waitForTimeout(2000);

  // Try to find the "Execute" button if Enter didn't submit
  const execBtn = page.getByRole('button', { name: /execute/i });
  if (await execBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await execBtn.click();
  }

  await page.waitForTimeout(2000);

  const bodyText = await page.locator('body').innerText();
  // A real "up" query result includes label names like "job=" and a value of "1" or "0"
  expect(bodyText).toMatch(/job\s*=|instance\s*=/i);

  await page.screenshot({ path: '/tmp/peh-playwright/prometheus-query.png', fullPage: true });
});
