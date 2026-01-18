/**
 * 커리큘럼 API 서비스
 */
import { api } from './api';
import type { Curriculum, CurriculumDetail, CurriculumCreate, Subject } from '../types/curriculum';

export const curriculumAPI = {
  /**
   * 커리큘럼 생성
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
   * 커리큘럼 목록 조회
   */
  async list(subject?: Subject): Promise<Curriculum[]> {
    const params = subject ? `?subject=${subject}` : '';
    return api.get<Curriculum[]>(`/curriculum${params}`);
  },

  /**
   * 커리큘럼 상세 조회
   */
  async get(curriculumId: string): Promise<CurriculumDetail> {
    return api.get<CurriculumDetail>(`/curriculum/${curriculumId}`);
  },

  /**
   * 커리큘럼 수정
   */
  async update(curriculumId: string, data: Partial<CurriculumCreate>): Promise<Curriculum> {
    return api.patch<Curriculum>(`/curriculum/${curriculumId}`, data);
  },

  /**
   * 커리큘럼 삭제
   */
  async delete(curriculumId: string): Promise<void> {
    return api.delete(`/curriculum/${curriculumId}`);
  },
};
