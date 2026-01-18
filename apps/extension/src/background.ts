/**
 * Background Service Worker
 * 알림 스케줄러 및 로그 관리
 */

// 설치 시
chrome.runtime.onInstalled.addListener(() => {
  console.log('[Extension] 점글이 학습 알림 확장 프로그램이 설치되었습니다.');
});

// 메시지 리스너 (popup/content script와 통신)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'LOG_SYNCPOINT') {
    // 로그 전송 (content script에서 처리하므로 여기서는 로깅만)
    console.log('[Extension] Syncpoint log:', message.data);
  }
  return true;
});
