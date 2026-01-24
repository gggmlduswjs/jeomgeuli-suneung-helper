/**
 * 음성 명령어 매칭 유틸리티
 */
import { compareTwoStrings } from 'string-similarity';
import { COMMAND_PHRASES } from './commands';
import { normalize } from './normalizers';

/** 명령어 매칭 (퍼지 매칭 사용) */
export function matchCommand(text: string, threshold: number = 0.40): string | undefined {
  const t = normalize(text);
  let bestCmd: string | undefined;
  let bestScore = 0;
  
  for (const [cmd, phrases] of Object.entries(COMMAND_PHRASES)) {
    for (const phrase of phrases) {
      const score = compareTwoStrings(t, phrase);
      if (score > bestScore) {
        bestScore = score;
        bestCmd = cmd;
      }
    }
  }
  
  // "다음" 명령어는 더 관대한 임계값 적용 (0.30으로 낮춤)
  const finalThreshold = bestCmd === 'next' ? Math.min(threshold, 0.30) : threshold;
  
  // 임계값 이상이면 명령 반환
  if (bestScore >= finalThreshold) {
    console.log(`[VoiceCommands] 퍼지 매칭: "${text}" -> "${bestCmd}" (유사도: ${(bestScore * 100).toFixed(1)}%, 임계값: ${(finalThreshold * 100).toFixed(1)}%)`);
    return bestCmd;
  }
  
  return undefined;
}

/** 키워드 기반 유연한 매칭 (핵심 단어만 있어도 인식) */
export function fuzzyMatch(text: string, keywords: string[]): boolean {
  const normalized = text.toLowerCase();
  
  // 완전 일치
  for (const keyword of keywords) {
    if (normalized === keyword.toLowerCase()) return true;
    if (normalized.includes(keyword.toLowerCase())) return true;
  }
  
  // 첫 글자 매칭 (2-3글자 단어의 경우)
  for (const keyword of keywords) {
    if (keyword.length <= 3 && normalized.startsWith(keyword[0])) {
      return true;
    }
  }
  
  // 부분 문자열 매칭 (핵심 글자 포함)
  for (const keyword of keywords) {
    if (keyword.length >= 2) {
      const firstTwo = keyword.substring(0, 2).toLowerCase();
      if (normalized.includes(firstTwo)) return true;
    }
  }
  
  return false;
}

/** 간단한 유사도 계산 (Levenshtein 거리 기반) */
export function similarity(s1: string, s2: string): number {
  const longer = s1.length > s2.length ? s1 : s2;
  const shorter = s1.length > s2.length ? s2 : s1;
  
  if (longer.length === 0) return 1.0;
  
  // 완전 일치
  if (s1 === s2) return 1.0;
  
  // 부분 일치 (한 단어가 다른 단어에 포함)
  if (longer.includes(shorter)) return 0.8;
  if (shorter.includes(longer)) return 0.8;
  
  // 첫 글자 일치
  if (s1[0] === s2[0] && s1.length <= 3 && s2.length <= 3) return 0.6;
  
  // 간단한 편집 거리 (최대 1글자 차이)
  if (Math.abs(s1.length - s2.length) <= 1) {
    let diff = 0;
    const minLen = Math.min(s1.length, s2.length);
    for (let i = 0; i < minLen; i++) {
      if (s1[i] !== s2[i]) diff++;
    }
    if (diff <= 1) return 0.7;
  }
  
  return 0;
}

