/**
 * 통합 API 클라이언트
 * 모든 API 서비스를 위한 공통 기반 클래스
 */
import { api, type ApiError } from './api';

export interface ResourceListParams {
  subject?: string;
  book_id?: string;
  [key: string]: any;
}

export interface ResourceCreateParams {
  [key: string]: any;
}

/**
 * 리소스별 CRUD 작업을 위한 기본 클래스
 */
export class ResourceService<T, TCreate = Partial<T>, TUpdate = Partial<T>> {
  constructor(
    private basePath: string,
    private resourceName: string = '리소스'
  ) {}

  /**
   * 목록 조회
   */
  async list(params?: ResourceListParams): Promise<T[]> {
    const queryString = params
      ? '?' + new URLSearchParams(
          Object.entries(params)
            .filter(([_, v]) => v !== undefined && v !== null)
            .map(([k, v]) => [k, String(v)])
        ).toString()
      : '';
    return api.get<T[]>(`${this.basePath}${queryString}`);
  }

  /**
   * 단일 항목 조회
   */
  async get(id: string): Promise<T> {
    return api.get<T>(`${this.basePath}/${id}`);
  }

  /**
   * 생성
   */
  async create(data: TCreate): Promise<T> {
    return api.post<T>(this.basePath, data);
  }

  /**
   * 업데이트
   */
  async update(id: string, data: TUpdate): Promise<T> {
    return api.post<T>(`${this.basePath}/${id}`, data);
  }

  /**
   * 삭제
   */
  async delete(id: string): Promise<void> {
    return api.post<void>(`${this.basePath}/${id}/delete`, {});
  }

  /**
   * FormData를 사용한 생성 (파일 업로드용)
   */
  async createWithFormData(formData: FormData): Promise<T> {
    return api.postFormData<T>(this.basePath, formData);
  }
}

/**
 * 커리큘럼 서비스
 */
import type { Curriculum, CurriculumDetail, Subject } from '../types/curriculum';

export class CurriculumService extends ResourceService<Curriculum> {
  constructor() {
    super('/curriculum', '커리큘럼');
  }

  /**
   * 커리큘럼 상세 조회
   */
  async getDetail(curriculumId: string): Promise<CurriculumDetail> {
    return api.get<CurriculumDetail>(`/curriculum/${curriculumId}`);
  }

  /**
   * 레슨 목록 조회
   */
  async listLessons(curriculumId: string): Promise<any[]> {
    return api.get<any[]>(`/curriculum/${curriculumId}/lessons`);
  }

  /**
   * 특정 레슨 조회
   */
  async getLesson(curriculumId: string, lessonNumber: number): Promise<any> {
    return api.get<any>(`/curriculum/${curriculumId}/lessons/${lessonNumber}`);
  }

  /**
   * 학습 단위 AI 기능
   */
  async generateUnitTTS(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ tts_text: string }> {
    return api.post<{ tts_text: string }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/tts`
    );
  }

  async getUnitSummary(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ summary: string }> {
    return api.post<{ summary: string }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/summary`
    );
  }

  async getUnitLecture(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ explanation: string }> {
    return api.post<{ explanation: string }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/lecture`
    );
  }

  async explainProblem(
    curriculumId: string,
    lessonNumber: number,
    unitId: string
  ): Promise<{ explanation: string }> {
    return api.post<{ explanation: string }>(
      `/curriculum/${curriculumId}/lessons/${lessonNumber}/units/${unitId}/explain`
    );
  }
}

/**
 * 레슨 서비스
 */
import type { Lesson } from '../types/lesson';

export class LessonService extends ResourceService<Lesson> {
  constructor() {
    super('/lessons', '레슨');
  }

  /**
   * 교재의 레슨 목록 조회
   */
  async listByBook(bookId: string): Promise<Lesson[]> {
    return api.get<Lesson[]>(`/books/${bookId}/lessons`);
  }

  /**
   * 강의 대본 조회
   */
  async getScript(lessonId: string) {
    return api.get<{
      lesson_id: string;
      title: string;
      script_text: string;
      estimated_time: number | null;
      key_points: string[];
    }>(`/lessons/${lessonId}/script`);
  }

  /**
   * 레슨 요약
   */
  async getSummary(lessonId: string) {
    return api.get<{
      lesson_id: string;
      summary: string;
      estimated_time: number | null;
    }>(`/lessons/${lessonId}/summary`);
  }
}

/**
 * 학습 단위 서비스
 */
import type { Unit } from '../types/unit';

export class UnitService extends ResourceService<Unit> {
  constructor() {
    super('/units', '학습 단위');
  }

  /**
   * 레슨의 학습 단위 목록 조회
   */
  async listByLesson(lessonId: string): Promise<Unit[]> {
    return api.get<Unit[]>(`/lessons/${lessonId}/units`);
  }
}

/**
 * 교재 서비스
 */
import type { Book, BookParseStatus, Subject, AIProcessingOptions } from '../types/book';

export class BookService extends ResourceService<Book> {
  constructor() {
    super('/books', '교재');
  }

  /**
   * PDF 업로드 및 교재 생성 (AI 옵션 포함)
   */
  async uploadPDF(
    file: File,
    title: string,
    subject: Subject,
    year?: number,
    aiOptions?: AIProcessingOptions
  ): Promise<Book> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('subject', subject);
    if (year) {
      formData.append('year', year.toString());
    }

    // AI 옵션 추가
    if (aiOptions) {
      // Level 1: ML
      if (aiOptions.enable_ml_deduplication !== undefined) {
        formData.append('enable_ml_deduplication', aiOptions.enable_ml_deduplication.toString());
      }
      if (aiOptions.enable_ml_classification !== undefined) {
        formData.append('enable_ml_classification', aiOptions.enable_ml_classification.toString());
      }

      // Level 2: DL
      if (aiOptions.enable_layout_analysis !== undefined) {
        formData.append('enable_layout_analysis', aiOptions.enable_layout_analysis.toString());
      }
      if (aiOptions.enable_math_recognition !== undefined) {
        formData.append('enable_math_recognition', aiOptions.enable_math_recognition.toString());
      }

      // Level 3: LLM
      if (aiOptions.enable_llm_metadata !== undefined) {
        formData.append('enable_llm_metadata', aiOptions.enable_llm_metadata.toString());
      }
      if (aiOptions.enable_llm_explanations !== undefined) {
        formData.append('enable_llm_explanations', aiOptions.enable_llm_explanations.toString());
      }
      if (aiOptions.enable_llm_recommendations !== undefined) {
        formData.append('enable_llm_recommendations', aiOptions.enable_llm_recommendations.toString());
      }
      if (aiOptions.openai_api_key) {
        formData.append('openai_api_key', aiOptions.openai_api_key);
      }
      if (aiOptions.education_level) {
        formData.append('education_level', aiOptions.education_level);
      }
    }

    return api.postFormData<Book>('/books/upload', formData);
  }

  /**
   * HWP 업로드 및 교재 생성
   */
  async uploadHWP(
    file: File,
    title: string,
    subject: Subject,
    year?: number
  ): Promise<Book> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('subject', subject);
    if (year) {
      formData.append('year', year.toString());
    }
    return api.postFormData<Book>('/books/upload-hwp', formData);
  }

  /**
   * 파싱 상태 조회
   */
  async getParseStatus(bookId: string): Promise<BookParseStatus> {
    return api.get<BookParseStatus>(`/books/${bookId}/parse-status`);
  }

  /**
   * 교재 재파싱
   */
  async reparse(bookId: string): Promise<{ ok: boolean; message: string; status: string }> {
    return api.post<{ ok: boolean; message: string; status: string }>(`/books/${bookId}/reparse`);
  }
}

/**
 * 통합 서비스 인스턴스 (하위 호환성을 위한 레거시 API 유지)
 */
export const curriculumService = new CurriculumService();
export const lessonService = new LessonService();
export const unitService = new UnitService();
export const bookService = new BookService();

/**
 * 레거시 API 호환성 (기존 코드가 계속 작동하도록)
 */
export const curriculumAPI = curriculumService;
export const lessonsAPI = lessonService;
export const unitsAPI = unitService;
export const booksAPI = bookService;
