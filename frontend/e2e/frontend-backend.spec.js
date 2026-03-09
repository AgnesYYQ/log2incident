import { test, expect } from '@playwright/test';

// Requires running services:
// 1) Backend API: http://localhost:8000
// 2) Frontend Vite app: http://localhost:5173
// 3) Redis + Postgres for product APIs

test('frontend-to-backend login and product fetch', async ({ page }) => {
  await page.goto('/');

  await page.getByLabel('Username').fill('demo');
  await page.getByLabel('Password').fill('demo123');
  await page.getByRole('button', { name: 'Sign In' }).click();

  await expect(page.getByRole('heading', { name: 'Product Pricing Desk' })).toBeVisible();
  await expect(page.getByText('Products (Postgres + Redis)')).toBeVisible();
});
