/**
 * 문학 강의를 Unit 형태로 로드하는 훅
 */
import { useState, useCallback } from 'react';
import { literatureAPI } from '../services/literature';
import { convertLiteratureLectureToUnits, getFirstLiteratureUnitId } from '../utils/literatureUnitConverter';
import type { Unit } from '../types/unit';
import { createModuleLogger } from '../utils/logger';

const logger = createModuleLogger('LiteratureUnitData');

/**
 * Unit의 이미지 경로를 실제 이미지 목록과 매칭하여 보완
 */
async function enhanceUnitImages(units: Unit[]): Promise<void> {
  try {
    // 개념 이미지 목록 가져오기
    const conceptImages = await literatureAPI.getConceptImages();
    const contentImages = await literatureAPI.getContentImages();
    const problemImages = await literatureAPI.getProblemImages();
    
    // 각 Unit의 이미지 경로 보완
    for (const unit of units) {
      let matchedImages: string[] = [];
      
      // 현재 경로에서 페이지 번호 추출 (2자리 또는 3자리)
      let pageNum: number | null = null;
      if (unit.content_image_paths && unit.content_image_paths.length > 0) {
        const currentPath = unit.content_image_paths[0];
        // p{숫자} 패턴 매칭 (2자리 또는 3자리, 또는 placeholder)
        const pageMatch = currentPath.match(/p(\d{1,3})/);
        if (pageMatch) {
          pageNum = parseInt(pageMatch[1], 10);
        }
      }
      
      // 페이지 번호가 없으면 스킵
      if (!pageNum) {
        // placeholder 경로 제거
        unit.content_image_paths = undefined;
        continue;
      }
      
      // 페이지 번호를 문자열로 변환 (2자리와 3자리 모두 매칭)
      const pageStr2 = pageNum.toString().padStart(2, '0'); // "08", "11"
      const pageStr3 = pageNum.toString().padStart(3, '0'); // "008", "011"
      const pageStrRaw = pageNum.toString(); // "8", "11"
      
      // Unit의 order를 기반으로 이미지 번호 매칭
      // 같은 페이지의 여러 섹션이 있을 수 있으므로, order를 기반으로 이미지 번호 결정
      // 예: order=1 → _01.png, order=2 → _02.png
      const imageNumber = unit.order.toString().padStart(2, '0');
      
      if (unit.type === 'CONCEPT_CORE') {
        // 개념 이미지: concept_p{page}_{number}.png 패턴 매칭
        // order 기반으로 특정 이미지만 선택
        matchedImages = conceptImages.filter(img => {
          const fileName = img.split('/').pop() || '';
          // concept_p08_01, concept_p008_01, concept_p8_01 등 매칭
          const pageMatch = fileName.includes(`concept_p${pageStr2}_`) || 
                           fileName.includes(`concept_p${pageStr3}_`) ||
                           fileName.includes(`concept_p${pageStrRaw}_`);
          // 이미지 번호도 매칭 (order 기반)
          const numberMatch = fileName.includes(`_${imageNumber}.png`);
          return pageMatch && numberMatch;
        });
        
        // 매칭 실패 시 첫 번째 이미지만 선택 (fallback)
        if (matchedImages.length === 0) {
          matchedImages = conceptImages.filter(img => {
            const fileName = img.split('/').pop() || '';
            return (fileName.includes(`concept_p${pageStr2}_`) || 
                    fileName.includes(`concept_p${pageStr3}_`) ||
                    fileName.includes(`concept_p${pageStrRaw}_`)) &&
                   fileName.includes('_01.png');
          });
        }
      } else if (unit.type === 'PASSAGE') {
        // content_id가 있으면 해당 이미지 직접 사용 (예: p09_01 → content_p09_01.png)
        const contentId = (unit as any).contentId as string | undefined;
        if (contentId) {
          const normalized = contentId.startsWith('p') ? contentId : `p${contentId}`;
          matchedImages = contentImages.filter(img => {
            const fileName = img.split('/').pop() || '';
            return fileName === `content_${normalized}.png`;
          });
        }
        // content_id 없으면 기존 페이지+order 매칭
        if (matchedImages.length === 0) {
          matchedImages = contentImages.filter(img => {
            const fileName = img.split('/').pop() || '';
            const pageMatch = fileName.includes(`content_p${pageStr2}_`) || 
                             fileName.includes(`content_p${pageStr3}_`) ||
                             fileName.includes(`content_p${pageStrRaw}_`);
            const numberMatch = fileName.includes(`_${imageNumber}.png`);
            return pageMatch && numberMatch;
          });
          if (matchedImages.length === 0) {
            matchedImages = contentImages.filter(img => {
              const fileName = img.split('/').pop() || '';
              return (fileName.includes(`content_p${pageStr2}_`) || 
                      fileName.includes(`content_p${pageStr3}_`) ||
                      fileName.includes(`content_p${pageStrRaw}_`)) &&
                     fileName.includes('_01.png');
            });
          }
        }
      } else if (unit.type === 'QUESTION') {
        // 문제 이미지: problem_p{page}_{problem_id}.png 패턴 매칭
        // 문제 Unit의 경우, problemId 메타데이터 또는 placeholder 경로에서 추출
        let problemId: string | null = null;
        
        // 메타데이터에서 problemId 가져오기
        if ((unit as any).problemId) {
          problemId = (unit as any).problemId;
        } else if (unit.content_image_paths && unit.content_image_paths.length > 0) {
          // placeholder 경로에서 problem_id 추출
          // 예: problem_p9_01_placeholder.png → 01
          const pathMatch = unit.content_image_paths[0].match(/problem_p\d+_(\d+)_placeholder/);
          if (pathMatch) {
            problemId = pathMatch[1];
          }
        }
        
        // 문제 이미지 매칭
        if (problemId) {
          matchedImages = problemImages.filter(img => {
            const fileName = img.split('/').pop() || '';
            const pageMatch = fileName.includes(`problem_p${pageStr2}_`) || 
                             fileName.includes(`problem_p${pageStr3}_`) ||
                             fileName.includes(`problem_p${pageStrRaw}_`);
            // 문제 번호 매칭 (problem_p09_01.png 형식)
            const numberMatch = fileName.includes(`_${problemId}.png`);
            return pageMatch && numberMatch;
          });
        }
        
        // 매칭 실패 시 페이지 번호만으로 매칭 (fallback)
        if (matchedImages.length === 0) {
          matchedImages = problemImages.filter(img => {
            const fileName = img.split('/').pop() || '';
            return fileName.includes(`problem_p${pageStr2}_`) || 
                   fileName.includes(`problem_p${pageStr3}_`) ||
                   fileName.includes(`problem_p${pageStrRaw}_`);
          });
          // 여러 이미지가 있으면 첫 번째만 선택
          if (matchedImages.length > 1) {
            matchedImages = [matchedImages[0]];
          }
        }
      }
      
      // 매칭된 이미지가 있으면 업데이트
      if (matchedImages.length > 0) {
        unit.content_image_paths = matchedImages;
        logger.log(`이미지 매칭 성공: ${unit.title} - ${matchedImages.length}개 이미지`);
      } else {
        // 매칭 실패 시 이미지 경로 제거
        unit.content_image_paths = undefined;
        logger.warn(`이미지 매칭 실패: ${unit.title} (페이지 ${pageNum})`);
      }
    }
  } catch (err) {
    logger.warn('이미지 경로 보완 실패:', err);
    // 실패해도 기본 경로는 유지
  }
}

export interface UseLiteratureUnitDataReturn {
  unit: Unit | null;
  allUnits: Unit[];
  lectureTitle: string;
  loading: boolean;
  error: string | null;
  loadLecture: (lectureId: number) => Promise<void>;
  loadUnit: (unitId: string) => Promise<void>;
  reset: () => void;
}

/**
 * 문학 강의를 Unit 형태로 로드하는 훅
 */
export function useLiteratureUnitData(): UseLiteratureUnitDataReturn {
  const [unit, setUnit] = useState<Unit | null>(null);
  const [allUnits, setAllUnits] = useState<Unit[]>([]);
  const [lectureTitle, setLectureTitle] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lectureId, setLectureId] = useState<number | null>(null);

  const loadLecture = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    setLectureId(id);

    try {
      // 강의 데이터 로드
      const lecture = await literatureAPI.getLecture(id);
      setLectureTitle(lecture.title);

      // 문제 데이터 로드 (problems가 문자열 배열인 경우)
      let problemsData: any[] = [];
      if (lecture.problems && Array.isArray(lecture.problems) && lecture.problems.length > 0) {
        if (typeof lecture.problems[0] === 'string') {
          // 문제 ID 배열인 경우, 각 문제 상세 정보 로드
          const problemPromises = lecture.problems.map((problemId: string) =>
            literatureAPI.getProblem(problemId).catch(() => null)
          );
          const loadedProblems = await Promise.all(problemPromises);
          problemsData = loadedProblems.filter(p => p !== null);
        } else {
          problemsData = lecture.problems;
        }
      }

      // 강의 데이터에 문제 데이터 병합
      const lectureWithProblems = {
        ...lecture,
        problems: problemsData,
      };

      // Unit 배열로 변환
      let units = convertLiteratureLectureToUnits(lectureWithProblems, id);
      
      // 문제 데이터가 로드된 경우, 문제 Unit 업데이트
      if (problemsData.length > 0) {
        const problemUnits = units.filter(u => u.type === 'QUESTION');
        for (let i = 0; i < Math.min(problemsData.length, problemUnits.length); i++) {
          const problem = problemsData[i];
          const problemUnit = problemUnits[i];
          
          if (problem && problemUnit && problemUnit.question) {
            // choices를 배열로 변환
            const choices = Object.entries(problem.choices || {})
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([, text]) => text);
            
            // correct_answer를 숫자로 변환
            const answerNumber = parseInt(problem.correct_answer) || 1;
            
            problemUnit.title = `문제 ${i + 1}`;
            problemUnit.content_text = problem.question_text;
            problemUnit.question = {
              stem: problem.question_text,
              choices: choices,
              answer: answerNumber,
            };
            
            // 문제 이미지 경로는 enhanceUnitImages에서 처리
            // 여기서는 페이지 번호와 problem_id 저장
            if (problem.page) {
              const pageNum = problem.page;
              const problemId = problem.problem_id || String(i + 1).padStart(2, '0');
              const pagePadded = String(pageNum).padStart(2, '0');
              problemUnit.content_image_paths = [
                `/api/data/literature/problems_images/problem_p${pagePadded}_${problemId}_placeholder.png`
              ];
              // problem_id를 메타데이터로 저장 (enhanceUnitImages에서 사용)
              (problemUnit as any).problemId = problemId;
            }
          }
        }
      }
      
      // 섹션 이미지 경로 보완 (페이지 번호 기반으로 실제 이미지 찾기)
      await enhanceUnitImages(units);
      
      setAllUnits(units);

      // 첫 번째 Unit 로드
      if (units.length > 0) {
        setUnit(units[0]);
      }
    } catch (err) {
      logger.error('문학 강의 로드 실패:', err);
      const errorMsg = err instanceof Error ? err.message : '강의를 불러오지 못했습니다.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUnit = useCallback((unitId: string) => {
    const foundUnit = allUnits.find(u => u.unit_id === unitId);
    if (foundUnit) {
      setUnit(foundUnit);
    } else {
      logger.warn(`Unit을 찾을 수 없습니다: ${unitId}`);
    }
  }, [allUnits]);

  const reset = useCallback(() => {
    setUnit(null);
    setAllUnits([]);
    setLectureTitle('');
    setError(null);
    setLectureId(null);
  }, []);

  return {
    unit,
    allUnits,
    lectureTitle,
    loading,
    error,
    loadLecture,
    loadUnit,
    reset,
  };
}

export default useLiteratureUnitData;
