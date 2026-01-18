/**
 * 교재 관련 타입 정의
 */
export enum ParseStatus {
  PENDING = "PENDING",
  PROCESSING = "PROCESSING",
  DONE = "DONE",
  FAILED = "FAILED",
}

export enum Subject {
  KOREAN = "KOREAN",
  ENGLISH = "ENGLISH",
  MATH = "MATH",
}

export interface Book {
  book_id: string;
  title: string;
  subject: Subject;
  year?: number;
  parse_status: ParseStatus;
  lesson_count?: number;
}

export interface BookCreate {
  title: string;
  subject: Subject;
  year?: number;
}

export interface BookParseStatus {
  book_id: string;
  status: ParseStatus;
  progress: number;
}
