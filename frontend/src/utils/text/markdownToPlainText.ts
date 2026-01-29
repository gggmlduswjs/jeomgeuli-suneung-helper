/**
 * 마크다운 텍스트를 TTS용 일반 텍스트로 변환
 * 특수기호를 제거하고 자연스러운 읽기 형태로 변환
 */
export function markdownToPlainText(markdown: string): string {
  if (!markdown) return '';

  let text = markdown;

  // 헤더 제거 (#, ##, ### 등)
  text = text.replace(/^#{1,6}\s+/gm, '');

  // 볼드/이탤릭 제거 (**텍스트**, *텍스트*, __텍스트__, _텍스트_)
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
  text = text.replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/__([^_]+)__/g, '$1');
  text = text.replace(/_([^_]+)_/g, '$1');

  // 코드 블록 제거 (```코드```, `코드`)
  text = text.replace(/```[\s\S]*?```/g, '');
  text = text.replace(/`([^`]+)`/g, '$1');

  // 링크 제거 ([텍스트](URL) → 텍스트)
  text = text.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1');

  // 이미지 제거 (![alt](URL))
  text = text.replace(/!\[([^\]]*)\]\([^\)]+\)/g, '');

  // 리스트 마커 제거 (-, *, +, 숫자.)
  text = text.replace(/^[\s]*[-*+]\s+/gm, '');
  text = text.replace(/^\d+\.\s+/gm, '');

  // 인용 블록 제거 (>)
  text = text.replace(/^>\s+/gm, '');

  // 수평선 제거 (---, ***)
  text = text.replace(/^[-*]{3,}$/gm, '');

  // HTML 태그 제거
  text = text.replace(/<[^>]+>/g, '');

  // 연속된 공백/줄바꿈 정리
  text = text.replace(/\n{3,}/g, '\n\n');
  text = text.replace(/[ \t]+/g, ' ');

  // 앞뒤 공백 제거
  text = text.trim();

  return text;
}
