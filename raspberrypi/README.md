# Raspberry Pi BLE 서버

점글이 하드웨어 시스템의 BLE → Serial Bridge 서버입니다.

## 역할

Raspberry Pi는 React PWA와 Arduino 사이에서 BLE ↔ USB Serial bridge 역할을 수행합니다.

```
React PWA (Web Bluetooth)
    ↓ BLE
Raspberry Pi (BLE → Serial Bridge)
    ↓ USB Serial
Arduino UNO
```

## 사전 요구사항

- Raspberry Pi 4 (또는 BLE 지원 라즈베리파이)
- Python 3.8+
- Arduino가 USB로 연결되어 있어야 함

## 설치

### 1. 시스템 패키지 설치

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-serial
```

### 2. Python 패키지 설치

```bash
pip3 install bluezero
```

또는 시스템 전역 설치:

```bash
sudo pip3 install bluezero
```

## 설정

### Serial 포트 확인

Arduino가 연결된 Serial 포트를 확인합니다:

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

일반적으로 `/dev/ttyACM0` 또는 `/dev/ttyUSB0`입니다.

### 포트 변경

`ble_server.py` 파일의 `SERIAL_PORT` 변수를 수정합니다:

```python
SERIAL_PORT = "/dev/ttyACM0"  # 실제 포트로 변경
```

## 실행

### 기본 실행

```bash
sudo python3 raspberrypi/ble_server.py
```

**주의**: BLE 권한을 위해 `sudo`가 필요할 수 있습니다.

### 백그라운드 실행

```bash
sudo nohup python3 raspberrypi/ble_server.py > ble_server.log 2>&1 &
```

### systemd 서비스로 등록 (선택사항)

`/etc/systemd/system/jeomgeuli-ble.service` 파일 생성:

```ini
[Unit]
Description=Jeomgeuli BLE Server
After=bluetooth.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/jeomgeuli
ExecStart=/usr/bin/python3 /path/to/jeomgeuli/raspberrypi/ble_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

서비스 활성화:

```bash
sudo systemctl enable jeomgeuli-ble.service
sudo systemctl start jeomgeuli-ble.service
```

## 정상 동작 확인

### 1. 서버 시작 확인

정상적으로 시작되면 다음 메시지가 출력됩니다:

```
[Serial] /dev/ttyACM0 연결됨 (115200 baud)
[BLE] 서버 초기화 중...
[BLE] 디바이스 이름: Jeomgeuli
[BLE] Service UUID: 12345678-1234-5678-1234-56789abcdef0
[BLE] Characteristic UUID: abcdabcd-1234-5678-1111-abcdefabcdef
[BLE] 서버 시작. 연결 대기 중...
```

### 2. BLE 디바이스 확인

스마트폰이나 다른 BLE 스캐너에서 "Jeomgeuli" 디바이스가 보이는지 확인합니다.

### 3. 데이터 전송 확인

React PWA에서 데이터를 전송하면 다음 로그가 출력됩니다:

```
[BLE→Serial] 3 바이트 전송: ec9588...
```

## 문제 해결

### Serial 연결 실패

**증상**: `[Serial] 연결 실패` 메시지

**해결 방법**:
1. Arduino가 USB로 연결되어 있는지 확인
2. Serial 포트가 올바른지 확인: `ls /dev/ttyACM*`
3. 다른 프로그램이 Serial 포트를 사용 중인지 확인
4. 사용자 권한 확인: `sudo usermod -a -G dialout $USER` (재로그인 필요)

### BLE 서버 시작 실패

**증상**: `Permission denied` 또는 BLE 관련 오류

**해결 방법**:
1. `sudo`로 실행
2. Bluetooth 서비스 확인: `sudo systemctl status bluetooth`
3. BLE 어댑터 확인: `hciconfig`

### 디바이스를 찾을 수 없음

**증상**: React PWA에서 "Jeomgeuli" 디바이스를 찾을 수 없음

**해결 방법**:
1. BLE 서버가 실행 중인지 확인
2. Bluetooth가 활성화되어 있는지 확인: `bluetoothctl show`
3. 디바이스 이름이 정확한지 확인 (대소문자 구분)
4. BLE 광고가 시작되었는지 로그 확인

### 데이터가 전송되지 않음

**증상**: React PWA에서 전송했지만 Arduino에서 수신되지 않음

**해결 방법**:
1. `[BLE→Serial]` 로그가 출력되는지 확인
2. Serial 포트가 올바른지 확인
3. Arduino Serial 모니터에서 데이터 수신 확인
4. 보드레이트가 115200인지 확인

## 참고 자료

- [HARDWARE_SPEC.md](../docs/HARDWARE_SPEC.md): 전체 하드웨어 스펙
- [bluezero 문서](https://github.com/ukBaz/python-bluezero): Python BLE 라이브러리

