/**
 * 문학/영어 강의 데이터를 Unit 형태로 변환하는 유틸리티
 */
import type { Unit, UnitType } from '../types/unit';

export type SubjectKind = 'literature' | 'english';

interface LiteratureSection {
  title: string;
  type: 'concept' | 'content' | 'work';
  content: string[];
  page?: number;
  content_id?: string;
  /** 영어 등: API에서 제공하는 실제 이미지 경로 (우선 사용) */
  image_path?: string;
}

interface LiteratureProblem {
  problem_id?: string;
  problem_number?: number;
  question_text?: string;
  choices: Record<string, string>;
  correct_answer?: string;
  explanation?: string;
  difficulty?: string;
  points?: number;
  page?: number;
  content?: string[];
  full_text?: string;
}

interface LiteratureLectureData {
  lecture_id: number;
  title: string;
  sections?: LiteratureSection[];
  problems?: (LiteratureProblem | string)[];
  concepts?: any[];
  works?: any[];
}

/**
 * 문학 섹션 타입을 Unit 타입으로 변환
 */
function sectionTypeToUnitType(sectionType: string): UnitType {
  switch (sectionType) {
    case 'concept':
      return 'CONCEPT_CORE';
    case 'content':
    case 'work':
      return 'PASSAGE';
    default:
      return 'CONCEPT_CORE';
  }
}

/**
 * 과목별 강의 데이터를 Unit 배열로 변환
 * 순서: 개념(sections) → 본문(sections) → 문제(problems)
 */
export function convertSubjectLectureToUnits(
  lecture: LiteratureLectureData,
  lectureId: number,
  subject: SubjectKind
): Unit[] {
  const base = subject;
  const units: Unit[] = [];
  let order = 1;

  if (lecture.sections && lecture.sections.length > 0) {
    for (const section of lecture.sections) {
      const unitType = sectionTypeToUnitType(section.type);
      const unitId = `${base}_${lectureId}_section_${order}`;
      const imagePaths: string[] = [];
      if (section.image_path && section.image_path.length > 0) {
        imagePaths.push(section.image_path);
      } else if (section.page) {
        const pageNum = section.page;
        if (section.type === 'concept') {
          imagePaths.push(`/api/data/${base}/concepts_images/concept_p${pageNum}_placeholder.png`);
        } else if (section.type === 'content' || section.type === 'work') {
          imagePaths.push(`/api/data/${base}/content_images/content_p${pageNum}_placeholder.png`);
        }
      }
      const unit = {
        unit_id: unitId,
        lesson_id: `${base}_lecture_${lectureId}`,
        type: unitType,
        title: section.title,
        order: order++,
        content_text: (section.content || []).join('\n'),
        content_image_paths: imagePaths.length > 0 ? imagePaths : undefined,
      } as Unit & { contentId?: string };
      if (section.content_id) unit.contentId = section.content_id;
      units.push(unit);
    }
  }

  if (lecture.problems && Array.isArray(lecture.problems) && lecture.problems.length > 0) {
    if (typeof lecture.problems[0] === 'string') {
      for (let i = 0; i < lecture.problems.length; i++) {
        const problemId = lecture.problems[i] as string;
        const unitId = `${base}_${lectureId}_problem_${order}`;
        const problemNumber = parseInt(problemId, 10) || (i + 1);
        const problemIdStr = String(problemId).padStart(2, '0');
        units.push({
          unit_id: unitId,
          lesson_id: `${base}_lecture_${lectureId}`,
          type: 'QUESTION',
          title: `문제 ${problemNumber}`,
          order: order++,
          question: { stem: `문제 ${problemNumber}`, choices: [], answer: undefined },
        } as Unit & { problemId?: string });
        (units[units.length - 1] as any).problemId = problemIdStr;
      }
    } else {
      for (const problem of lecture.problems as LiteratureProblem[]) {
        const unitId = `${base}_${lectureId}_problem_${problem.problem_id || order}`;
        const choices = Object.entries(problem.choices || {})
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([, text]) => text);
        const answerNumber = parseInt(String(problem.correct_answer), 10) || 1;
        units.push({
          unit_id: unitId,
          lesson_id: `${base}_lecture_${lectureId}`,
          type: 'QUESTION',
          title: problem.problem_number ? `${problem.problem_number}번 문제` : `문제 ${order}`,
          order: order++,
          content_text: problem.question_text || '',
          question: { stem: problem.question_text || '', choices, answer: answerNumber },
        });
      }
    }
  }

  return units;
}

/** 문학 강의 → Unit 변환 (기존 호환) */
export function convertLiteratureLectureToUnits(
  lecture: LiteratureLectureData,
  lectureId: number
): Unit[] {
  return convertSubjectLectureToUnits(lecture, lectureId, 'literature');
}

export function getFirstSubjectUnitId(lectureId: number, subject: SubjectKind): string {
  return `${subject}_${lectureId}_section_1`;
}

export function getFirstLiteratureUnitId(lectureId: number): string {
  return getFirstSubjectUnitId(lectureId, 'literature');
}
