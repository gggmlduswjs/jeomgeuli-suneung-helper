/**
 * Command Pattern - Command Invoker
 * 명령 실행 관리자
 */
import { Command, CommandResult } from './Command';

export class CommandInvoker {
  private history: Command[] = [];
  private maxHistorySize: number = 50;

  /**
   * 명령 실행
   */
  async execute(command: Command): Promise<CommandResult> {
    try {
      if (command.canExecute && !command.canExecute()) {
        return {
          success: false,
          message: 'Command cannot be executed',
        };
      }

      await command.execute();
      
      // 히스토리에 추가
      this.history.push(command);
      if (this.history.length > this.maxHistorySize) {
        this.history.shift();
      }

      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * 마지막 명령 실행 취소
   */
  async undo(): Promise<CommandResult> {
    const command = this.history.pop();
    if (!command || !command.undo) {
      return {
        success: false,
        message: 'No command to undo',
      };
    }

    try {
      await command.undo();
      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * 히스토리 초기화
   */
  clearHistory(): void {
    this.history = [];
  }

  /**
   * 히스토리 조회
   */
  getHistory(): Command[] {
    return [...this.history];
  }
}

// 싱글톤 인스턴스
let invokerInstance: CommandInvoker | null = null;

export function getCommandInvoker(): CommandInvoker {
  if (!invokerInstance) {
    invokerInstance = new CommandInvoker();
  }
  return invokerInstance;
}


