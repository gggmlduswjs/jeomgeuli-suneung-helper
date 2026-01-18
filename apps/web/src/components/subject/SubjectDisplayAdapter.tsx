/**
 * Adapter Pattern - 과목별 UI 어댑터
 * 과목별로 다른 UI를 렌더링하는 어댑터 컴포넌트
 */
import { useEffect } from 'react';
import { getSubjectStrategy, extractSubjectType, type SubjectType } from '../../strategies/subjectLearning';
import VoiceFirstDisplay from '../voice/VoiceFirstDisplay';
import { useBrailleChunkReader } from '../../hooks/useBrailleChunkReader';
import { extractFormula, extractKeywords, extractPassageKey } from '../../utils/contentExtractor';
import ChunkNavigation from '../braille/ChunkNavigation';

interface SubjectDisplayAdapterProps {
  subject: string;
  content: string;
  onSpeak: (text: string) => void;
  className?: string;
}

/**
 * 수학 전용 디스플레이
 */
function MathDisplay({ content, onSpeak }: { content: string; onSpeak: (text: string) => void }) {
  const strategy = getSubjectStrategy('math');
  const chunkReader = useBrailleChunkReader(content, {
    maxCells: 3,
    strategy: strategy.readQuestion.chunkStrategy,
    autoPlay: false,
  });

  // 수식 추출
  const formula = extractFormula(content);

  useEffect(() => {
    if (content) {
      onSpeak(content);
    }
    if (formula) {
      setTimeout(() => {
        onSpeak(`수식: ${formula}`);
      }, 3000);
    }
  }, [content, formula, onSpeak]);

  return (
    <div className="space-y-4">
      {chunkReader.totalChunks > 1 && (
        <ChunkNavigation chunkReader={chunkReader} label="수식 청크" />
      )}
      <div className="bg-card border border-border rounded-lg p-4">
        <p className="text-base leading-relaxed whitespace-pre-wrap">{content}</p>
        {formula && (
          <div className="mt-4 p-3 bg-accent/10 border border-accent/20 rounded-lg">
            <p className="text-sm font-medium mb-1">수식</p>
            <p className="text-base font-mono">{formula}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 국어 전용 디스플레이
 */
function KoreanDisplay({ content, onSpeak }: { content: string; onSpeak: (text: string) => void }) {
  const strategy = getSubjectStrategy('korean');
  const chunkReader = useBrailleChunkReader(content, {
    maxCells: 3,
    strategy: strategy.readQuestion.chunkStrategy,
    autoPlay: false,
  });

  // 핵심 문장 추출
  const keySentence = extractPassageKey(content);
  const keywords = extractKeywords(content, 5);

  useEffect(() => {
    if (content) {
      onSpeak(content);
    }
    if (keySentence) {
      setTimeout(() => {
        onSpeak(`핵심 문장: ${keySentence}`);
      }, 3000);
    }
    if (keywords.length > 0) {
      setTimeout(() => {
        onSpeak(`핵심 키워드: ${keywords.join(', ')}`);
      }, 5000);
    }
  }, [content, keySentence, keywords, onSpeak]);

  return (
    <div className="space-y-4">
      {chunkReader.totalChunks > 1 && (
        <ChunkNavigation chunkReader={chunkReader} label="지문 청크" />
      )}
      <div className="bg-card border border-border rounded-lg p-4">
        <p className="text-base leading-relaxed whitespace-pre-wrap">{content}</p>
        {keywords.length > 0 && (
          <div className="mt-4 p-3 bg-accent/10 border border-accent/20 rounded-lg">
            <p className="text-sm font-medium mb-2">핵심 키워드</p>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-accent/20 rounded text-sm"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 영어 전용 디스플레이
 */
function EnglishDisplay({ content, onSpeak }: { content: string; onSpeak: (text: string) => void }) {
  const strategy = getSubjectStrategy('english');
  const chunkReader = useBrailleChunkReader(content, {
    maxCells: 3,
    strategy: strategy.readQuestion.chunkStrategy,
    autoPlay: false,
  });

  // 핵심 어휘 추출
  const keywords = extractKeywords(content, 5);

  useEffect(() => {
    // 영어는 음성 우선
    if (content) {
      onSpeak(content);
    }
    if (keywords.length > 0) {
      setTimeout(() => {
        onSpeak(`핵심 어휘: ${keywords.join(', ')}`);
      }, 3000);
    }
  }, [content, keywords, onSpeak]);

  return (
    <div className="space-y-4">
      {chunkReader.totalChunks > 1 && (
        <ChunkNavigation chunkReader={chunkReader} label="영어 청크" />
      )}
      <div className="bg-card border border-border rounded-lg p-4">
        <p className="text-base leading-relaxed whitespace-pre-wrap">{content}</p>
        {keywords.length > 0 && (
          <div className="mt-4 p-3 bg-accent/10 border border-accent/20 rounded-lg">
            <p className="text-sm font-medium mb-2">핵심 어휘</p>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-accent/20 rounded text-sm"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 과목별 UI 어댑터
 */
export default function SubjectDisplayAdapter({ 
  subject, 
  content, 
  onSpeak,
  className = '' 
}: SubjectDisplayAdapterProps) {
  const subjectType = extractSubjectType(subject);
  const strategy = getSubjectStrategy(subjectType);

  // 과목별로 다른 UI 렌더링
  switch (subjectType) {
    case 'math':
      return <MathDisplay content={content} onSpeak={onSpeak} />;
    
    case 'korean':
      return <KoreanDisplay content={content} onSpeak={onSpeak} />;
    
    case 'english':
      return <EnglishDisplay content={content} onSpeak={onSpeak} />;
    
    case 'science':
    case 'social':
    default:
      // 기본: VoiceFirstDisplay 사용
      return (
        <VoiceFirstDisplay 
          content={content} 
          subject={subject} 
          onSpeak={onSpeak}
          className={className}
        />
      );
  }
}

