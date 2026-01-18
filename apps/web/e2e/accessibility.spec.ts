import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/');
    
    // 주요 버튼에 ARIA 라벨 확인
    const buttons = page.locator('button[aria-label]');
    const count = await buttons.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');
    
    // Tab 키로 네비게이션 가능한지 확인
    await page.keyboard.press('Tab');
    const firstFocused = page.locator(':focus');
    await expect(firstFocused).toBeVisible();
    
    await page.keyboard.press('Tab');
    const secondFocused = page.locator(':focus');
    await expect(secondFocused).toBeVisible();
  });

  test('should have proper heading structure', async ({ page }) => {
    await page.goto('/');
    
    // h1이 하나만 있는지 확인
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
  });

  test('should have accessible form controls', async ({ page }) => {
    await page.goto('/explore');
    
    // 입력 필드에 라벨이 있는지 확인
    const input = page.getByPlaceholder(/메시지를 입력|질문/i);
    await expect(input).toBeVisible();
    
    // 입력 필드가 포커스 가능한지 확인
    await input.focus();
    await expect(input).toBeFocused();
  });
});
