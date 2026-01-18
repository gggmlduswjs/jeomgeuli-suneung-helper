import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import { curriculumAPI } from '../../services/curriculum';
import type { Curriculum, Subject } from '../../types/curriculum';

export default function CurriculumPage() {
  const navigate = useNavigate();
  const { speak } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<Subject | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCurricula();
  }, [selectedSubject]);

  const loadCurricula = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await curriculumAPI.list(selectedSubject);
      setCurricula(data);
    } catch (err: any) {
      const errorMsg = '커리큘럼 목록을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    navigate('/curriculum/create');
  };

  const handleView = (curriculumId: string) => {
    navigate(`/curriculum/${curriculumId}`);
  };

  return (
    <AppShellMobile title="커리큘럼 관리" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">커리큘럼 목록</h2>
          <button
            onClick={handleCreate}
            className="btn-primary text-sm"
            aria-label="새 커리큘럼 생성"
          >
            + 생성
          </button>
        </div>

        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setSelectedSubject(undefined)}
            className={`px-4 py-2 rounded-lg ${
              selectedSubject === undefined ? 'btn-primary' : 'btn-ghost'
            }`}
          >
            전체
          </button>
          <button
            onClick={() => setSelectedSubject('KOREAN')}
            className={`px-4 py-2 rounded-lg ${
              selectedSubject === 'KOREAN' ? 'btn-primary' : 'btn-ghost'
            }`}
          >
            문학
          </button>
          <button
            onClick={() => setSelectedSubject('MATH')}
            className={`px-4 py-2 rounded-lg ${
              selectedSubject === 'MATH' ? 'btn-primary' : 'btn-ghost'
            }`}
          >
            수1
          </button>
          <button
            onClick={() => setSelectedSubject('ENGLISH')}
            className={`px-4 py-2 rounded-lg ${
              selectedSubject === 'ENGLISH' ? 'btn-primary' : 'btn-ghost'
            }`}
          >
            영어
          </button>
        </div>

        {loading && (
          <div className="text-center py-8">
            <p className="text-muted">로딩 중...</p>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-4 mb-4">
            <p className="text-error">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-4">
            {curricula.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted">등록된 커리큘럼이 없습니다.</p>
                <button
                  onClick={handleCreate}
                  className="btn-primary mt-4"
                >
                  새 커리큘럼 생성
                </button>
              </div>
            ) : (
              curricula.map((curriculum) => (
                <div
                  key={curriculum.curriculum_id}
                  className="bg-card border border-border rounded-lg p-4"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold">{curriculum.title}</h3>
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        curriculum.status === 'DONE'
                          ? 'bg-success/20 text-success'
                          : curriculum.status === 'GENERATING'
                          ? 'bg-warning/20 text-warning'
                          : curriculum.status === 'FAILED'
                          ? 'bg-error/20 text-error'
                          : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      {curriculum.status === 'DONE'
                        ? '완료'
                        : curriculum.status === 'GENERATING'
                        ? '생성 중'
                        : curriculum.status === 'FAILED'
                        ? '실패'
                        : '대기'}
                    </span>
                  </div>
                  <p className="text-sm text-muted mb-2">
                    레슨: {curriculum.lesson_count}개
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleView(curriculum.curriculum_id)}
                      className="btn-ghost text-sm"
                    >
                      보기
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </AppShellMobile>
  );
}
