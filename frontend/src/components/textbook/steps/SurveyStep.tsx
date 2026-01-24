/**
 * 커리큘럼 구조 설문 스텝
 * 교재의 구조 파악을 위한 설문조사
 */
import type { CurriculumStructureSurvey } from '../../../services/templates';

interface SurveyStepProps {
  survey: CurriculumStructureSurvey;
  onSurveyChange: (survey: CurriculumStructureSurvey) => void;
}

const UNIT_OPTIONS = [
  { value: 'concept', label: '개념 설명' },
  { value: 'passage', label: '지문/예제' },
  { value: 'problem', label: '문제' },
  { value: 'example', label: '예시' },
  { value: 'summary', label: '요약' }
];

export default function SurveyStep({ survey, onSurveyChange }: SurveyStepProps) {
  const handleLectureBasedChange = (isLectureBased: boolean) => {
    onSurveyChange({
      ...survey,
      is_lecture_based: isLectureBased
    });
  };

  const toggleUnit = (unit: string, field: 'lecture_units' | 'unit_order') => {
    const currentUnits = survey[field] || [];
    const newUnits = currentUnits.includes(unit)
      ? currentUnits.filter(u => u !== unit)
      : [...currentUnits, unit];

    onSurveyChange({
      ...survey,
      [field]: newUnits
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">3. 교재 구조 설문</h3>
        <p className="text-sm text-muted-foreground mb-4">
          교재의 구조를 파악하기 위한 간단한 질문에 답해주세요
        </p>
      </div>

      {/* 강의 기반 구조 */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">
          이 교재는 강의(Lecture) 단위로 구성되어 있나요?
        </label>
        <div className="flex gap-3">
          <button
            onClick={() => handleLectureBasedChange(true)}
            className={`flex-1 px-4 py-3 border rounded-lg transition-colors ${
              survey.is_lecture_based
                ? 'border-primary bg-primary/5 text-primary font-medium'
                : 'border-border hover:border-primary/50'
            }`}
          >
            예 (1강, 2강... 형식)
          </button>
          <button
            onClick={() => handleLectureBasedChange(false)}
            className={`flex-1 px-4 py-3 border rounded-lg transition-colors ${
              !survey.is_lecture_based
                ? 'border-primary bg-primary/5 text-primary font-medium'
                : 'border-border hover:border-primary/50'
            }`}
          >
            아니오 (연속된 내용)
          </button>
        </div>
      </div>

      {/* 강의 내 단위 구성 */}
      {survey.is_lecture_based && (
        <div className="space-y-3">
          <label className="block text-sm font-medium">
            각 강의는 어떤 요소들로 구성되어 있나요? (복수 선택)
          </label>
          <div className="grid grid-cols-2 gap-2">
            {UNIT_OPTIONS.map(option => (
              <button
                key={option.value}
                onClick={() => toggleUnit(option.value, 'lecture_units')}
                className={`px-4 py-3 border rounded-lg transition-colors text-sm ${
                  survey.lecture_units?.includes(option.value)
                    ? 'border-primary bg-primary/5 text-primary font-medium'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 단위 순서 */}
      <div className="space-y-3">
        <label className="block text-sm font-medium">
          단위들이 나타나는 순서를 선택해주세요
        </label>
        <p className="text-xs text-muted-foreground">
          선택한 순서대로 번호가 표시됩니다
        </p>
        <div className="space-y-2">
          {UNIT_OPTIONS.map(option => {
            const orderIndex = survey.unit_order?.indexOf(option.value);
            const isSelected = orderIndex !== undefined && orderIndex !== -1;

            return (
              <button
                key={option.value}
                onClick={() => toggleUnit(option.value, 'unit_order')}
                className={`w-full px-4 py-3 border rounded-lg transition-colors text-left flex items-center gap-3 ${
                  isSelected
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold ${
                  isSelected
                    ? 'border-primary bg-primary text-white'
                    : 'border-border'
                }`}>
                  {isSelected ? (orderIndex + 1) : ''}
                </div>
                <span className={isSelected ? 'font-medium' : ''}>
                  {option.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
