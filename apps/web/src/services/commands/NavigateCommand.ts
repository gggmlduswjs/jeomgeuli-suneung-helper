/**
 * Command Pattern - Navigate Commands
 * 네비게이션 관련 명령
 */
import { Command } from './Command';
import { useNavigate } from 'react-router-dom';

export class NavigateCommand implements Command {
  constructor(
    private path: string,
    private navigate: ReturnType<typeof useNavigate>
  ) {}

  execute(): void {
    this.navigate(this.path);
  }

  canExecute(): boolean {
    return !!this.path && !!this.navigate;
  }
}

export class NavigateBackCommand implements Command {
  constructor(
    private navigate: ReturnType<typeof useNavigate>
  ) {}

  execute(): void {
    this.navigate(-1);
  }

  canExecute(): boolean {
    return !!this.navigate;
  }
}

export class NavigateHomeCommand implements Command {
  constructor(
    private navigate: ReturnType<typeof useNavigate>
  ) {}

  execute(): void {
    this.navigate('/');
  }

  canExecute(): boolean {
    return !!this.navigate;
  }
}


