/**
 * 음성 알림 유틸리티
 * 블록 전환 시 알림음 재생 및 타임스탬프 관리
 * 
 * 개선 사항:
 * - TTS와 겹쳐서 재생 가능 (Web Audio API 사용)
 * - 매우 짧은 효과음 (0.1~0.15초)
 * - TTS보다 낮은 볼륨 (60~70%)
 * - 무채색 사운드 (wood click, soft tick 느낌)
 */

/**
 * 짧은 효과음 재생 (미세 강조용)
 * TTS와 겹쳐서 재생되며, 학습 흐름을 방해하지 않는 미세한 강조 신호
 * 
 * @param type 효과음 타입
 * @param delay 재생 지연 시간 (초) - TTS 시작 후 언제 재생할지
 */
export function playNotificationSound(
  type: 'block' | 'section' | 'explanation' | 'note' | 'instruction' = 'block',
  delay: number = 0
): void {
  try {
    const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContext) {
      console.warn('AudioContext를 지원하지 않는 브라우저입니다.');
      return;
    }

    const ctx = new AudioContext();
    const startTime = ctx.currentTime + delay;

    // 알림음 타입에 따라 주파수와 패턴 조정
    // 모든 효과음: 0.1~0.15초, 볼륨 0.1~0.12 (TTS보다 작게)
    switch (type) {
      case 'explanation':
        // 해설: 800Hz soft tick (팅) - 부드러운 단일 클릭
        const oscExp = ctx.createOscillator();
        const gainExp = ctx.createGain();
        oscExp.frequency.value = 800;
        oscExp.type = 'sine';
        // 볼륨: 0.1 (TTS의 60% 수준)
        gainExp.gain.setValueAtTime(0.1, startTime);
        gainExp.gain.exponentialRampToValueAtTime(0.01, startTime + 0.12);
        oscExp.connect(gainExp);
        gainExp.connect(ctx.destination);
        oscExp.start(startTime);
        oscExp.stop(startTime + 0.12);
        oscExp.onended = () => ctx.close();
        break;
        
      case 'note':
        // 필기: 600Hz soft tick 두 번 (팅팅) - 중요 내용 강조
        // 첫 번째 클릭
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.frequency.value = 600;
        osc1.type = 'sine';
        gain1.gain.setValueAtTime(0.1, startTime);
        gain1.gain.exponentialRampToValueAtTime(0.01, startTime + 0.08);
        osc1.connect(gain1);
        gain1.connect(ctx.destination);
        osc1.start(startTime);
        osc1.stop(startTime + 0.08);
        
        // 두 번째 클릭 (0.08초 후)
        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.frequency.value = 600;
        osc2.type = 'sine';
        gain2.gain.setValueAtTime(0.1, startTime + 0.08);
        gain2.gain.exponentialRampToValueAtTime(0.01, startTime + 0.16);
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.start(startTime + 0.08);
        osc2.stop(startTime + 0.16);
        
        // 정리
        osc2.onended = () => ctx.close();
        break;
        
      case 'instruction':
        // 지시: 1000Hz muted chime (툭) - 문제 풀이 등 명확한 신호
        const oscInst = ctx.createOscillator();
        const gainInst = ctx.createGain();
        oscInst.frequency.value = 1000;
        oscInst.type = 'sine';
        // 볼륨: 0.12 (약간 더 명확하게)
        gainInst.gain.setValueAtTime(0.12, startTime);
        gainInst.gain.exponentialRampToValueAtTime(0.01, startTime + 0.15);
        oscInst.connect(gainInst);
        gainInst.connect(ctx.destination);
        oscInst.start(startTime);
        oscInst.stop(startTime + 0.15);
        oscInst.onended = () => ctx.close();
        break;
        
      case 'section':
        // 섹션 전환: 700Hz soft tick (딱)
        const oscSec = ctx.createOscillator();
        const gainSec = ctx.createGain();
        oscSec.frequency.value = 700;
        oscSec.type = 'sine';
        gainSec.gain.setValueAtTime(0.1, startTime);
        gainSec.gain.exponentialRampToValueAtTime(0.01, startTime + 0.1);
        oscSec.connect(gainSec);
        gainSec.connect(ctx.destination);
        oscSec.start(startTime);
        oscSec.stop(startTime + 0.1);
        oscSec.onended = () => ctx.close();
        break;
        
      default:
        // 블록 전환: 800Hz soft tick (팅)
        const oscBlock = ctx.createOscillator();
        const gainBlock = ctx.createGain();
        oscBlock.frequency.value = 800;
        oscBlock.type = 'sine';
        gainBlock.gain.setValueAtTime(0.1, startTime);
        gainBlock.gain.exponentialRampToValueAtTime(0.01, startTime + 0.12);
        oscBlock.connect(gainBlock);
        gainBlock.connect(ctx.destination);
        oscBlock.start(startTime);
        oscBlock.stop(startTime + 0.12);
        oscBlock.onended = () => ctx.close();
        break;
    }
  } catch (error) {
    console.error('효과음 재생 실패:', error);
  }
}

/**
 * TTS 텍스트에서 핵심 포인트 위치 찾기
 * 문장 중간 호흡 지점을 찾아 효과음 삽입 위치 반환
 * 
 * @param text TTS 텍스트
 * @returns 효과음 삽입 위치 (초 단위, 대략적인 추정)
 */
export function findEmphasisPoint(text: string): number | null {
  if (!text || text.length < 10) return null;
  
  // 핵심 키워드 패턴
  const emphasisPatterns = [
    /핵심은/,
    /중요한 것은/,
    /정리하면/,
    /결론적으로/,
    /요약하면/,
    /특히/,
    /주의/,
    /기억/,
    /필수/,
    /반드시/
  ];
  
  // 텍스트 길이 기반 대략적인 시간 추정 (한글 기준 약 3자/초)
  const estimatedDuration = text.length / 3;
  
  // 패턴 매칭하여 중간 지점 찾기
  for (const pattern of emphasisPatterns) {
    const match = text.match(pattern);
    if (match && match.index !== undefined) {
      // 매칭된 위치를 시간으로 변환 (대략적인 추정)
      const positionRatio = match.index / text.length;
      return estimatedDuration * positionRatio;
    }
  }
  
  // 패턴이 없으면 중간 지점 반환
  return estimatedDuration * 0.4; // 40% 지점
}

/**
 * 타임스탬프 저장 인터페이스
 */
export interface BlockTimestamp {
  block_id: string;
  unit_id: string;
  timestamp: number; // 초 단위
  block_type: string;
  text_type?: 'explanation' | 'note' | 'instruction'; // 해설, 필기, 지시
}

/**
 * 타임스탬프 관리 클래스
 */
export class TimestampManager {
  private timestamps: Map<string, BlockTimestamp> = new Map();
  private currentTimestamp: number = 0;

  /**
   * 블록 타임스탬프 추가
   */
  addTimestamp(timestamp: BlockTimestamp): void {
    this.timestamps.set(timestamp.block_id || timestamp.unit_id, timestamp);
  }

  /**
   * 블록 ID로 타임스탬프 조회
   */
  getTimestamp(blockId: string): BlockTimestamp | undefined {
    return this.timestamps.get(blockId);
  }

  /**
   * 현재 타임스탬프 설정
   */
  setCurrentTimestamp(timestamp: number): void {
    this.currentTimestamp = timestamp;
  }

  /**
   * 현재 타임스탬프 조회
   */
  getCurrentTimestamp(): number {
    return this.currentTimestamp;
  }

  /**
   * 모든 타임스탬프 조회
   */
  getAllTimestamps(): BlockTimestamp[] {
    return Array.from(this.timestamps.values()).sort((a, b) => a.timestamp - b.timestamp);
  }

  /**
   * 타임스탬프 초기화
   */
  clear(): void {
    this.timestamps.clear();
    this.currentTimestamp = 0;
  }
}

/**
 * 전역 타임스탬프 관리자 인스턴스
 */
export const timestampManager = new TimestampManager();
