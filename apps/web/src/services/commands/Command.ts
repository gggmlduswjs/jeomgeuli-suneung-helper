/**
 * Command Pattern - Command Interface
 * 모든 명령의 기본 인터페이스
 */
export interface Command {
  execute(): void | Promise<void>;
  undo?(): void | Promise<void>;
  canExecute?(): boolean;
}

/**
 * Command Result
 */
export interface CommandResult {
  success: boolean;
  message?: string;
  data?: any;
}


