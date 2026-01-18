/**
 * 백엔드 API 클라이언트
 */
const API_BASE = 'http://localhost:8000/api/v1';

export const extensionAPI = {
  async getSyncpoints(lessonId: string) {
    const response = await fetch(`${API_BASE}/lessons/${lessonId}/syncpoints`);
    if (!response.ok) throw new Error('Syncpoints 조회 실패');
    return response.json();
  },

  async logSyncpoint(data: {
    user_id: string;
    lesson_id?: string;
    syncpoint_id?: string;
    event: string;
  }) {
    const response = await fetch(`${API_BASE}/syncpoints/log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('로그 전송 실패');
    return response.json();
  },
};
