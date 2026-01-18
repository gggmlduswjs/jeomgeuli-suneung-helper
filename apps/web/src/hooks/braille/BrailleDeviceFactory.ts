/**
 * Factory Pattern - Braille Device Factory
 * 점자 디바이스 어댑터 생성 팩토리
 */
import { BrailleDeviceAdapter } from './BrailleDeviceAdapter';
import { OrbitReaderAdapter } from './OrbitReaderAdapter';
import { GenericBLEAdapter } from './GenericBLEAdapter';
import { MockBrailleAdapter } from './MockBrailleAdapter';

export type BrailleDeviceType = 'orbit' | 'generic' | 'mock' | 'auto';

export interface BrailleDeviceConfig {
  type?: BrailleDeviceType;
  serviceUUID?: string;
  charUUID?: string;
  namePrefix?: string;
}

export class BrailleDeviceFactory {
  /**
   * 점자 디바이스 어댑터 생성
   */
  static create(config: BrailleDeviceConfig = {}): BrailleDeviceAdapter {
    const type = config.type || 'auto';

    switch (type) {
      case 'orbit':
        return new OrbitReaderAdapter();
      
      case 'generic':
        return new GenericBLEAdapter(
          config.serviceUUID,
          config.charUUID,
          config.namePrefix
        );
      
      case 'mock':
        return new MockBrailleAdapter();
      
      case 'auto':
      default:
        // 자동 감지: 환경 변수나 설정에서 확인
        const envType = process.env.REACT_APP_BRAILLE_DEVICE_TYPE as BrailleDeviceType;
        if (envType && envType !== 'auto') {
          return this.create({ ...config, type: envType });
        }
        
        // 기본값: Generic
        return new GenericBLEAdapter(
          config.serviceUUID,
          config.charUUID,
          config.namePrefix
        );
    }
  }
}


