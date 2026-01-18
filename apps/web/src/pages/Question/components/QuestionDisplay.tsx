import { useEffect } from 'react';
import { BraillePatternFactory } from '../../../lib/braillePattern';
import useBrailleBLE from '../../../hooks/useBrailleBLE';
import { useBrailleChunkReader } from '../../../hooks/useBrailleChunkReader';
import { getSubjectStrategy, extractSubjectType } from '../../../strategies/subjectLearning';
import { extractFormula, extractKeywords } from '../../../utils/contentExtractor';
import type { Question } from '../../../lib/api';

interface QuestionDisplayProps {
  question: Question | null;
  onSpeak: (text: string) => void;
  onChunkNavigation?: (action: 'next' | 'prev' | 'reset') => void;
  chunkNavigationRef?: React.MutableRefObject<{ next: () => void; prev: () => void; reset: () => void } | null>;
  readingMode?: 'braille-only' | 'braille-with-audio' | 'audio-first';
  subject?: 'math' | 'korean' | 'english' | 'science' | 'social';
}

export default function QuestionDisplay({ 
  question, 
  onSpeak, 
  onChunkNavigation, 
  chunkNavigationRef,
  readingMode = 'braille-only',
  subject: subjectProp
}: QuestionDisplayProps) {
  const { isConnected, writeCells } = useBrailleBLE();

  // 과목 추출 (question에서 직접 가져오거나 기본값 사용)
  // TODO: Question 타입에 subject 필드 추가 필요
  const subject = subjectProp || 'math'; // 기본값, 나중에 question.subject로 변경
  const strategy = getSubjectStrategy(subject);

  // 전체 문제 텍스트 구성
  const fullQuestionText = question
    ? `${question.question_text}\n\n선택지:\n1. ${question.choice1}\n2. ${question.choice2}\n3. ${question.choice3}\n4. ${question.choice4}${question.choice5 ? `\n5. ${question.choice5}` : ''}`
    : '';

  // 청크 리더 (과목별 전략 적용)
  const chunkReader = useBrailleChunkReader(fullQuestionText, {
    maxCells: 3, // 설정에서 가져올 수 있음
    strategy: strategy.readQuestion.chunkStrategy,
    autoPlay: false,
    subject: subject, // 과목별 전략 적용
  });

  // chunkNavigationRef에 함수 등록 (부모 컴포넌트에서 음성 명령으로 접근 가능)
  useEffect(() => {
    if (chunkNavigationRef) {
      chunkNavigationRef.current = {
        next: chunkReader.next,
        prev: chunkReader.prev,
        reset: chunkReader.reset,
      };
    }
  }, [chunkReader.next, chunkReader.prev, chunkReader.reset, chunkNavigationRef]);

  // 문제 및 선택지 음성 안내 (과목별 전략 적용)
  useEffect(() => {
    if (!question) return;

    // 점자 읽기 모드: 음성 최소화
    if (readingMode === 'braille-only') {
      // "점자 문제입니다. 읽고 답하세요." 한 번만
      onSpeak('점자 문제입니다. 읽고 답하세요.');
      return;
    }

    // 음성 우선: 전체 문제 읽기
    if (strategy.readQuestion.primary === 'audio' || strategy.readQuestion.primary === 'mixed') {
      onSpeak(question.question_text);
    }

    // 선택지 읽기 (약간의 지연 후)
    setTimeout(() => {
      const choices = [
        `1번: ${question.choice1}`,
        `2번: ${question.choice2}`,
        `3번: ${question.choice3}`,
        `4번: ${question.choice4}`,
        question.choice5 ? `5번: ${question.choice5}` : null,
      ].filter(Boolean).join('. ');
      onSpeak(choices);
    }, 3000);

    // 점자 출력 (과목별 전략 적용)
    if (isConnected) {
      if (strategy.readQuestion.primary === 'braille-chunk' || strategy.readQuestion.primary === 'mixed') {
        // 청크 방식: 첫 번째 청크를 점자로 출력
        if (chunkReader.currentChunk) {
          // useBrailleChunkReader가 자동으로 출력하므로 여기서는 추가 작업 불필요
        }
      }

      // 수학: 수식 추출 및 표시
      if (subject === 'math' && strategy.specialHandling?.math === 'formula-braille') {
        const formula = extractFormula(question.question_text);
        if (formula) {
          setTimeout(() => {
            // 수식은 별도로 점자로 출력 (청크 방식)
            // 실제로는 청크 리더에 포함되어 있음
          }, 5000);
        }
      }

      // 선택지 번호 점자 패턴 전송
      const patterns = [
        BraillePatternFactory.createNumberPattern(1),
        BraillePatternFactory.createNumberPattern(2),
        BraillePatternFactory.createNumberPattern(3),
        BraillePatternFactory.createNumberPattern(4),
      ];
      if (question.choice5) {
        patterns.push(BraillePatternFactory.createNumberPattern(5));
      }
      // 각 패턴을 순차적으로 전송
      patterns.forEach((pattern, index) => {
        setTimeout(() => {
          writeCells([pattern]);
        }, 4000 + index * 500);
      });
    }
  }, [question, onSpeak, isConnected, writeCells, strategy, subject, chunkReader.currentChunk, readingMode]);

  if (!question) {
    return (
      <div className="p-4 text-center text-muted">
        <p>문제를 불러오는 중...</p>
      </div>
    );
  }

  const choices = [
    { num: 1, text: question.choice1 },
    { num: 2, text: question.choice2 },
    { num: 3, text: question.choice3 },
    { num: 4, text: question.choice4 },
    question.choice5 ? { num: 5, text: question.choice5 } : null,
  ].filter(Boolean) as Array<{ num: number; text: string }>;

  return (
    <div className="space-y-4">
      <div className="bg-card border border-border rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-2">문제</h3>
        <p className="text-base leading-relaxed whitespace-pre-wrap">
          {question.question_text}
        </p>
      </div>

      {/* 청크 네비게이션 (점자 디스플레이 연결 시 표시) */}
      {isConnected && chunkReader.totalChunks > 1 && (
        <div className="bg-accent/10 border border-accent/20 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">점자 청크</span>
            <span className="text-xs text-muted">
              {chunkReader.currentIndex + 1} / {chunkReader.totalChunks}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                chunkReader.prev();
                onChunkNavigation?.('prev');
              }}
              disabled={chunkReader.currentIndex === 0}
              className="btn-ghost text-xs px-2 py-1 disabled:opacity-50"
              aria-label="이전 청크"
            >
              ← 이전
            </button>
            <button
              onClick={() => {
                chunkReader.next();
                onChunkNavigation?.('next');
              }}
              disabled={chunkReader.currentIndex >= chunkReader.totalChunks - 1}
              className="btn-ghost text-xs px-2 py-1 disabled:opacity-50"
              aria-label="다음 청크"
            >
              다음 →
            </button>
            <button
              onClick={() => {
                chunkReader.reset();
                onChunkNavigation?.('reset');
              }}
              className="btn-ghost text-xs px-2 py-1"
              aria-label="처음으로"
            >
              처음
            </button>
          </div>
          {chunkReader.currentChunk && (
            <p className="text-xs text-muted mt-2">
              현재: {chunkReader.currentChunk.substring(0, 30)}
              {chunkReader.currentChunk.length > 30 ? '...' : ''}
            </p>
          )}
        </div>
      )}

      <div className="space-y-2">
        <h3 className="text-lg font-semibold mb-2">선택지</h3>
        {choices.map((choice) => (
          <div
            key={choice.num}
            className="bg-card border border-border rounded-lg p-3 flex items-start gap-3"
          >
            <span className="font-bold text-primary min-w-[2rem]">
              {choice.num}번
            </span>
            <span className="flex-1">{choice.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}


