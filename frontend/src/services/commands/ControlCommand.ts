/**
 * Command Pattern - Control Commands
 * 제어 관련 명령 (재생, 일시정지, 정지 등)
 */
import { Command } from './Command';

export class NextCommand implements Command {
  constructor(private handler: () => void) {}

  execute(): void {
    this.handler();
  }

  canExecute(): boolean {
    return !!this.handler;
  }
}

export class PrevCommand implements Command {
  constructor(private handler: () => void) {}

  execute(): void {
    this.handler();
  }

  canExecute(): boolean {
    return !!this.handler;
  }
}

export class RepeatCommand implements Command {
  constructor(private handler: () => void) {}

  execute(): void {
    this.handler();
  }

  canExecute(): boolean {
    return !!this.handler;
  }
}

export class PauseCommand implements Command {
  constructor(private handler: () => void) {}

  execute(): void {
    this.handler();
  }

  canExecute(): boolean {
    return !!this.handler;
  }
}

export class StartCommand implements Command {
  constructor(private handler: () => void) {}

  execute(): void {
    this.handler();
  }

  canExecute(): boolean {
    return !!this.handler;
  }
}

export class StopCommand implements Command {
  constructor(private handler: () => void) {}

  execute(): void {
    this.handler();
  }

  canExecute(): boolean {
    return !!this.handler;
  }
}


