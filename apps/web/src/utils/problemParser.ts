/**
 * 문제 파싱 유틸리티
 * 문제 텍스트에서 지문과 선택지를 추출
 */

export interface ProblemMetadata {
  problem_id?: string;
  choices?: string[];
  answer?: number;
  question_text?: string;
}

export interface ParsedProblem {
  questionText: string;
  choices: string[];
  problemNumber: string;
  correctAnswer?: number;
}

/**
 * 문제 번호 추출
 */
function extractProblemNumber(content: string, fallback?: string): string {
  const numMatch = content.match(/문제\s*(\d+)/i) || content.match(/(\d+)\s*번/);
  return fallback || numMatch?.[1] || '';
}

/**
 * 선택지 추출 (①~⑤ 형식)
 */
function extractChoices(content: string): string[] {
  const choices: string[] = [];
  const matches = content.matchAll(/[①-⑤]\s*([^①-⑤]+?)(?=[①-⑤]|$)/g);
  
  for (const match of matches) {
    choices.push(match[1].trim());
  }
  
  return choices;
}

/**
 * 문제 지문 추출 (선택지 제거 후 남은 텍스트)
 */
function extractQuestionText(content: string, choices: string[]): string {
  if (choices.length === 0) {
    return content.trim();
  }
  
  let questionText = content;
  // 선택지 패턴 제거
  for (const choice of choices) {
    questionText = questionText.replace(choice, '').trim();
  }
  
  // 첫 번째 줄이 문제 지문일 가능성이 높음
  const lines = content.split('\n').filter(line => line.trim());
  return lines[0] || questionText;
}

/**
 * 문제 텍스트 파싱
 */
export function parseProblemContent(
  content: string,
  problemNumber?: string
): ParsedProblem {
  const choices = extractChoices(content);
  const questionText = extractQuestionText(content, choices);
  const extractedNumber = extractProblemNumber(content, problemNumber);

  return {
    questionText: questionText || content,
    choices,
    problemNumber: extractedNumber,
  };
}

/**
 * 메타데이터에서 문제 데이터 생성
 */
export function createProblemFromMetadata(
  metadata: ProblemMetadata,
  fallbackContent: string,
  fallbackNumber?: string
): ParsedProblem {
  return {
    questionText: metadata.question_text || fallbackContent,
    choices: metadata.choices || [],
    problemNumber: metadata.problem_id || fallbackNumber || '',
    correctAnswer: metadata.answer,
  };
}

/**
 * 문제 타입 판단
 */
export function isMultipleChoice(problem: ParsedProblem | null): boolean {
  return problem !== null && problem.choices.length > 0;
}
