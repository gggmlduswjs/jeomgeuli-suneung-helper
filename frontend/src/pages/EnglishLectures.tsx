/**
 * 영어 강의 목록 페이지
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import ToastA11y from '../components/system/ToastA11y';
import { usePageBase } from '../hooks/usePageBase';
import { englishAPI, type EnglishLectureSummary } from '../services/english';
import { createModuleLogger } from '../utils/logger';

const logger = createModuleLogger('EnglishLectures');

export default function EnglishLectures() {
  const navigate = useNavigate();
  const [lectures, setLectures] = useState<EnglishLectureSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { speak, stopTTS, stopSTT, isListening, transcript, showToast, toastMessage, setShowToast, showToastMessage } = usePageBase({
    autoAnnounce: '영어 강의 목록입니다.',
    voiceCommands: {
      home: () => { stopTTS(); navigate('/'); showToastMessage('홈으로 이동합니다.'); speak('홈으로 이동합니다.'); stopSTT(); },
      back: () => { stopTTS(); navigate(-1); showToastMessage('이전 페이지로 이동합니다.'); speak('이전 페이지로 이동합니다.'); stopSTT(); },
    },
  });

  useEffect(() => { loadLectures(); }, []);

  const loadLectures = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await englishAPI.getLectures();
      setLectures(data);
      logger.log(`영어 강의 ${data.length}개 로드`);
      showToastMessage(`영어 강의 ${data.length}개를 불러왔습니다.`);
      speak(`영어 강의 ${data.length}개를 불러왔습니다.`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : '강의 목록을 불러오지 못했습니다.';
      setError(msg);
      logger.error('영어 강의 로드 실패:', err);
      showToastMessage(msg);
      speak(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleLectureSelect = (lecture: EnglishLectureSummary) => {
    showToastMessage(`${lecture.title}을(를) 선택했습니다.`);
    speak(`${lecture.title}을(를) 선택했습니다.`);
    stopTTS();
    stopSTT();
    navigate(`/english/lectures/${lecture.lecture_id}`);
  };

  const handleLectureRead = (lecture: EnglishLectureSummary) => {
    speak(`${lecture.lecture_id}강. ${lecture.title}`);
  };

  return (
    <AppShellMobile title="영어 강의 목록" className="relative h-screen flex flex-col">
      <div className="mb-2">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>
      <div className="px-2 py-1 space-y-2 flex-1 overflow-y-auto min-h-0">
        <div className="bg-card border border-border rounded-lg p-4">
          <h2 className="text-xl font-bold mb-2">영어 강의</h2>
          <p className="text-sm text-muted">총 {lectures.length}강입니다.</p>
        </div>
        {loading && (
          <div className="text-center py-8" role="status" aria-live="polite">강의 목록을 불러오는 중...</div>
        )}
        {error && !loading && (
          <div className="bg-destructive/10 border border-destructive rounded-lg p-4">
            <h3 className="text-lg font-semibold text-destructive mb-2">오류 발생</h3>
            <p className="text-sm">{error}</p>
            <button onClick={loadLectures} className="mt-3 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90" aria-label="다시 시도">다시 시도</button>
          </div>
        )}
        {!loading && !error && lectures.length > 0 && (
          <div className="space-y-2" role="list" aria-label="영어 강의 목록">
            {lectures.map((l) => (
              <div
                key={l.lecture_id}
                className="bg-card border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors cursor-pointer"
                role="listitem"
                tabIndex={0}
                onClick={() => handleLectureSelect(l)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleLectureSelect(l); }
                  if (e.key === 'r' || e.key === 'R') { e.preventDefault(); handleLectureRead(l); }
                }}
                aria-label={`${l.lecture_id}강 ${l.title}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <span className="inline-block px-2 py-0.5 bg-primary/10 text-primary text-xs font-semibold rounded mr-2">{l.lecture_id}강</span>
                    <h3 className="text-base font-semibold inline">{l.title}</h3>
                  </div>
                  <button onClick={(e) => { e.stopPropagation(); handleLectureRead(l); }} className="ml-2 px-3 py-1 text-xs bg-secondary text-secondary-foreground rounded hover:bg-secondary/80" aria-label={`${l.lecture_id}강 제목 읽기`}>읽기</button>
                </div>
              </div>
            ))}
          </div>
        )}
        {!loading && !error && lectures.length === 0 && (
          <div className="text-center py-8"><p className="text-muted">강의가 없습니다.</p></div>
        )}
      </div>
      <div className="border-t border-border p-2 bg-background flex gap-2">
        <button onClick={() => navigate(-1)} className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 font-semibold" aria-label="이전 페이지로">뒤로</button>
        <button onClick={() => navigate('/')} className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 font-semibold" aria-label="홈으로">홈으로</button>
      </div>
      <ToastA11y message={toastMessage} isVisible={showToast} duration={3000} onClose={() => setShowToast(false)} />
    </AppShellMobile>
  );
}
