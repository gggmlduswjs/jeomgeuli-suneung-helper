// 글로벌 타입 정의
declare global {
  // API 응답 타입
  interface Response {
    answer?: string;
    chat_markdown?: string;
    keywords?: string[];
    braille_words?: string[];
    mode?: string;
    actions?: Record<string, any>;
    meta?: Record<string, any>;
    error?: string;
    news?: any[];
    query?: string;
    ok?: boolean;
    data?: any;
  }

  // Bluetooth API 타입 정의
  interface Navigator {
    bluetooth?: {
      requestDevice(options: {
        filters: Array<{ namePrefix?: string; services?: string[] }>;
        optionalServices?: string[];
      }): Promise<BluetoothDevice>;
    };
  }
  
  interface BluetoothDevice {
    gatt?: BluetoothRemoteGATTServer;
    addEventListener(type: string, listener: () => void): void;
  }
  
  interface BluetoothRemoteGATTServer {
    connect(): Promise<BluetoothRemoteGATTServer>;
    connected: boolean;
    disconnect(): void;
    getPrimaryService(service: string): Promise<BluetoothRemoteGATTService>;
  }
  
  interface BluetoothRemoteGATTService {
    getCharacteristic(characteristic: string): Promise<BluetoothRemoteGATTCharacteristic>;
  }
  
  interface BluetoothRemoteGATTCharacteristic {
    writeValue(data: Uint8Array): Promise<void>;
  }
}

export {};
