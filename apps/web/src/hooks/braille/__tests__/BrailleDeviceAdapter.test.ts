/**
 * Adapter Pattern - Braille Device Adapter Tests
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { MockBrailleAdapter } from '../MockBrailleAdapter';
import { BrailleDeviceFactory } from '../BrailleDeviceFactory';

describe('MockBrailleAdapter', () => {
  let adapter: MockBrailleAdapter;

  beforeEach(() => {
    adapter = new MockBrailleAdapter();
  });

  it('should connect successfully', async () => {
    await adapter.connect();
    expect(adapter.isConnected()).toBe(true);
  });

  it('should disconnect successfully', async () => {
    await adapter.connect();
    await adapter.disconnect();
    expect(adapter.isConnected()).toBe(false);
  });

  it('should write cells', async () => {
    await adapter.connect();
    const cells = [[1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0]];
    
    await adapter.writeCells(cells);
    const lastCells = adapter.getLastCells();
    
    expect(lastCells).toEqual(cells);
  });

  it('should write text', async () => {
    await adapter.connect();
    // Mock adapter는 간단한 변환을 수행
    await adapter.writeText('test');
    
    const lastCells = adapter.getLastCells();
    expect(lastCells.length).toBeGreaterThan(0);
  });

  it('should throw error when not connected', async () => {
    await expect(adapter.writeCells([[1, 0, 0, 0, 0, 0]])).rejects.toThrow();
  });
});

describe('BrailleDeviceFactory', () => {
  it('should create mock adapter', () => {
    const adapter = BrailleDeviceFactory.create({ type: 'mock' });
    expect(adapter).toBeInstanceOf(MockBrailleAdapter);
  });

  it('should create generic adapter by default', () => {
    const adapter = BrailleDeviceFactory.create({ type: 'generic' });
    expect(adapter).toBeDefined();
  });
});


