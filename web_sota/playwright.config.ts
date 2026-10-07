import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: "http://localhost:10860",
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: "uv run system-admin-mcp --web",
      url: "http://127.0.0.1:10861/api/health",
      timeout: 90000,
      reuseExistingServer: true,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:10860",
      timeout: 90000,
      reuseExistingServer: true,
    },
  ],
});
