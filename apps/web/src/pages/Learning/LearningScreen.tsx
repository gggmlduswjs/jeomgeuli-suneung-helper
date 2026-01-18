/**
 * 학습 화면 - 3단 패널 구조
 * 보호자용 시각 UI + 시각장애인용 음성/점자 UX
 */
import { useState, useEffect } from 'react';
import DocumentTree from './components/DocumentTree';
import CurrentContentPanel from './components/CurrentContentPanel';
import BrailleStatusPanel from './components/BrailleStatusPanel';
import GraphPreview from './components/GraphPreview';
import useTTS from '../../hooks/useTTS';
import { useBrailleBLE } from '../../hooks/useBrailleBLE';

interface LearningScreenProps {
  unitId?: number;
  passageId?: number;
  questionId?: number;
  subject?: 'korean' | 'english' | 'math';
}

export default function LearningScreen({
  unitId,
  passageId,
  questionId,
  subject = 'korean'
}: LearningScreenProps) {
  const { speak, stop: stopTTS } = useTTS();
  const { isConnected, writeCells } = useBrailleBLE();
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);
  const [chunks, setChunks] = useState<Array<{
    id: number;
    text: string;
    cells: number[][];
    semanticType: string;
  }>>([]);

  // 현재 청크
  const currentChunk = chunks[currentChunkIndex];

  // 청크 읽기 (TTS + 점자 출력)
  useEffect(() => {
    if (currentChunk) {
      // TTS로 읽기
      speak(currentChunk.text);
      
      // 점자 디바이스에 출력
      if (isConnected && currentChunk.cells) {
        // 3-cell 패킷으로 전송
        const packets = currentChunk.cells;
        packets.forEach((packet) => {
          writeCells(packet);
        });
      }
    }
  }, [currentChunk, isConnected, speak, writeCells]);

  // 다음 청크
  const handleNext = () => {
    if (currentChunkIndex < chunks.length - 1) {
      stopTTS();
      setCurrentChunkIndex(currentChunkIndex + 1);
    }
  };

  // 이전 청크
  const handlePrev = () => {
    if (currentChunkIndex > 0) {
      stopTTS();
      setCurrentChunkIndex(currentChunkIndex - 1);
    }
  };

  // 반복
  const handleRepeat = () => {
    stopTTS();
    if (currentChunk) {
      speak(currentChunk.text);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 왼쪽 패널: 지문/문항 구조 트리 (보호자용) */}
      <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
        <DocumentTree
          unitId={unitId}
          passageId={passageId}
          questionId={questionId}
          currentChunkIndex={currentChunkIndex}
          onChunkSelect={(index) => {
            stopTTS();
            setCurrentChunkIndex(index);
          }}
        />
      </div>

      {/* 가운데 패널: 현재 출력 중인 내용 (공통) */}
      <div className="flex-1 flex flex-col">
        <CurrentContentPanel
          chunk={currentChunk}
          chunkIndex={currentChunkIndex}
          totalChunks={chunks.length}
          onNext={handleNext}
          onPrev={handlePrev}
          onRepeat={handleRepeat}
        />
        
        {/* 그래프가 있을 경우 미리보기 */}
        {currentChunk?.semanticType === 'graph_pattern' && (
          <div className="mt-4 px-4">
            <GraphPreview chunk={currentChunk} />
          </div>
        )}
      </div>

      {/* 오른쪽 패널: 점자 출력 상태 (보호자용) */}
      <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
        <BrailleStatusPanel
          currentChunk={currentChunk}
          isConnected={isConnected}
          chunkIndex={currentChunkIndex}
          totalChunks={chunks.length}
        />
      </div>
    </div>
  );
}

