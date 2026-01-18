import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import { curriculumAPI } from '../../services/curriculum';
import type { CurriculumDetail } from '../../types/curriculum';

export default function CurriculumDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { speak } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [curriculum, setCurriculum] = useState<CurriculumDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadCurriculum(id);
    }
  }, [id]);

  const loadCurriculum = async (curriculumId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await curriculumAPI.get(curriculumId);
      setCurriculum(data);
    } catch (err: any) {
      const errorMsg = '커리큘럼을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <AppShellMobile title="커리큘럼 상세" className="relative">
        <div className="p-4 text-center py-8">
          <p className="text-muted">로딩 중...</p>
        </div>
      </AppShellMobile>
    );
  }

  if (error || !curriculum) {
    return (
      <AppShellMobile title="커리큘럼 상세" className="relative">
        <div className="p-4">
          <div className="bg-error/10 border border-error rounded-lg p-4">
            <p className="text-error">{error || '커리큘럼을 찾을 수 없습니다.'}</p>
          </div>
          <button
            onClick={() => navigate('/curriculum')}
            className="btn-primary mt-4 w-full"
          >
            목록으로
          </button>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile title={curriculum.title} className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4 space-y-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-4">커리큘럼 정보</h3>
          <div className="space-y-2 text-sm">
            <p>총 레슨: {curriculum.total_lessons}개</p>
            <p>총 학습 단위: {curriculum.total_units}개</p>
            <p>
              상태:{' '}
              <span
                className={
                  curriculum.status === 'DONE'
                    ? 'text-success'
                    : curriculum.status === 'GENERATING'
                    ? 'text-warning'
                    : curriculum.status === 'FAILED'
                    ? 'text-error'
                    : 'text-muted'
                }
              >
                {curriculum.status === 'DONE'
                  ? '완료'
                  : curriculum.status === 'GENERATING'
                  ? '생성 중'
                  : curriculum.status === 'FAILED'
                  ? '실패'
                  : '대기'}
              </span>
            </p>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-4">학습 경로</h3>
          <div className="space-y-2">
            {curriculum.learning_path.map((item, index) => (
              <div key={index} className="text-sm">
                {item.order}. {item.title}
                {index < curriculum.learning_path.length - 1 && (
                  <div className="text-muted">↓</div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-4">레슨 목록</h3>
          <div className="space-y-2">
            {curriculum.lessons.map((lesson, index) => (
              <div
                key={index}
                className="border border-border rounded-lg p-3"
              >
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium">
                    {lesson.lesson_number}강 {lesson.title}
                  </h4>
                </div>
                <p className="text-sm text-muted">
                  학습 단위: {lesson.learning_units.length}개 | 예상 시간: {lesson.estimated_time}분
                </p>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={() => navigate('/curriculum')}
          className="btn-ghost w-full"
        >
          목록으로
        </button>
      </div>
    </AppShellMobile>
  );
}
