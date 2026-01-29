/**
 * 영어 강의를 Unit 형태로 로드하는 훅
 */
import { useState, useCallback } from 'react';
import { englishAPI } from '../services/english';
import { convertSubjectLectureToUnits } from '../utils/literatureUnitConverter';
import type { Unit } from '../types/unit';
import { createModuleLogger } from '../utils/logger';

const logger = createModuleLogger('EnglishUnitData');

const SUBJECT = 'english';

async function enhanceUnitImages(units: Unit[]): Promise<void> {
  try {
    const conceptImages = await englishAPI.getConceptImages();
    const contentImages = await englishAPI.getContentImages();
    const problemImages = await englishAPI.getProblemImages();

    for (const unit of units) {
      const firstPath = unit.content_image_paths?.[0] ?? '';

      // API의 section.image_path 등으로 이미 실제 경로가 있는 경우: 목록에 있으면 유지
      if (firstPath && !firstPath.includes('_placeholder')) {
        const list =
          unit.type === 'CONCEPT_CORE'
            ? conceptImages
            : unit.type === 'PASSAGE'
              ? contentImages
              : unit.type === 'QUESTION'
                ? problemImages
                : [];
        const exists = list.includes(firstPath);
        if (exists) {
          logger.log(`이미지 경로 유지: ${unit.title}`);
          continue;
        }
        unit.content_image_paths = undefined;
        logger.debug(`이미지 목록에 없음(제거): ${unit.title} - ${firstPath}`);
        continue;
      }

      let matchedImages: string[] = [];
      let pageNum: number | null = null;
      if (unit.content_image_paths?.length) {
        const m = unit.content_image_paths[0].match(/p(\d{1,3})/);
        if (m) pageNum = parseInt(m[1], 10);
      }
      if (!pageNum) {
        unit.content_image_paths = undefined;
        continue;
      }

      const pageStr2 = pageNum.toString().padStart(2, '0');
      const pageStr3 = pageNum.toString().padStart(3, '0');
      const pageStrRaw = pageNum.toString();
      const imageNumber = unit.order.toString().padStart(2, '0');

      if (unit.type === 'CONCEPT_CORE') {
        matchedImages = conceptImages.filter((img) => {
          const fn = img.split('/').pop() || '';
          const pm = fn.includes(`concept_p${pageStr2}_`) || fn.includes(`concept_p${pageStr3}_`) || fn.includes(`concept_p${pageStrRaw}_`);
          const nm = fn.includes(`_${imageNumber}.png`);
          return pm && nm;
        });
        if (!matchedImages.length) {
          matchedImages = conceptImages.filter((img) => {
            const fn = img.split('/').pop() || '';
            return (fn.includes(`concept_p${pageStr2}_`) || fn.includes(`concept_p${pageStr3}_`) || fn.includes(`concept_p${pageStrRaw}_`)) && fn.includes('_01.png');
          });
        }
      } else if (unit.type === 'PASSAGE') {
        const contentId = (unit as any).contentId as string | undefined;
        if (contentId) {
          const norm = contentId.startsWith('p') ? contentId : `p${contentId}`;
          matchedImages = contentImages.filter((img) => (img.split('/').pop() || '') === `content_${norm}.png`);
        }
        if (!matchedImages.length) {
          matchedImages = contentImages.filter((img) => {
            const fn = img.split('/').pop() || '';
            const pm = fn.includes(`content_p${pageStr2}_`) || fn.includes(`content_p${pageStr3}_`) || fn.includes(`content_p${pageStrRaw}_`);
            const nm = fn.includes(`_${imageNumber}.png`);
            return pm && nm;
          });
          if (!matchedImages.length) {
            matchedImages = contentImages.filter((img) => {
              const fn = img.split('/').pop() || '';
              return (fn.includes(`content_p${pageStr2}_`) || fn.includes(`content_p${pageStr3}_`) || fn.includes(`content_p${pageStrRaw}_`)) && fn.includes('_01.png');
            });
          }
        }
      } else if (unit.type === 'QUESTION') {
        let problemId: string | null = (unit as any).problemId ?? null;
        if (!problemId && unit.content_image_paths?.length) {
          const pm = unit.content_image_paths[0].match(/problem_p\d+_(\d+)_placeholder/);
          if (pm) problemId = pm[1];
        }
        if (problemId) {
          matchedImages = problemImages.filter((img) => {
            const fn = img.split('/').pop() || '';
            const pm = fn.includes(`problem_p${pageStr2}_`) || fn.includes(`problem_p${pageStr3}_`) || fn.includes(`problem_p${pageStrRaw}_`);
            const nm = fn.includes(`_${problemId}.png`);
            return pm && nm;
          });
        }
        if (!matchedImages.length) {
          matchedImages = problemImages.filter((img) => {
            const fn = img.split('/').pop() || '';
            return fn.includes(`problem_p${pageStr2}_`) || fn.includes(`problem_p${pageStr3}_`) || fn.includes(`problem_p${pageStrRaw}_`);
          });
          if (matchedImages.length > 1) matchedImages = [matchedImages[0]];
        }
      }

      if (matchedImages.length) {
        unit.content_image_paths = matchedImages;
        logger.log(`이미지 매칭 성공: ${unit.title} - ${matchedImages.length}개`);
      } else {
        unit.content_image_paths = undefined;
        logger.debug(`이미지 매칭 실패: ${unit.title} (페이지 ${pageNum})`);
      }
    }
  } catch (e) {
    logger.warn('이미지 경로 보완 실패:', e);
  }
}

export interface UseEnglishUnitDataReturn {
  unit: Unit | null;
  allUnits: Unit[];
  lectureTitle: string;
  loading: boolean;
  error: string | null;
  loadLecture: (lectureId: number) => Promise<void>;
  loadUnit: (unitId: string) => void;
  reset: () => void;
}

export function useEnglishUnitData(): UseEnglishUnitDataReturn {
  const [unit, setUnit] = useState<Unit | null>(null);
  const [allUnits, setAllUnits] = useState<Unit[]>([]);
  const [lectureTitle, setLectureTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLecture = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const lecture = await englishAPI.getLecture(id);
      setLectureTitle(lecture.title);

      let problemsData: any[] = [];
      if (lecture.problems?.length) {
        if (typeof lecture.problems[0] === 'string') {
          const loaded = await Promise.all(
            (lecture.problems as string[]).map((pid) => englishAPI.getProblem(pid).catch(() => null))
          );
          problemsData = loaded.filter(Boolean);
        } else {
          problemsData = lecture.problems as any[];
        }
      }

      const lectureWithProblems = { ...lecture, problems: problemsData } as any;
      let units = convertSubjectLectureToUnits(lectureWithProblems, id, 'english');

      if (problemsData.length) {
        const problemUnits = units.filter((u) => u.type === 'QUESTION');
        for (let i = 0; i < Math.min(problemsData.length, problemUnits.length); i++) {
          const p = problemsData[i];
          const pu = problemUnits[i];
          if (!p || !pu?.question) continue;
          const choices = Object.entries(p.choices || {})
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([, t]) => String(t));
          const answerNumber = parseInt(p.correct_answer ?? '', 10) || 1;
          pu.title = `문제 ${i + 1}`;
          pu.content_text = p.question_text ?? p.question;
          pu.question = { stem: p.question_text ?? p.question ?? '', choices, answer: answerNumber };
          if (p.page) {
            const pid = p.problem_id ?? String(i + 1).padStart(2, '0');
            const pagePadded = String(p.page).padStart(2, '0');
            pu.content_image_paths = [`/api/data/${SUBJECT}/problems_images/problem_p${pagePadded}_${pid}_placeholder.png`];
            (pu as any).problemId = pid;
          }
        }
      }

      await enhanceUnitImages(units);
      setAllUnits(units);
      if (units.length) setUnit(units[0]);
    } catch (e) {
      logger.error('영어 강의 로드 실패:', e);
      setError(e instanceof Error ? e.message : '강의를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUnit = useCallback((unitId: string) => {
    const u = allUnits.find((x) => x.unit_id === unitId);
    if (u) setUnit(u);
    else logger.warn(`Unit 없음: ${unitId}`);
  }, [allUnits]);

  const reset = useCallback(() => {
    setUnit(null);
    setAllUnits([]);
    setLectureTitle('');
    setError(null);
  }, []);

  return { unit, allUnits, lectureTitle, loading, error, loadLecture, loadUnit, reset };
}

export default useEnglishUnitData;
