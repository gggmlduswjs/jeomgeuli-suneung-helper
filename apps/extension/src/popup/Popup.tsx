/**
 * Popup UI
 * 최소 UI (모드 설정, on/off)
 */
import { useState, useEffect } from 'react';

export default function Popup() {
  const [lessonId, setLessonId] = useState<string>('');
  const [enabled, setEnabled] = useState<boolean>(true);

  useEffect(() => {
    // Storage에서 설정 로드
    chrome.storage.local.get(['lessonId', 'enabled'], (result) => {
      setLessonId(result.lessonId || '');
      setEnabled(result.enabled !== false);
    });
  }, []);

  const handleSave = () => {
    chrome.storage.local.set({ lessonId, enabled }, () => {
      // Content script에 메시지 전송
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]?.id) {
          chrome.tabs.sendMessage(tabs[0].id, {
            type: 'UPDATE_SETTINGS',
            lessonId,
            enabled,
          });
        }
      });
    });
  };

  return (
    <div style={{ width: '300px', padding: '16px' }}>
      <h2 style={{ marginBottom: '16px' }}>점글이 학습 알림</h2>
      
      <div style={{ marginBottom: '12px' }}>
        <label style={{ display: 'block', marginBottom: '4px' }}>
          강 ID:
        </label>
        <input
          type="text"
          value={lessonId}
          onChange={(e) => setLessonId(e.target.value)}
          placeholder="ls_01"
          style={{ width: '100%', padding: '4px' }}
        />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label>
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
          />
          활성화
        </label>
      </div>

      <button
        onClick={handleSave}
        style={{
          width: '100%',
          padding: '8px',
          backgroundColor: '#4CAF50',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
        }}
      >
        저장
      </button>
    </div>
  );
}
