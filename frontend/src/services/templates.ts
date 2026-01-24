/**
 * 템플릿 관리 API 서비스
 */
import { api } from './api';

export interface ParsingTemplate {
  name: string;
  subject: string;
  version: string;
  description: string;
  patterns: {
    lecture_title_patterns?: string[];
    toc_lecture_patterns?: string[];
    concept_title_patterns?: string[];
    content_header_patterns?: string[];
    section_title_patterns?: string[];
    problem_number_pattern?: string;
  };
  config: {
    toc_end_page?: number;
    start_content_page?: number;
    paragraph_y_threshold?: number;
    unit_order?: string[];
    is_lecture_based?: boolean;
    lecture_units?: string[];
    region_hints?: {
      [key: string]: {
        y_min?: number;
        y_max?: number;
      };
    };
    region_text_examples?: {
      [key: string]: string[];
    };
    region_image_examples?: {
      [key: string]: unknown[];
    };
    toc_text?: string;
    toc_lecture_list?: Array<{
      lecture_id: number;
      title: string;
      start_page?: number | null;
      end_page?: number | null;
      source?: string;
    }>;
    lecture_page_ranges?: {
      [key: string]: {
        start_page: number;
        end_page?: number;
      };
    };
    font_info?: {
      [key: string]: {
        size?: number;
        weight?: string;
        family?: string;
      };
    };
    layout_info?: {
      header_height?: number;
      footer_height?: number;
      margin?: {
        top?: number;
        bottom?: number;
        left?: number;
        right?: number;
      };
      column_count?: number;
      content_area?: {
        x_min?: number;
        x_max?: number;
        y_min?: number;
        y_max?: number;
      };
    };
    problem_patterns?: {
      number_format?: string;
      number_position?: string;
      answer_format?: string;
      answer_position?: string;
      problem_separator?: string;
      example_numbers?: string[];
    };
    section_spacing?: {
      concept_to_passage?: number;
      passage_to_problem?: number;
      problem_to_problem?: number;
      min_section_height?: number;
      max_section_height?: number;
    };
  };
  confidence: number;
  sample_texts?: string[];
  stats?: {
    total_lectures?: number;
    lectures_with_pages?: number;
    total_patterns?: number;
    has_region_hints?: boolean;
    has_region_text_examples?: boolean;
    has_region_image_examples?: boolean;
    toc_text_length?: number;
  };
  created_at?: string;
  updated_at?: string;
  _summary?: {
    total_lectures?: number;
    lectures_with_pages?: number;
    toc_text_length?: number;
    toc_text_preview?: string;
    has_region_hints?: boolean;
    region_hints_labels?: string[];
    has_region_text_examples?: boolean;
    region_text_examples_labels?: string[];
    region_text_examples_count?: number;
    has_region_image_examples?: boolean;
    region_image_examples_labels?: string[];
    region_image_examples_count?: number;
  };
}

export interface TemplateTestResult {
  ok: boolean;
  confidence: number;
  matches: {
    lecture_title: string[];
    problem_number: string[];
    concept_title: string[];
    section_title: string[];
  };
  sample_text: string;
}

export interface PatternDetectionResult {
  ok: boolean;
  detected_patterns: {
    lecture_title_patterns: string[];
    problem_number_patterns: string[];
    concept_title_patterns: string[];
  };
  sample_lines: string[];
}

export interface ParsingGuideRegion {
  page: number;
  label: string; // 'concept' | 'passage' | 'problem'
  bbox: [number, number, number, number]; // [x_min, y_min, x_max, y_max]
}

export interface CurriculumStructureSurvey {
  is_lecture_based: boolean;
  lecture_units: string[];
  unit_order: string[];
}

export interface GenerateTemplateFromTOCRequest {
  subject: string;
  name: string;
  version?: string;
  description?: string;
  year?: number;
  book_name?: string;
  toc_text: string;
  curriculum_survey?: CurriculumStructureSurvey;
  parsing_guide_regions?: ParsingGuideRegion[];
  toc_lecture_line_examples: string[];
  toc_nonlecture_line_examples?: string[];
  expected_lecture_count?: number;
  toc_lecture_list?: Array<{
    lecture_id: number;
    title: string;
    start_page: number | null;
    end_page: number | null;
  }>;
  save?: boolean;
  model_name?: string;
  confidence?: number;
  defaults?: {
    toc_end_page?: number;
    start_content_page?: number;
    paragraph_y_threshold?: number;
    [key: string]: unknown;
  };
}

export interface GenerateTemplateFromTOCResponse {
  ok: boolean;
  template: ParsingTemplate & { _notes?: string[] };
  saved: boolean;
  file_path: string | null;
  validation?: unknown;
}

export const templatesAPI = {
  /**
   * 템플릿 목록 조회
   */
  async list(subject?: string): Promise<ParsingTemplate[]> {
    const url = subject ? `/templates?subject=${subject}` : '/templates';
    return api.get<ParsingTemplate[]>(url);
  },

  /**
   * 템플릿 상세 조회
   */
  async get(subject: string, name: string): Promise<ParsingTemplate> {
    return api.get<ParsingTemplate>(`/templates/${subject}/${name}`);
  },

  /**
   * 템플릿 생성
   */
  async create(template: ParsingTemplate): Promise<{ ok: boolean; message: string; template: ParsingTemplate }> {
    return api.post<{ ok: boolean; message: string; template: ParsingTemplate }>('/templates', template);
  },

  /**
   * 템플릿 수정
   */
  async update(subject: string, name: string, template: Partial<ParsingTemplate>): Promise<{ ok: boolean; message: string; template: ParsingTemplate }> {
    return api.put<{ ok: boolean; message: string; template: ParsingTemplate }>(`/templates/${subject}/${name}`, template);
  },

  /**
   * 템플릿 삭제
   */
  async delete(subject: string, name: string): Promise<{ ok: boolean; message: string }> {
    return api.delete<{ ok: boolean; message: string }>(`/templates/${subject}/${name}`);
  },

  /**
   * 템플릿 복사
   */
  async copy(subject: string, name: string, newName?: string, newVersion?: string): Promise<{ ok: boolean; message: string; template: ParsingTemplate }> {
    return api.post<{ ok: boolean; message: string; template: ParsingTemplate }>(`/templates/${subject}/${name}/copy`, {
      new_name: newName,
      new_version: newVersion
    });
  },

  /**
   * 템플릿 테스트
   */
  async test(subject: string, name: string, sampleText: string): Promise<TemplateTestResult> {
    return api.post<TemplateTestResult>(`/templates/${subject}/${name}/test`, {
      sample_text: sampleText
    });
  },

  /**
   * 패턴 자동 감지 (AI 보조)
   */
  async detectPatterns(sampleText: string, subject: string): Promise<PatternDetectionResult> {
    return api.post<PatternDetectionResult>('/templates/detect-patterns', {
      sample_text: sampleText,
      subject
    });
  },

  /**
   * 목차(TOC) 텍스트로 템플릿 자동 생성 (GPT)
   * - 기본은 preview(미저장)
   * - save=true면 서버에서 즉시 저장까지 수행
   */
  async generateFromToc(req: GenerateTemplateFromTOCRequest): Promise<GenerateTemplateFromTOCResponse> {
    return api.post<GenerateTemplateFromTOCResponse>('/templates/generate-from-toc', req);
  },

  /**
   * PDF에서 영역별 텍스트 예시 자동 추출
   */
  async extractTextExamples(
    pdfFile: File,
    subject: string,
    regionHints: { [key: string]: { y_min: number; y_max: number } },
    samplePages?: number[],
    parsingGuideRegions?: ParsingGuideRegion[]
  ): Promise<{
    ok: boolean;
    region_text_examples: { [key: string]: string[] };
    pages_processed: number;
    total_examples: number;
  }> {
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    formData.append('subject', subject);
    formData.append('region_hints', JSON.stringify(regionHints));
    if (samplePages && samplePages.length > 0) {
      formData.append('sample_pages', samplePages.join(','));
    }
    if (parsingGuideRegions && parsingGuideRegions.length > 0) {
      formData.append('parsing_guide_regions', JSON.stringify(parsingGuideRegions));
    }

    return api.postFormData<{
      ok: boolean;
      region_text_examples: { [key: string]: string[] };
      pages_processed: number;
      total_examples: number;
    }>('/templates/extract-text-examples', formData);
  },

  /**
   * 목차 텍스트에서 강의 목록 및 페이지 범위 추출
   */
  async parseTocLectures(tocText: string): Promise<{
    ok: boolean;
    lectures: Array<{
      lecture_id: number;
      title: string;
      start_page: number | null;
      end_page: number | null;
    }>;
    total_lectures: number;
    lectures_with_pages: number;
  }> {
    return api.post<{
      ok: boolean;
      lectures: Array<{
        lecture_id: number;
        title: string;
        start_page: number | null;
        end_page: number | null;
      }>;
      total_lectures: number;
      lectures_with_pages: number;
    }>('/templates/parse-toc-lectures', { toc_text: tocText });
  },
};
