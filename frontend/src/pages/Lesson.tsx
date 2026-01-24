/**
 * 강(단원) 페이지
 * 강 목록 표시 및 Unit 페이지로 이동
 */
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import ToastA11y from '../components/system/ToastA11y';
import LessonList from '../components/lesson/LessonList';
import { lessonsAPI, unitsAPI } from '../services/api/client';
import { useAILectureTeacher } from '../hooks/useAILectureTeacher';
import type { Lesson } from '../types/lesson';
import type { Unit } from '../types/unit';

export default function Lesson() {
  const navigate = useNavigate();
  const { lessonId } = useParams<{ lessonId: string }>();
  const { speak, stop: stopTTS } = useTTS();
  const { stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };
  
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [showSequentialLesson, setShowSequentialLesson] = useState(false);
  
  // AI 강의 선생님 훅 (순차적 수업용)
  const aiTeacher = lessonId ? useAILectureTeacher(lessonId) : null;

  useEffect(() => {
    if (lessonId) {
      loadLesson(lessonId);
      loadUnits(lessonId);
    }
  }, [lessonId]);

  const loadLesson = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await lessonsAPI.get(id);
      setLesson(data);
      speak(`${data.title}입니다. ${data.unit_count || 0}개의 학습 단위가 있습니다.`);
      
      // AI 요약 로드
      loadAISummary(id);
    } catch (err) {
      const errorMsg = '강을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadAISummary = async (lessonId: string) => {
    setIsLoadingSummary(true);
    try {
      const summary = await lessonsAPI.getSummary(lessonId);
      setAiSummary(summary.summary);
      // 요약을 TTS로 재생
      speak(`이 레슨의 핵심 내용: ${summary.summary}`);
    } catch (err) {
      console.error('[Lesson] AI 요약 로드 실패:', err);
      // 요약 실패해도 계속 진행
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const loadUnits = async (id: string) => {
    try {
      const data = await unitsAPI.listByLesson(id);
      setUnits(data);
    } catch (err) {
      console.error('[Lesson] 학습 단위 목록 로드 실패:', err);
    }
  };

  const handleUnitSelect = async (unit: Unit) => {
    // Lesson 정보가 필요하므로 먼저 로드
    if (lesson?.book_id) {
      // bookId와 lessonId를 포함한 경로로 이동 (향후 QuestionLearning으로 통합 가능)
      navigate(`/unit/${unit.unit_id}`);
    } else {
      // 레거시 경로
      navigate(`/unit/${unit.unit_id}`);
    }
  };

  // 음성 명령어
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: () => {
      if (lesson?.book_id) {
        navigate(`/book/${lesson.book_id}`);
      } else {
        navigate('/');
      }
    },
  });

  useEffect(() => {
    if (!transcript) return;
    onSpeech(transcript);
  }, [transcript, onSpeech]);

  return (
    <AppShellMobile title={lesson?.title || '강'} className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
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
            {/* AI 요약 표시 */}
            {isLoadingSummary && (
              <div className="bg-info/10 border border-info rounded-lg p-4">
                <p className="text-info">AI가 레슨 내용을 요약하고 있습니다...</p>
              </div>
            )}
            
            {aiSummary && !isLoadingSummary && (
              <div className="bg-primary/10 border border-primary rounded-lg p-4">
                <h4 className="font-semibold mb-2">AI 레슨 요약</h4>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{aiSummary}</p>
                <button
                  onClick={() => speak(`이 레슨의 핵심 내용: ${aiSummary}`)}
                  className="btn-ghost text-xs mt-2"
                >
                  다시 듣기
                </button>
              </div>
            )}
            
            {/* 순차적 수업 모드 */}
            {lesson && (lesson as any).lecture_script_text && aiTeacher && (
              <div className="bg-card border border-border rounded-lg p-4 mb-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-semibold">AI 순차적 수업</h4>
                  {!showSequentialLesson && (
                    <button
                      onClick={async () => {
                        setShowSequentialLesson(true);
                        await aiTeacher.startLesson();
                      }}
                      className="btn-primary text-sm"
                      disabled={aiTeacher.isTeaching}
                    >
                      수업 시작
                    </button>
                  )}
                </div>
                
                {showSequentialLesson && (
                  <div className="space-y-2">
                    {aiTeacher.currentTopic && (
                      <div className="bg-primary/10 border border-primary rounded-lg p-3 mb-2">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {aiTeacher.currentTopic}
                        </p>
                      </div>
                    )}
                    
                    <div className="flex gap-2">
                      <button
                        onClick={aiTeacher.prevTopic}
                        disabled={aiTeacher.position === 0 || aiTeacher.isTeaching}
                        className="btn-ghost text-sm flex-1"
                      >
                        이전
                      </button>
                      <button
                        onClick={aiTeacher.nextTopic}
                        disabled={aiTeacher.isTeaching}
                        className="btn-primary text-sm flex-1"
                      >
                        {aiTeacher.isTeaching ? '처리 중...' : '다음'}
                      </button>
                    </div>
                    
                    <button
                      onClick={() => setShowSequentialLesson(false)}
                      className="btn-ghost text-xs w-full"
                    >
                      수업 종료
                    </button>
                  </div>
                )}
              </div>
            )}
            
            <LessonList
              units={units}
              onSelect={handleUnitSelect}
              onSpeak={speak}
            />
          </div>
        )}
      </div>

      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
