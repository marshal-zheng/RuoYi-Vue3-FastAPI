import { defineConfig, devices } from "@playwright/test";

const baseURL =
  process.env.DEMO_OFFLINE_E2E_BASE_URL || "http://127.0.0.1:4173";

export default defineConfig({
  testDir: "tests/e2e/demo-offline",
  testIgnore: "page-state/**",
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: {
    timeout: 15_000,
  },
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  outputDir: "tests/reports/demo-offline-e2e",
  reporter: [
    ["list"],
    [
      "html",
      {
        outputFolder: "tests/reports/demo-offline-e2e-html",
        open: "never",
      },
    ],
  ],
  use: {
    baseURL,
    actionTimeout: 15_000,
    navigationTimeout: 45_000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
});
