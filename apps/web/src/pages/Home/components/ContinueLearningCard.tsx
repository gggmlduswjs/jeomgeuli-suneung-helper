/**
 * 오늘 학습 이어하기 카드
 * 보호자용 시각 UI + 시각장애인용 음성 안내
 */
import { BookOpen, Play } from 'lucide-react';
import type { Progress } from '../../../types/progress';

interface ContinueLearningCardProps {
  progress?: Progress | null;
  onContinue?: () => void;
  onSpeak?: (text: string) => void;
}

export default function ContinueLearningCard({
  progress,
  onContinue,
  onSpeak,
}: ContinueLearningCardProps) {
  const handleContinue = () => {
    if (onContinue) {
      onContinue();
    } else if (progress?.unit_id) {
      // Unit 페이지로 이동
      window.location.href = `/unit/${progress.unit_id}`;
    }
  };

  if (!progress || !progress.unit_id) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border-2 border-dashed border-gray-300">
        <div className="flex items-center gap-3 mb-4">
          <BookOpen className="w-6 h-6 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-500">오늘 학습 이어하기</h3>
        </div>
        <p className="text-gray-400 text-sm">진행 중인 학습이 없습니다.</p>
      </div>
    );
  }

  const subjectNames = {
    korean: '국어',
    english: '영어',
    math: '수학'
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow-md p-6 border-2 border-blue-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <BookOpen className="w-6 h-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-800">오늘 학습 이어하기</h3>
        </div>
        <button
          onClick={handleContinue}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          aria-label="학습 이어하기"
        >
          <Play className="w-4 h-4" />
          <span>계속하기</span>
        </button>
      </div>
      
      <div className="space-y-2">
        <div>
          <p className="text-sm text-gray-600 mb-1">현재 학습 위치</p>
          <p className="text-base font-medium text-gray-800">
            {progress.lesson_id ? `강: ${progress.lesson_id}` : '위치 없음'}
          </p>
          {progress.unit_id && (
            <p className="text-sm text-gray-500 mt-1">
              단위: {progress.unit_id}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

