/**
 * Command Pattern Tests
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { CommandInvoker, getCommandInvoker } from '../CommandInvoker';
import { Command } from '../Command';

// Mock Command 구현
class MockCommand implements Command {
  executed = false;
  undone = false;

  execute(): void {
    this.executed = true;
  }

  undo(): void {
    this.undone = true;
  }

  canExecute(): boolean {
    return true;
  }
}

describe('CommandInvoker', () => {
  let invoker: CommandInvoker;

  beforeEach(() => {
    invoker = new CommandInvoker();
  });

  it('should execute command successfully', async () => {
    const command = new MockCommand();
    const result = await invoker.execute(command);

    expect(result.success).toBe(true);
    expect(command.executed).toBe(true);
  });

  it('should not execute command if canExecute returns false', async () => {
    const command = new MockCommand();
    command.canExecute = () => false;

    const result = await invoker.execute(command);

    expect(result.success).toBe(false);
    expect(command.executed).toBe(false);
  });

  it('should undo last command', async () => {
    const command = new MockCommand();
    await invoker.execute(command);

    const undoResult = await invoker.undo();

    expect(undoResult.success).toBe(true);
    expect(command.undone).toBe(true);
  });

  it('should return singleton instance', () => {
    const instance1 = getCommandInvoker();
    const instance2 = getCommandInvoker();

    expect(instance1).toBe(instance2);
  });

  it('should maintain command history', () => {
    const command1 = new MockCommand();
    const command2 = new MockCommand();

    invoker.execute(command1);
    invoker.execute(command2);

    const history = invoker.getHistory();
    expect(history.length).toBe(2);
  });
});


