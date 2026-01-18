/**
 * Command Pattern - Learning Commands
 * 학습 관련 명령
 */
import { Command } from './Command';

export class SelectItemCommand implements Command {
  constructor(
    private handler: (index: number) => void,
    private index: number
  ) {}

  execute(): void {
    this.handler(this.index);
  }

  canExecute(): boolean {
    return !!this.handler && this.index >= 0;
  }
}

export class SubmitAnswerCommand implements Command {
  constructor(
    private handler: (answer: number) => void,
    private answer: number
  ) {}

  execute(): void {
    this.handler(this.answer);
  }

  canExecute(): boolean {
    return !!this.handler && this.answer > 0;
  }
}

export class MarkLearnedCommand implements Command {
  constructor(
    private handler: (queueId: number, grade: number) => void,
    private queueId: number,
    private grade: number = 3
  ) {}

  execute(): void {
    this.handler(this.queueId, this.grade);
  }

  canExecute(): boolean {
    return !!this.handler && this.queueId > 0;
  }
}


