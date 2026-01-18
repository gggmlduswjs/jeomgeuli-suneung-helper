/**
 * Content Script
 * 플레이어 DOM 감지 및 시간 동기화, 알림 포인트 처리
 */

// API 기본 URL
const API_BASE = 'http://localhost:8000/api/v1';

// 현재 강 ID (popup에서 설정)
let currentLessonId: string | null = null;
let syncpoints: Array<{ syncpoint_id: string; timestamp_sec: number; hint_type?: string }> = [];
let isEnabled = true;

// 플레이어 감지
function detectPlayer(): { element: HTMLElement | null; getCurrentTime: () => number } | null {
  // YouTube
  const youtubePlayer = document.querySelector('video');
  if (youtubePlayer) {
    return {
      element: youtubePlayer,
      getCurrentTime: () => youtubePlayer.currentTime,
    };
  }

  // EBS 등 다른 플레이어
  const video = document.querySelector('video');
  if (video) {
    return {
      element: video,
      getCurrentTime: () => video.currentTime,
    };
  }

  return null;
}

// Syncpoints 로드
async function loadSyncpoints(lessonId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/lessons/${lessonId}/syncpoints`);
    if (response.ok) {
      const data = await response.json();
      syncpoints = data;
      console.log('[Extension] Syncpoints loaded:', syncpoints.length);
    }
  } catch (error) {
    console.error('[Extension] Syncpoints 로드 실패:', error);
  }
}

// 알림 로그 전송
async function logSyncpoint(syncpointId: string, event: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/syncpoints/log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'u_demo',
        lesson_id: currentLessonId,
        syncpoint_id: syncpointId,
        event,
      }),
    });
  } catch (error) {
    console.error('[Extension] 로그 전송 실패:', error);
  }
}

// 띵동 재생
function playBeep(): void {
  const audio = new Audio(chrome.runtime.getURL('src/audio/beep.mp3'));
  audio.play().catch(console.error);
}

// 힌트 재생 (TTS 또는 음성 파일)
function playHint(hintType?: string): void {
  // TTS 사용 또는 음성 파일 재생
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(`힌트: ${hintType || '알림'}`);
    utterance.lang = 'ko-KR';
    window.speechSynthesis.speak(utterance);
  }
}

// 메인 루프
function startMonitoring(): void {
  const player = detectPlayer();
  if (!player || !currentLessonId || !isEnabled) {
    return;
  }

  const checkInterval = setInterval(() => {
    if (!isEnabled || !currentLessonId) {
      clearInterval(checkInterval);
      return;
    }

    const currentTime = player.getCurrentTime();
    
    // Syncpoints 확인
    for (const sp of syncpoints) {
      // 알림 타이밍 (0.5초 오차 허용)
      if (Math.abs(currentTime - sp.timestamp_sec) < 0.5) {
        playBeep();
        if (sp.hint_type) {
          playHint(sp.hint_type);
        }
        logSyncpoint(sp.syncpoint_id, 'BEEP_PLAYED');
        
        // 한 번만 재생하도록 제거
        syncpoints = syncpoints.filter(s => s.syncpoint_id !== sp.syncpoint_id);
      }
    }
  }, 100); // 100ms마다 체크
}

// Storage에서 설정 읽기
chrome.storage.local.get(['lessonId', 'enabled'], (result) => {
  currentLessonId = result.lessonId || null;
  isEnabled = result.enabled !== false;
  
  if (currentLessonId) {
    loadSyncpoints(currentLessonId).then(() => {
      startMonitoring();
    });
  }
});

// Storage 변경 감지
chrome.storage.onChanged.addListener((changes) => {
  if (changes.lessonId) {
    currentLessonId = changes.lessonId.newValue;
    if (currentLessonId) {
      loadSyncpoints(currentLessonId);
    }
  }
  if (changes.enabled !== undefined) {
    isEnabled = changes.enabled.newValue;
  }
});

console.log('[Extension] Content script loaded');
