/**
 * 수학1 강의 상세 페이지 (목차만 연동, 학습 UI 준비 중)
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import { math1API } from '../services/math1';

export default function Math1LectureDetail() {
  const { lectureId } = useParams<{ lectureId: string }>();
  const navigate = useNavigate();
  const [title, setTitle] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!lectureId) return;
    const id = parseInt(lectureId);
    if (Number.isNaN(id)) {
      setError('잘못된 강의 번호입니다.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    math1API
      .getLecture(id)
      .then((l) => {
        setTitle(l.title);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : '강의를 불러오지 못했습니다.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [lectureId]);

  if (loading) {
    return (
      <AppShellMobile title="수학1 강의" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1">
          <p className="text-muted" role="status" aria-live="polite">강의를 불러오는 중...</p>
        </div>
      </AppShellMobile>
    );
  }

  if (error) {
    return (
      <AppShellMobile title="수학1 강의" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1 px-4">
          <div className="bg-destructive/10 border border-destructive rounded-lg p-6 max-w-md text-center">
            <h3 className="text-lg font-semibold text-destructive mb-2">오류 발생</h3>
            <p className="text-sm mb-4">{error}</p>
            <button
              onClick={() => navigate('/math1/lectures')}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
              aria-label="강의 목록으로"
            >
              강의 목록으로
            </button>
          </div>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile title={title} className="relative h-screen flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center px-4">
        <h2 className="text-xl font-bold mb-2">{title}</h2>
        <p className="text-muted text-sm mb-6">수학1 학습 화면은 준비 중입니다.</p>
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/math1/lectures')}
            className="px-5 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 font-medium"
            aria-label="강의 목록으로"
          >
            목록으로
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2.5 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 font-medium"
            aria-label="홈으로"
          >
            홈으로
          </button>
        </div>
      </div>
    </AppShellMobile>
  );
}
