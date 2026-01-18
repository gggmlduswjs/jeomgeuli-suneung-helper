import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display main navigation buttons', async ({ page }) => {
    // 메인 네비게이션 버튼 확인
    await expect(page.getByRole('button', { name: /점자학습|학습/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /정보탐색|탐색/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /복습/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /자유변환/i })).toBeVisible();
  });

  test('should navigate to learn page', async ({ page }) => {
    await page.getByRole('button', { name: /점자학습|학습/i }).click();
    await expect(page).toHaveURL(/\/learn/);
  });

  test('should navigate to explore page', async ({ page }) => {
    await page.getByRole('button', { name: /정보탐색|탐색/i }).click();
    await expect(page).toHaveURL(/\/explore/);
  });

  test('should have accessible navigation', async ({ page }) => {
    // 키보드 네비게이션 테스트
    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });
});

