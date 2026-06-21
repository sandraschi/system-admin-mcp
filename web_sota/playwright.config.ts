import { defineConfig } from '@playwright/test';
export default defineConfig({
    testDir: './e2e', timeout: 60000, retries: 1,
    use: { baseURL: 'http://localhost:10860', headless: true, screenshot: 'only-on-failure' },
    webServer: {
        command: 'uv run python -m system_admin_mcp.server --port 10861',
        port: 10861, timeout: 30000, reuseExistingServer: false
    }
});
