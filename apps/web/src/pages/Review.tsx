/**
 * 복습 페이지
 * 복습 큐 API 연동, 우선순위 표시
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import ToastA11y from '../components/system/ToastA11y';
import ReviewQueue from '../components/review/ReviewQueue';
import { reviewAPI } from '../services/review';
import { unitsAPI } from '../services/units';
import type { ReviewQueueItem } from '../types/review';
import type { Unit } from '../types/unit';

export default function Review() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [queueItems, setQueueItems] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReviewQueue();
  }, []);

  const loadReviewQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await reviewAPI.getQueue('u_demo');
      setQueueItems(data);
      
      if (data.length === 0) {
        speak('복습할 항목이 없습니다.');
      } else {
        speak(`복습할 항목이 ${data.length}개 있습니다.`);
      }
    } catch (err) {
      const errorMsg = '복습 큐를 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleItemSelect = async (item: ReviewQueueItem) => {
    // Unit 페이지로 이동
    navigate(`/unit/${item.unit_id}`);
  };

  const handleComplete = async (unitId: string) => {
    try {
      await reviewAPI.complete({
        user_id: 'u_demo',
        unit_id: unitId,
      });
      
      // 큐 새로고침
      await loadReviewQueue();
      showToastMessage('복습이 완료되었습니다.');
      speak('복습이 완료되었습니다.');
    } catch (err) {
      console.error('[Review] 복습 완료 실패:', err);
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
      navigate('/');
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
    <AppShellMobile title="복습" className="relative">
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
          <ReviewQueue
            items={queueItems}
            onSelect={handleItemSelect}
            onComplete={handleComplete}
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
