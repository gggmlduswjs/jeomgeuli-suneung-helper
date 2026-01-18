# Arduino 펌웨어

점글이 하드웨어 시스템의 Arduino UNO 펌웨어입니다.

## 역할

Arduino는 PC(Serial) 또는 블루투스(BTSerial)로부터 텍스트를 수신하여 점자 모듈을 제어합니다.

```
PC/프론트엔드 (Serial/BLE)
    ↓ 텍스트 전송 (UTF-8)
Arduino UNO (텍스트 수신 → 한글 자모 분리 → 점자 변환)
    ↓ GPIO (D2, D3, D4)
JY-SOFT 점자 모듈 (3셀)
```

## 하드웨어 요구사항

- Arduino UNO (또는 호환 보드)
- JY-SOFT 스마트 점자 모듈 × 3 (3셀 버전, 총 18-dot)
- Shift Register (74HC595) × 3
- 5핀 케이블
- 5V, 2A 이상 전원 어댑터 (3셀 구동용)
- 블루투스 모듈 (HC-05/HC-06, 선택사항)

## 하드웨어 연결

### Arduino와 점자 모듈 연결

| 점자 모듈 | Arduino UNO | 설명 |
|-----------|-------------|------|
| VCC (빨간색) | 5V | 전원 공급 |
| GND | GND | 그라운드 |
| DATA | D2 | 시리얼 데이터 입력 |
| LATCH | D3 | 래치 신호 |
| CLOCK | D4 | 클럭 신호 |

### 블루투스 모듈 연결 (선택사항)

| 블루투스 모듈 | Arduino UNO | 설명 |
|---------------|-------------|------|
| TX | D12 (RX) | 블루투스 → Arduino |
| RX | D13 (TX) | Arduino → 블루투스 |
| VCC | 5V | 전원 공급 |
| GND | GND | 그라운드 |

### 전원 공급

- 점자 모듈: 5V, 2A 이상 어댑터 권장
- Arduino: USB 전원 또는 외부 전원

## 소프트웨어 요구사항

### Arduino IDE

1. [Arduino IDE 다운로드](https://www.arduino.cc/en/software)
2. Arduino IDE 설치

### braille.h 라이브러리

JY-SOFT 점자 모듈은 `braille.h` 라이브러리를 사용합니다.

**라이브러리 위치**:
- `arduino/braille_3cell/braille.h`
- `arduino/braille_3cell/braille.cpp`

**라이브러리 사용법**:
```cpp
#include "braille.h"

braille bra(DATA_PIN, LATCH_PIN, CLOCK_PIN, MODULE_COUNT);
bra.begin();
bra.on(cellIndex, dotIndex);  // dotIndex: 0-5 (Dot 1-6)
bra.off(cellIndex, dotIndex);
bra.refresh();
```

## 펌웨어 파일

### 메인 펌웨어

- **`braille_3cell/braille_3cell.ino`**: 메인 펌웨어
  - 3셀 점자 모듈 제어
  - Serial/BTSerial 통신으로 텍스트 수신
  - UTF-8 디코딩 및 한글 자모 분리
  - 초성/중성/종성을 각각 다른 셀에 출력
  - 2024년 개정 한국점자 규정 적용

### 테스트 코드

- **`braille_3cell_test/integration_test/integration_test.ino`**: 통합 테스트
- **`braille_3cell_test/test_braille_patterns/test_braille_patterns.ino`**: 점자 패턴 테스트

## 펌웨어 업로드

### 1. 보드 선택

Arduino IDE에서:
- 도구 → 보드 → Arduino UNO

### 2. 포트 선택

Arduino가 USB로 연결된 포트를 선택:
- 도구 → 포트 → COM 포트 (Windows) 또는 /dev/ttyACM0 (Linux)

### 3. 업로드

- 스케치 → 업로드 (Ctrl+U)

### 4. 업로드 확인

시리얼 모니터를 열어 확인:
- 도구 → 시리얼 모니터
- 보드레이트: **9600**
- 다음 메시지가 출력되면 성공:
  ```
  === 점자 디스플레이 시스템 (통합 버전) 시작 ===
  블루투스나 PC로 한글을 입력하세요. (예: 가, 안녕, ㄱ, test)
  ```

## 사용법

### 시리얼 모니터에서 테스트

1. 시리얼 모니터 열기 (보드레이트: 9600)
2. 줄바꿈 설정: "새 줄" 선택
3. 입력창에 텍스트 입력:
   - `test`: 1~6번 점 순차 테스트
   - `all`: 모든 셀의 모든 점 켜기
   - `cell1`, `cell2`, `cell3`: 특정 셀의 모든 점 켜기
   - `가`, `안녕`, `ㄱ`: 한글 텍스트 입력 (점자로 변환되어 출력)

### 프론트엔드에서 사용

프론트엔드는 Web Serial API 또는 BLE를 통해 텍스트를 전송합니다:
- 텍스트는 UTF-8 인코딩으로 전송
- 각 텍스트는 개행 문자(`\n`)로 구분
- Arduino는 한 글자씩 처리하여 점자로 출력

## 동작 원리

### 1. 텍스트 수신

```cpp
String str = Serial.readStringUntil('\n');
```

### 2. UTF-8 디코딩

```cpp
// 1바이트: ASCII 문자
// 2바이트: 일부 특수 문자
// 3바이트: 한글 (완성형, 자음, 모음)
```

### 3. 한글 자모 분리

```cpp
// 완성형 한글 (가~힣): 초성/중성/종성 분리
// 자음 낱자 (ㄱ~ㅎ): 초성 매핑
// 모음 낱자 (ㅏ~ㅣ): 중성 매핑
```

### 4. 점자 출력

- **셀 0**: 초성 (첫소리)
- **셀 1**: 중성 (가운뎃소리)
- **셀 2**: 종성 (받침)

각 글자는 1.5초 표시 후 다음 글자로 이동합니다.

## 점자 매핑 규칙

### 초성 (첫소리)

- ㄱ: Dot 4
- ㄴ: Dot 1, 4
- ㄷ: Dot 2, 4
- ㄹ: Dot 5
- ㅁ: Dot 1, 5
- ㅂ: Dot 4, 5
- ㅅ: Dot 6
- ㅇ: 점 없음 (표기 안 함)
- ㅈ: Dot 4, 6
- ㅊ: Dot 5, 6
- ㅋ: Dot 1, 2, 4
- ㅌ: Dot 1, 2, 5
- ㅍ: Dot 1, 4, 5
- ㅎ: Dot 2, 4, 5

### 중성 (가운뎃소리)

- ㅏ: Dot 1, 2, 6
- ㅑ: Dot 3, 4, 5
- ㅓ: Dot 2, 3, 4
- ㅕ: Dot 1, 5, 6
- ㅗ: Dot 1, 3, 6
- ㅛ: Dot 3, 4, 6
- ㅜ: Dot 1, 3, 4
- ㅠ: Dot 1, 4, 6
- ㅡ: Dot 2, 4, 6
- ㅣ: Dot 1, 3, 5
- ㅐ: Dot 1, 2, 3, 5
- ㅔ: Dot 1, 3, 4, 5

### 종성 (받침)

- ㄱ: Dot 1
- ㄴ: Dot 2, 4
- ㄷ: Dot 3, 4
- ㄹ: Dot 2
- ㅁ: Dot 2, 6
- ㅂ: Dot 1, 2
- ㅅ: Dot 3
- ㅇ: Dot 2, 5
- ㅈ: Dot 3, 5
- ㅊ: Dot 3, 5, 6
- ㅋ: Dot 2, 3, 6
- ㅌ: Dot 2, 3, 5
- ㅍ: Dot 2, 5, 6
- ㅎ: Dot 2, 3, 5, 6

**주의**: 종성 점자는 초성과 다릅니다!

## 문제 해결

### 업로드 실패

**증상**: "avrdude: stk500_getsync()" 오류

**해결 방법**:
1. Arduino가 올바른 포트에 연결되어 있는지 확인
2. 다른 프로그램이 Serial 포트를 사용 중인지 확인
3. Arduino 보드 선택이 올바른지 확인
4. USB 케이블이 데이터 전송을 지원하는지 확인

### 점자가 출력되지 않음

**증상**: Serial 모니터에는 로그가 출력되지만 점자가 나오지 않음

**해결 방법**:
1. 점자 모듈 전원 확인 (5V, 2A 이상, 3셀 구동용)
2. 핀 연결 확인 (D2, D3, D4)
3. `test` 명령어로 하드웨어 구동 테스트 먼저 수행
4. 점자 모듈의 LED나 상태 표시 확인

### 점자가 잘못된 위치에 나타남

**증상**: 점자가 올라오지만 예상한 위치가 아님

**해결 방법**:
1. `braille.cpp`의 `DOT_MAP` 확인
2. `shiftOut` 방향 확인: `MSBFIRST` 사용
3. `test` 명령어로 각 DOT가 올바른 위치에 나타나는지 확인

### Serial 데이터 수신 안 됨

**증상**: 프론트엔드에서 전송했지만 Arduino에서 수신되지 않음

**해결 방법**:
1. Serial 모니터에서 데이터 수신 확인
2. 보드레이트가 9600인지 확인
3. USB 케이블 연결 확인
4. Arduino가 다른 프로그램에서 사용 중인지 확인
5. 시리얼 모니터의 줄바꿈 설정 확인 ("새 줄" 선택)

### 한글 점자 변환 오류

**증상**: 한글 문자가 올바른 점자로 변환되지 않음

**해결 방법**:
1. `displayHangulChar()` 함수의 매핑 확인
2. UTF-8 디코딩 로직 확인
3. 시리얼 모니터에서 입력 텍스트 확인

## 확인된 설정

테스트 코드로 확인된 하드웨어 설정:

- **shiftOut 방향**: `MSBFIRST`
- **셀 전송 순서**: 셀3 → 셀2 → 셀1 (왼쪽 → 중간 → 오른쪽 표시)
- **DOT 매핑**:
  - Dot 1 → 비트 2
  - Dot 2 → 비트 4
  - Dot 3 → 비트 6
  - Dot 4 → 비트 3
  - Dot 5 → 비트 5
  - Dot 6 → 비트 7

## 참고 자료

- [2024년 개정 한국점자 규정](../docs/2024년 개정 한국점자 규정.pdf)
- [HARDWARE.md](../docs/HARDWARE.md): 전체 하드웨어 스펙
- [Arduino 공식 문서](https://www.arduino.cc/reference/en/)
