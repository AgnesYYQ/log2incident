import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL: process.env.FRONTEND_BASE_URL || 'http://localhost:5173',
    headless: true,
  },
});
