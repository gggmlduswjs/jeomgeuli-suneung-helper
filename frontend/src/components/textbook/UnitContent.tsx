import { useState, useEffect, useMemo } from 'react';
import { getSubjectStrategy } from '../../strategies/subjectLearning';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import { useUnitBraille } from '../../hooks/useUnitBraille';
import { useUnitAIExplanation } from '../../hooks/useUnitAIExplanation';
import BrailleStatusPanel from '../unit/BrailleStatusPanel';
import AIExplanationCard from '../unit/AIExplanationCard';
import UnitHeader from '../unit/UnitHeader';
import UnitImage from '../unit/UnitImage';
import ProblemContent from './ProblemContent';
import BrailleStrip from '../braille/BrailleStrip';
import SimilarContentSection from './SimilarContentSection';
import { extractKeywords } from '../../utils/contentExtractor';
import { literatureAPI } from '../../services/literature';
import type { Unit } from '../../types/api';

// 점자 출력 기능은 keywords 섹션에서만 사용

// 키워드 섹션 컴포넌트
function KeywordsSection({
  aiExplanation,
  loadingAI,
  isConnected,
  writeText,
  brailleStatus,
  allSections = [],
}: {
  aiExplanation: string | null;
  loadingAI: boolean;
  isConnected: boolean;
  writeText: (text: string) => Promise<void>;
  brailleStatus: 'pending' | 'converting' | 'completed' | 'failed';
  allSections?: any[];
}) {
  const [tfidfKeywords, setTfidfKeywords] = useState<Array<{ keyword: string; score: number }>>([]);
  const [loadingTFIDF, setLoadingTFIDF] = useState(false);
  
  // AI 설명에서 키워드 추출 (기본 정규식 방식 - fallback)
  const fallbackKeywords = useMemo(() => {
    if (!aiExplanation) return [];
    return extractKeywords(aiExplanation, 3);
  }, [aiExplanation]);

  // TF-IDF 기반 키워드 추출 (ML 방식)
  useEffect(() => {
    if (!aiExplanation || loadingAI) {
      setTfidfKeywords([]);
      return;
    }

    // 모든 섹션의 콘텐츠를 수집 (문제 섹션 제외)
    const allTexts = allSections
      .filter((s) => s.section_type !== 'problem' && s.section_type !== 'keywords')
      .map((s) => s.content || '')
      .filter((c) => c.trim().length > 0);

    // AI 설명도 포함
    if (aiExplanation.trim().length > 0) {
      allTexts.push(aiExplanation);
    }

    if (allTexts.length === 0) {
      setTfidfKeywords([]);
      return;
    }

    setLoadingTFIDF(true);
    literatureAPI
      .extractKeywordsTFIDF(allTexts, 3)
      .then((result) => {
        setTfidfKeywords(result.keywords);
      })
      .catch((err) => {
        console.error('[KeywordsSection] TF-IDF 키워드 추출 실패:', err);
        // 실패 시 fallback 키워드 사용
        setTfidfKeywords([]);
      })
      .finally(() => {
        setLoadingTFIDF(false);
      });
  }, [aiExplanation, allSections, loadingAI]);

  // TF-IDF 키워드가 있으면 사용, 없으면 fallback 사용
  const keywords = useMemo(() => {
    if (tfidfKeywords.length > 0) {
      return tfidfKeywords.map((k) => k.keyword);
    }
    return fallbackKeywords;
  }, [tfidfKeywords, fallbackKeywords]);

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-4">
      <div>
        <h3 className="text-lg font-semibold mb-2">단원 내용 요약</h3>
        {loadingAI ? (
          <p className="text-xs text-gray-500 mb-4">요약을 생성하는 중입니다...</p>
        ) : aiExplanation ? (
          <div className="text-sm text-gray-700 bg-gray-50 rounded p-3 mb-4 whitespace-pre-wrap">
            {aiExplanation}
          </div>
        ) : (
          <p className="text-xs text-gray-500 mb-4">요약이 생성되지 않았습니다.</p>
        )}
      </div>
      
      <div>
        <h4 className="text-md font-semibold mb-3">핵심 키워드 (3개)</h4>
        {(loadingAI || loadingTFIDF) ? (
          <p className="text-sm text-muted">키워드를 추출하는 중입니다...</p>
        ) : keywords.length > 0 ? (
          <>
            <p className="text-sm text-muted mb-4">다음 키워드를 점자로 읽어보세요.</p>
            <div className="space-y-3">
              {keywords.map((keyword: string, idx: number) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-600 w-8">{idx + 1}.</span>
                  <BrailleStrip text={keyword.trim()} size="normal" />
                  <span className="text-sm text-gray-700 ml-auto">{keyword.trim()}</span>
                </div>
              ))}
            </div>
            {/* 키워드 섹션도 BLE 디바이스로 출력 */}
            {isConnected && (
              <div className="mt-4 pt-4 border-t">
                <p className="text-xs text-muted mb-2">점자 디바이스 출력:</p>
                <button
                  onClick={() => {
                    const keywordsText = keywords.join(' ');
                    writeText(keywordsText).catch((err) => {
                      console.error('[UnitContent] 키워드 점자 출력 실패:', err);
                    });
                  }}
                  className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90"
                >
                  키워드 점자 출력
                </button>
              </div>
            )}
          </>
        ) : (
          <p className="text-muted">키워드가 없습니다.</p>
        )}
      </div>
    </div>
  );
}

interface UnitContentProps {
  unit: Unit | null;
  onSpeak: (text: string) => void;
  readingMode?: 'braille-only' | 'audio-first' | 'mixed';
  sectionType?: string;
  problemMetadata?: Unit['problem_metadata'];
  onTTSComplete?: () => void; // TTS 재생 완료 시 콜백
  allSections?: any[]; // keywords 섹션 요약 생성을 위한 전체 섹션 데이터
  currentSectionIndex?: number; // 현재 섹션 인덱스 (유사 콘텐츠 추천용)
  onSectionSelect?: (index: number) => void; // 섹션 선택 핸들러 (유사 콘텐츠 클릭 시)
}

export default function UnitContent({
  unit,
  onSpeak,
  readingMode = 'braille-only',
  sectionType = 'general',
  problemMetadata,
  onTTSComplete,
  allSections = [],
  currentSectionIndex,
  onSectionSelect,
}: UnitContentProps) {
  const { isConnected, writeCells, writeText } = useBrailleBLE();
  const subject = unit?.textbook?.subject?.toLowerCase() || 'math';
  const strategy = getSubjectStrategy(subject);

  const { brailleStatus, chunkReader } = useUnitBraille({
    unit,
    strategy,
    readingMode,
    isConnected,
    writeCells,
  });

  // AI 설명만 자동으로 읽기 (제목이나 키워드는 읽지 않음)
  // keywords 섹션일 때는 이전 섹션들의 내용을 모두 모아서 요약 생성
  // 섹션 변경 시 이전 데이터를 초기화하기 위해 key를 사용
  const { aiExplanation, loadingAI, loadAIExplanation } = useUnitAIExplanation({
    unit,
    sectionType,
    autoLoad: true,
    onSpeak,
    autoSpeak: true, // AI 설명 생성 시 자동으로 TTS 재생
    readingMode, // 읽기 모드 전달
    onTTSComplete, // TTS 완료 시 다음 섹션으로 이동
    allSections: sectionType === 'keywords' ? allSections : undefined, // keywords 섹션에서만 전달
  });
  
  // 섹션 변경 시 점자 상태 초기화 (keywords 섹션 제외)
  useEffect(() => {
    if (sectionType !== 'keywords' && unit?.id) {
      // 섹션이 변경되면 점자 상태 초기화는 useUnitBraille 내부에서 처리됨
      // 추가 초기화가 필요하면 여기서 처리
    }
  }, [unit?.id, sectionType]);

  if (!unit) {
    return (
      <div className="p-4 text-center text-muted">
        <p>단원을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <UnitHeader title={unit.title} textbookTitle={unit.textbook_title} />

      {/* 점자 변환 상태 표시 */}
      {readingMode === 'braille-only' && (
        <BrailleStatusPanel
          brailleStatus={brailleStatus}
          isConnected={isConnected}
          chunkReader={chunkReader}
        />
      )}

      {/* AI 설명 표시 */}
      <AIExplanationCard
        sectionType={sectionType}
        aiExplanation={aiExplanation}
        loadingAI={loadingAI}
        onSpeak={onSpeak}
        onLoadExplanation={loadAIExplanation}
        hasContent={!!(unit && unit.content)}
      />

      {/* 이미지 표시 */}
      {unit.image_path && (
        <UnitImage imagePath={unit.image_path} alt={unit.title || '학습 내용 이미지'} />
      )}

      {/* 본문 내용 */}
      {sectionType === 'problem' ? (
        <ProblemContent
          unit={unit}
          onSpeak={onSpeak}
          problemNumber={unit.title?.match(/\d+/)?.[0]}
          problemMetadata={problemMetadata || unit?.problem_metadata}
        />
      ) : sectionType === 'keywords' ? (
        // 핵심 키워드 섹션: AI 자동 설명을 요약으로 사용, 그 요약에서 키워드 추출
        <KeywordsSection 
          aiExplanation={aiExplanation}
          loadingAI={loadingAI}
          isConnected={isConnected}
          writeText={writeText}
          brailleStatus={brailleStatus}
          allSections={allSections}
        />
      ) : (
        // 이미지가 있으면 텍스트는 표시하지 않음 (이미지로 충분)
        unit.image_path ? null : (
          <div className="bg-card border border-border rounded-lg p-4">
            {/* 점자 출력 기능은 keywords 섹션에서만 사용 */}
            {/* 일반 섹션은 텍스트만 표시 */}
            <div className="whitespace-pre-wrap text-base leading-relaxed">
              {unit.content || '내용이 없습니다.'}
            </div>
          </div>
        )
      )}

      {/* 유사 콘텐츠 추천 (문제 섹션과 키워드 섹션 제외) */}
      {sectionType !== 'problem' && 
       sectionType !== 'keywords' && 
       allSections.length > 1 && 
       unit.content && (
        <SimilarContentSection
          queryText={unit.content}
          candidateTexts={allSections
            .filter((s) => s.section_type !== 'problem' && s.section_type !== 'keywords')
            .map((s) => s.content || '')
            .filter((c) => c.trim().length > 0)}
          currentIndex={currentSectionIndex}
          onSelect={onSectionSelect}
          topK={3}
          minSimilarity={0.3}
        />
      )}
    </div>
  );
}


