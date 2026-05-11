import { test, expect } from "@playwright/test";
import path from "node:path";

const SAMPLE = path.resolve(__dirname, "../../../data/credit_card_transactions_sample_50k.csv");

test("full flow: upload → dashboard → filter → chat → summary", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  const input = page.getByTestId("upload-input");
  await input.setInputFiles(SAMPLE);

  await expect(page.getByTestId("profile-card")).toBeVisible({ timeout: 30_000 });

  // 4-6 charts visible
  await expect.poll(async () =>
    (await page.locator('[data-testid^="chart-"]').count()),
    { timeout: 30_000 }
  ).toBeGreaterThanOrEqual(4);

  const charts = await page.locator('[data-testid^="chart-"]').count();
  expect(charts).toBeLessThanOrEqual(6);

  // Filter — pick the first available filter dropdown if there is one
  const firstFilter = page.locator('[data-testid^="filter-"]').first();
  if (await firstFilter.isVisible().catch(() => false)) {
    const options = firstFilter.locator("option");
    if ((await options.count()) > 1) {
      const value = await options.nth(1).getAttribute("value");
      if (value) {
        const start = Date.now();
        await firstFilter.selectOption(value);
        // Wait until charts re-render (allow up to 5s in real backend)
        await page.waitForTimeout(800);
        expect(Date.now() - start).toBeLessThan(5000);
      }
    }
  }

  // Chat
  await page.getByTestId("chat-input").fill("Which category has the most rows?");
  await page.getByTestId("chat-send").click();
  await expect(page.getByTestId("chat-messages").locator("div").last()).toBeVisible({ timeout: 30_000 });

  // Summary
  const summary = page.getByTestId("summary-text");
  await expect(summary).toBeVisible({ timeout: 60_000 });
  const text = (await summary.textContent()) || "";
  const numericFacts = text.match(/\d+(\.\d+)?/g) || [];
  expect(numericFacts.length).toBeGreaterThanOrEqual(3);
});
