/**
 * Adapter Pattern - Mock Braille Adapter
 * 테스트 및 개발용 모의 점자 디바이스 어댑터
 */
import { BrailleDeviceAdapter } from './BrailleDeviceAdapter';

export class MockBrailleAdapter implements BrailleDeviceAdapter {
  private connected: boolean = false;
  private deviceName: string = "Mock Braille Display";
  private error: string | null = null;
  private lastCells: number[][] = [];

  async connect(): Promise<void> {
    // 모의 연결 - 즉시 성공
    this.connected = true;
    this.error = null;
    console.log("[MockBrailleAdapter] 연결됨");
  }

  async disconnect(): Promise<void> {
    this.connected = false;
    this.error = null;
    console.log("[MockBrailleAdapter] 연결 해제됨");
  }

  isConnected(): boolean {
    return this.connected;
  }

  async writeCells(cells: number[][]): Promise<void> {
    if (!this.connected) {
      throw new Error("BLE 디바이스가 연결되지 않았습니다.");
    }

    this.lastCells = cells;
    console.log("[MockBrailleAdapter] 셀 전송:", cells);
  }

  async writeText(text: string): Promise<void> {
    if (!text.trim()) return;

    // 모의 변환: 각 문자를 간단한 패턴으로 변환
    const cells: number[][] = text.split('').map((char) => {
      const code = char.charCodeAt(0);
      return [
        (code >> 0) & 1,
        (code >> 1) & 1,
        (code >> 2) & 1,
        (code >> 3) & 1,
        (code >> 4) & 1,
        (code >> 5) & 1,
      ];
    });

    await this.writeCells(cells);
  }

  getDeviceName(): string | null {
    return this.deviceName;
  }

  getError(): string | null {
    return this.error;
  }

  /**
   * 마지막으로 전송된 셀 조회 (테스트용)
   */
  getLastCells(): number[][] {
    return this.lastCells;
  }
}


