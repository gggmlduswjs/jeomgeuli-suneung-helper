/**
 * 정답/오답 관련 타입 정의
 */
export interface Answer {
  answer_id: string;
  saved: boolean;
}

export interface AnswerCreate {
  user_id: string;
  unit_id: string;
  selected: number;
  is_correct: boolean;
}
