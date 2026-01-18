#!/usr/bin/env python3
"""
점글이 BLE → Serial Bridge 서버
Raspberry Pi 4에서 실행

HARDWARE_SPEC.md의 스펙을 준수합니다.
"""

from bluezero import peripheral
from serial import Serial
import sys
import time

# BLE 설정 (HARDWARE_SPEC.md에 명시된 값 - 불변)
DEVICE_NAME = "Jeomgeuli"
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "abcdabcd-1234-5678-1111-abcdefabcdef"

# Serial 설정
SERIAL_PORT = "/dev/ttyACM0"  # Arduino가 연결된 포트 (확인 필요)
BAUD_RATE = 115200

# Serial 연결
try:
    ser = Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"[Serial] {SERIAL_PORT} 연결됨 ({BAUD_RATE} baud)")
except Exception as e:
    print(f"[Serial] 연결 실패: {e}")
    print(f"[Serial] 사용 가능한 포트 확인: ls /dev/ttyACM* /dev/ttyUSB*")
    sys.exit(1)

def write_handler(value):
    """BLE Write → Serial 전송"""
    try:
        # BLE로 받은 데이터를 그대로 Serial로 전송
        ser.write(value)
        ser.flush()
        print(f"[BLE→Serial] {len(value)} 바이트 전송: {value.hex()}")
    except Exception as e:
        print(f"[BLE→Serial] 전송 실패: {e}")

# BLE 서버 생성
print(f"[BLE] 서버 초기화 중...")
print(f"[BLE] 디바이스 이름: {DEVICE_NAME}")
print(f"[BLE] Service UUID: {SERVICE_UUID}")
print(f"[BLE] Characteristic UUID: {CHAR_UUID}")

ble = peripheral.Peripheral(
    device_name=DEVICE_NAME,
    services=[{
        'uuid': SERVICE_UUID,
        'characteristics': [{
            'uuid': CHAR_UUID,
            'properties': ['write', 'write-without-response'],
            'write': write_handler
        }]
    }]
)

print(f"[BLE] 서버 시작. 연결 대기 중...")
try:
    ble.run()
except KeyboardInterrupt:
    print("\n[BLE] 서버 종료")
    ser.close()
    sys.exit(0)

