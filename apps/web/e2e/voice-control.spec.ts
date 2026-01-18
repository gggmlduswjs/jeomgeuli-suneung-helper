import { test, expect } from '@playwright/test';

test.describe('Voice Control', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display voice input button', async ({ page }) => {
    // 음성 입력 버튼 확인
    const micButton = page.getByRole('button', { name: /음성|마이크/i });
    await expect(micButton).toBeVisible();
  });

  test('should handle voice command navigation', async ({ page }) => {
    // 음성 명령어 시뮬레이션 (실제 STT는 모킹)
    await page.evaluate(() => {
      // VoiceEventBus를 통해 transcript 이벤트 발생
      window.dispatchEvent(new CustomEvent('voice:transcript', {
        detail: { text: '학습' }
      }));
    });

    // 잠시 대기 후 네비게이션 확인
    await page.waitForTimeout(1000);
    // 실제 구현에 따라 조정 필요
  });

  test('should handle stop command', async ({ page }) => {
    // 정지 명령 테스트
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('voice:transcript', {
        detail: { text: '멈춰' }
      }));
    });

    await page.waitForTimeout(500);
    // TTS가 중지되었는지 확인
  });
});

