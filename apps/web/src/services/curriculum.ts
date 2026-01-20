/**
 * 커리큘럼 API 서비스
 */
import { api } from './api';
import type { Curriculum, CurriculumDetail, CurriculumCreate, Subject } from '../types/curriculum';

export const curriculumAPI = {
  /**
   * 커리큘럼 목록 조회 (사용자용)
   */
  async list(subject?: Subject, bookId?: string): Promise<Curriculum[]> {
    const params = new URLSearchParams();
    if (subject) params.append('subject', subject);
    if (bookId) params.append('book_id', bookId);
    const queryString = params.toString();
    return api.get<Curriculum[]>(`/curriculum${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * 커리큘럼 상세 조회 (사용자용)
   */
  async get(curriculumId: string): Promise<CurriculumDetail> {
    return api.get<CurriculumDetail>(`/curriculum/${curriculumId}`);
  },

  /**
   * 커리큘럼의 레슨 목록 조회 (사용자용)
   */
  async listLessons(curriculumId: string): Promise<any[]> {
    return api.get<any[]>(`/curriculum/${curriculumId}/lessons`);
  },

  /**
   * 커리큘럼의 특정 레슨 조회 (사용자용)
   */
  async getLesson(curriculumId: string, lessonNumber: number): Promise<any> {
    return api.get<any>(`/curriculum/${curriculumId}/lessons/${lessonNumber}`);
  },

  /**
   * 학습 단위의 TTS 텍스트를 AI로 생성 (강의 대본 기반)
   */
  async generateUnitTTS(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ tts_text: string }> {
    return api.post<{ tts_text: string }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/tts`
    );
  },

  /**
   * 학습 단위 요약 (본문 읽기용)
   */
  async getUnitSummary(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ summary: string }> {
    return api.post<{ summary: string }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/summary`
    );
  },

  /**
   * 학습 단위 강의식 설명 (강의해줘용)
   */
  async getUnitLecture(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ explanation: string }> {
    return api.post<{ explanation: string }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/lecture`
    );
  },

  /**
   * 문제 설명 (문제 설명해줘용)
   */
  async explainProblem(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ explanation: string }> {
    return api.post<{ explanation: string }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/explain`
    );
  },

  /**
   * 이미지에서 OCR로 텍스트 추출
   */
  async extractTextFromImage(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ ok: boolean; extracted_text: string; problem_text?: string; choices?: string[]; blocks_count: number }> {
    return api.post<{ ok: boolean; extracted_text: string; problem_text?: string; choices?: string[]; blocks_count: number }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/extract-text`
    );
  },

  // 아래 함수들은 관리자용 (프론트엔드에서 사용 안 함)
  // 관리자가 백엔드 API를 직접 호출하거나 스크립트로 처리
  
  /**
   * 커리큘럼 생성 (관리자용 - 프론트엔드에서 사용 안 함)
   * @deprecated 사용자용이 아님. 관리자가 백엔드에서 직접 처리
   */
  async generate(
    subject: Subject,
    title: string,
    hwpFiles: File[],
    pdfFile?: File,
    bookId?: string
  ): Promise<Curriculum> {
    const formData = new FormData();
    formData.append('subject', subject);
    formData.append('title', title);
    if (bookId) {
      formData.append('book_id', bookId);
    }
    
    hwpFiles.forEach((file) => {
      formData.append('hwp_files', file);
    });
    
    if (pdfFile) {
      formData.append('pdf_file', pdfFile);
    }
    
    return api.postFormData<Curriculum>('/curriculum/generate', formData);
  },

  /**
   * 커리큘럼 수정 (관리자용 - 프론트엔드에서 사용 안 함)
   * @deprecated 사용자용이 아님. 관리자가 백엔드에서 직접 처리
   */
  async update(curriculumId: string, data: Partial<CurriculumCreate>): Promise<Curriculum> {
    return api.patch<Curriculum>(`/curriculum/${curriculumId}`, data);
  },

  /**
   * 커리큘럼 삭제 (관리자용 - 프론트엔드에서 사용 안 함)
   * @deprecated 사용자용이 아님. 관리자가 백엔드에서 직접 처리
   */
  async delete(curriculumId: string): Promise<void> {
    return api.delete(`/curriculum/${curriculumId}`);
  },
};
