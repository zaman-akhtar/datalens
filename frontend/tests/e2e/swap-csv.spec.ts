import { test, expect } from "@playwright/test";
import path from "node:path";

const CC = path.resolve(__dirname, "../../../data/credit_card_transactions_sample_50k.csv");
const AIRBNB = path.resolve(__dirname, "../../../backend/tests/fixtures/airbnb_sample.csv");

test("uploading a different CSV cleanly replaces the dataset", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await page.getByTestId("upload-input").setInputFiles(CC);
  await expect(page.getByTestId("profile-card")).toBeVisible({ timeout: 30_000 });

  // Swap
  await page.locator("summary").getByText("Upload another CSV").click();
  const inputs = page.getByTestId("upload-input");
  await inputs.last().setInputFiles(AIRBNB);
  await expect(page.getByTestId("profile-card")).toContainText("airbnb_sample.csv", { timeout: 30_000 });

  // Credit-card-specific terms must be gone from the visible profile/charts
  const dom = await page.locator("body").innerText();
  expect(dom).not.toContain("merchant");
  expect(dom).not.toContain("is_fraud");
});
