/**
 * Adapter Pattern - Generic BLE Braille Display Adapter
 * 일반적인 BLE 점자 디스플레이 어댑터
 */
import { BrailleDeviceAdapter } from './BrailleDeviceAdapter';

export class GenericBLEAdapter implements BrailleDeviceAdapter {
  private device: BluetoothDevice | null = null;
  private characteristic: BluetoothRemoteGATTCharacteristic | null = null;
  private deviceName: string | null = null;
  private error: string | null = null;

  private readonly SERVICE_UUID: string;
  private readonly CHAR_UUID: string;
  private readonly NAME_PREFIX: string;

  constructor(
    serviceUUID: string = "0000180a-0000-1000-8000-00805f9b34fb",
    charUUID: string = "00002a29-0000-1000-8000-00805f9b34fb",
    namePrefix: string = "Braille"
  ) {
    this.SERVICE_UUID = serviceUUID;
    this.CHAR_UUID = charUUID;
    this.NAME_PREFIX = namePrefix;
  }

  async connect(): Promise<void> {
    try {
      this.error = null;

      if (!('bluetooth' in navigator)) {
        throw new Error("Bluetooth API를 지원하지 않는 브라우저입니다.");
      }

      if (this.device && this.device.gatt?.connected) {
        return;
      }

      if (this.device) {
        try {
          const server = await this.device.gatt?.connect();
          if (server) {
            const service = await server.getPrimaryService(this.SERVICE_UUID);
            const char = await service.getCharacteristic(this.CHAR_UUID);
            this.characteristic = char;
            this.deviceName = this.device.name || "점자 디스플레이";
            return;
          }
        } catch {
          // 재연결 실패 시 새로 연결
        }
      }

      const newDevice = await (navigator as any).bluetooth.requestDevice({
        filters: [
          { namePrefix: this.NAME_PREFIX },
          { namePrefix: "점자" },
          { services: [this.SERVICE_UUID] }
        ],
        optionalServices: [this.SERVICE_UUID]
      });

      const server = await newDevice.gatt?.connect();
      if (!server) {
        throw new Error("GATT 서버 연결에 실패했습니다.");
      }

      const service = await server.getPrimaryService(this.SERVICE_UUID);
      const char = await service.getCharacteristic(this.CHAR_UUID);

      this.device = newDevice;
      this.characteristic = char;
      this.deviceName = newDevice.name || "점자 디스플레이";

      newDevice.addEventListener("gattserverdisconnected", () => {
        this.characteristic = null;
        this.error = "디바이스 연결이 끊어졌습니다.";
      });

    } catch (error: any) {
      this.error = error?.message || "BLE 연결에 실패했습니다.";
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (this.device?.gatt?.connected) {
      this.device.gatt.disconnect();
    }
    this.device = null;
    this.characteristic = null;
    this.deviceName = null;
    this.error = null;
  }

  isConnected(): boolean {
    return this.device?.gatt?.connected === true && this.characteristic !== null;
  }

  async writeCells(cells: number[][]): Promise<void> {
    if (!this.characteristic || !this.isConnected()) {
      throw new Error("BLE 디바이스가 연결되지 않았습니다.");
    }

    try {
      const buffer = new Uint8Array(cells.length);
      cells.forEach((cell, idx) => {
        buffer[idx] = cell.reduce((acc, dot, i) => {
          return acc | ((dot ? 1 : 0) << i);
        }, 0);
      });

      await this.characteristic.writeValue(buffer);
    } catch (error: any) {
      this.error = `전송 실패: ${error?.message || '알 수 없는 오류'}`;
      throw error;
    }
  }

  async writeText(text: string): Promise<void> {
    if (!text.trim()) return;

    try {
      const response = await fetch('/api/braille/convert/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        throw new Error('점자 변환 실패');
      }

      const data = await response.json();
      if (data.cells && Array.isArray(data.cells)) {
        await this.writeCells(data.cells);
      } else {
        throw new Error('잘못된 응답 형식');
      }
    } catch (error: any) {
      this.error = `텍스트 전송 실패: ${error?.message || '알 수 없는 오류'}`;
      throw error;
    }
  }

  getDeviceName(): string | null {
    return this.deviceName;
  }

  getError(): string | null {
    return this.error;
  }
}


