import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const backendDir = path.resolve(__dirname, "../backend");

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `uv run uvicorn app.main:app --port 8000`,
      cwd: backendDir,
      port: 8000,
      timeout: 30_000,
      reuseExistingServer: true,
      env: { ...process.env, MOCK_LLM: "1" },
    },
    {
      command: "npm run dev",
      port: 5173,
      timeout: 30_000,
      reuseExistingServer: true,
    },
  ],
});
