/**
 * 음성 우선 UX 컴포넌트
 * 음성을 먼저 재생하고, 점자는 보조적으로 표시
 */
import { useEffect } from 'react';
import { useBrailleChunkReader } from '../../hooks/useBrailleChunkReader';
import { getSubjectStrategy, extractSubjectType } from '../../strategies/subjectLearning';
import ChunkNavigation from '../braille/ChunkNavigation';

interface VoiceFirstDisplayProps {
  content: string;
  subject: string;
  onSpeak: (text: string) => void;
  className?: string;
}

export default function VoiceFirstDisplay({ 
  content, 
  subject, 
  onSpeak,
  className = '' 
}: VoiceFirstDisplayProps) {
  const subjectType = extractSubjectType(subject);
  const strategy = getSubjectStrategy(subjectType);
  
  // 청크 리더 (과목별 전략 적용)
  const chunkReader = useBrailleChunkReader(content, {
    maxCells: 3,
    strategy: strategy.readQuestion.chunkStrategy,
    autoPlay: false,
  });

  // 자동으로 음성 재생 (음성 우선)
  useEffect(() => {
    if (content && strategy.displayContent.useAudio) {
      onSpeak(content);
    }
  }, [content, onSpeak, strategy.displayContent.useAudio]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 점자 청크 네비게이션 (보조적) */}
      {chunkReader.totalChunks > 1 && (
        <ChunkNavigation 
          chunkReader={chunkReader}
          label={`${subject} 점자 청크`}
        />
      )}
      
      {/* 텍스트 내용 (시각적 표시용) */}
      <div className="bg-card border border-border rounded-lg p-4">
        <p className="text-base leading-relaxed whitespace-pre-wrap">
          {content}
        </p>
      </div>
    </div>
  );
}

