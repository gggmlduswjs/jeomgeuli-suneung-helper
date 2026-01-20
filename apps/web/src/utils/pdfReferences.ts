/**
 * PDF 참조 정보 파싱 유틸리티
 * 중복된 pdf_references 파싱 로직을 통합
 */

export interface PDFReference {
  block_id?: string;
  page?: number;
  position?: string;
}

/**
 * pdf_references를 파싱하여 block_id 추출
 */
export function parsePDFReferences(pdfReferences: any): {
  blockId: string | null;
  pdfRefs: PDFReference | PDFReference[] | null;
} {
  let pdfRefs: PDFReference | PDFReference[] | null = null;
  let blockId: string | null = null;

  if (pdfReferences) {
    try {
      if (typeof pdfReferences === 'string') {
        pdfRefs = JSON.parse(pdfReferences);
      } else {
        pdfRefs = pdfReferences;
      }

      if (Array.isArray(pdfRefs) && pdfRefs.length > 0) {
        blockId = pdfRefs[0]?.block_id || null;
      } else if (typeof pdfRefs === 'object' && pdfRefs !== null) {
        blockId = pdfRefs.block_id || null;
      }
    } catch (e) {
      console.warn('[PDF References] 파싱 실패:', e);
    }
  }

  return { blockId, pdfRefs };
}

/**
 * 과목을 이미지 경로용 형식으로 변환
 */
function normalizeSubjectForPath(subject: string): string {
  const subjectLower = subject.toLowerCase();
  // Subject enum 값 (KOREAN, MATH, ENGLISH)을 폴더명 형식으로 변환
  const mapping: Record<string, string> = {
    'korean': 'korean',
    'math': 'math',
    'english': 'english',
    'literature': 'korean',  // literature는 korean 폴더 사용
    'math1': 'math',  // math1은 math 폴더 사용
  };
  return mapping[subjectLower] || subjectLower;
}

/**
 * 이미지 경로 생성
 * Vite 프록시를 통해 백엔드 API로 요청이 전달되도록 상대 경로 사용
 */
export function buildImagePath(
  blockId: string,
  subject: string,
  lessonNumber: number | string
): string {
  const lessonNum = String(lessonNumber).padStart(2, '0');
  const normalizedSubject = normalizeSubjectForPath(subject);
  
  // Vite 프록시를 통해 백엔드로 요청이 전달되도록 상대 경로 사용
  // vite.config.ts에서 /api/v1을 http://localhost:8000으로 프록시 설정됨
  const imagePath = `/api/v1/captures/${normalizedSubject}/lesson_${lessonNum}/${blockId}.png`;
  
  return imagePath;
}
