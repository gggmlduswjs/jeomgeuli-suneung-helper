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
import { lessonsAPI } from '../services/lessons';
import { unitsAPI } from '../services/units';
import type { Lesson } from '../types/lesson';
import type { Unit } from '../types/unit';

export default function Lesson() {
  const navigate = useNavigate();
  const { lessonId } = useParams<{ lessonId: string }>();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    } catch (err) {
      const errorMsg = '강을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadUnits = async (id: string) => {
    try {
      const data = await unitsAPI.list(id);
      setUnits(data);
    } catch (err) {
      console.error('[Lesson] 학습 단위 목록 로드 실패:', err);
    }
  };

  const handleUnitSelect = (unit: Unit) => {
    navigate(`/unit/${unit.unit_id}`);
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

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

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
          <LessonList
            units={units}
            onSelect={handleUnitSelect}
            onSpeak={speak}
          />
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
