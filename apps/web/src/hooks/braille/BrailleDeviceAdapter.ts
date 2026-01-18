/**
 * Adapter Pattern - Braille Device Adapter Interface
 * 점자 디바이스 어댑터 인터페이스
 */
export interface BrailleDeviceAdapter {
  /**
   * 디바이스 연결
   */
  connect(): Promise<void>;

  /**
   * 디바이스 연결 해제
   */
  disconnect(): Promise<void>;

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean;

  /**
   * 점자 셀 배열 전송
   */
  writeCells(cells: number[][]): Promise<void>;

  /**
   * 텍스트를 점자로 변환하여 전송
   */
  writeText(text: string): Promise<void>;

  /**
   * 디바이스 이름
   */
  getDeviceName(): string | null;

  /**
   * 에러 메시지
   */
  getError(): string | null;
}


