import { test, expect } from '@playwright/test';

test.describe('Explore Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/explore');
  });

  test('should display input field', async ({ page }) => {
    const input = page.getByPlaceholder(/메시지를 입력|질문/i);
    await expect(input).toBeVisible();
  });

  test('should submit query and display answer', async ({ page }) => {
    // API 모킹 설정
    await page.route('**/api/explore/', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: '테스트 답변입니다.',
          news: [],
          query: '테스트',
          ok: true,
        }),
      });
    });

    const input = page.getByPlaceholder(/메시지를 입력|질문/i);
    await input.fill('테스트 질문');
    await input.press('Enter');

    // 답변 표시 확인
    await expect(page.getByText(/테스트 답변/i)).toBeVisible({ timeout: 10000 });
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // 에러 응답 모킹
    await page.route('**/api/explore/', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'internal_error',
          detail: '서버 오류',
        }),
      });
    });

    const input = page.getByPlaceholder(/메시지를 입력|질문/i);
    await input.fill('테스트');
    await input.press('Enter');

    // 에러 메시지 확인
    await expect(page.getByText(/오류|에러/i)).toBeVisible({ timeout: 5000 });
  });
});

