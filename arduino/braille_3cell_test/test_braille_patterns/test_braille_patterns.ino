/*
 * Arduino IDE에서 한글 점자 패턴 테스트 코드 (메모리 최적화 버전)
 * 
 * 목적:
 * 1. 각 한글 글자의 점자 패턴을 하드웨어에서 직접 테스트
 * 2. 올바른 패턴 값을 확인하여 ko_braille.json 검증
 * 3. 잘못된 패턴 발견 시 수정
 * 
 * 메모리 최적화:
 * - PROGMEM 사용 (문자열을 플래시 메모리에 저장)
 * - F() 매크로 사용 (Serial.print에서)
 * - String 클래스 제거 (char 배열 사용)
 * - description 문자열 제거
 * 
 * 하드웨어 동작:
 * - 단일 문자(ㄱ, ㄴ 등)는 첫 번째 셀(오른쪽)에만 표시
 * - setBraille3Cells(cell1, cell2, cell3): cell1=오른쪽, cell2=중간, cell3=왼쪽
 * 
 * 사용법:
 * 1. 이 코드를 Arduino IDE에 업로드
 * 2. Serial Monitor 열기 (115200 baud)
 * 3. 테스트 방법:
 *    - 수동 테스트: 16진수 패턴 입력 (예: 01, 03, 05)
 *    - 자동 테스트: 'test' 입력 → 모든 패턴 순차 출력
 *    - 특정 글자 테스트: 'ㄱ', 'ㄴ' 등 입력
 */

#include <avr/pgmspace.h>
#include <SoftwareSerial.h>

// 블루투스 모듈 설정 (HC-06/BT05)
// 아두이노 기준: RX=12, TX=13 (블루투스 모듈의 TX는 아두이노 RX에, 블루투스 모듈의 RX는 아두이노 TX에 연결)
#define BT_RX_PIN 12  // 아두이노 RX (블루투스 모듈 TX 연결)
#define BT_TX_PIN 13  // 아두이노 TX (블루투스 모듈 RX 연결)
#define BT_BAUD 9600

SoftwareSerial BTSerial(BT_RX_PIN, BT_TX_PIN);  // RX, TX 순서

const int DATA_PIN = 2;
const int LATCH_PIN = 3;
const int CLOCK_PIN = 4;

byte cellBuf[3] = {0, 0, 0};

// 패턴 데이터 구조 (메모리 최적화)
struct TestPattern {
  uint8_t pattern;  // 패턴 바이트 (0x00~0x3F)
  char name[4];      // 한글 글자 (UTF-8, 3바이트 + null terminator)
};

// 패턴 배열 (PROGMEM으로 플래시 메모리에 저장)
const TestPattern testPatterns[] PROGMEM = {
  // 기본 자음
  {0x01, "ㄱ"},  // [1,0,0,0,0,0] = 0x01
  {0x05, "ㄴ"},  // [1,0,1,0,0,0] = 0x05
  {0x13, "ㄷ"},  // [1,1,0,0,1,0] = 0x13
  {0x09, "ㄹ"},  // [1,0,0,1,0,0] = 0x09
  {0x0D, "ㅁ"},  // [1,0,1,1,0,0] = 0x0D
  {0x0B, "ㅂ"},  // [1,1,0,1,0,0] = 0x0B
  {0x0A, "ㅅ"},  // [0,1,0,1,0,0] = 0x0A
  {0x0C, "ㅇ"},  // [0,0,1,1,0,0] = 0x0C
  {0x11, "ㅈ"},  // [1,0,0,0,1,0] = 0x11
  {0x19, "ㅊ"},  // [1,0,0,1,1,0] = 0x19
  {0x15, "ㅋ"},  // [1,0,1,0,1,0] = 0x15
  {0x13, "ㅌ"},  // [1,1,0,0,1,0] = 0x13
  {0x1D, "ㅍ"},  // [1,0,1,1,1,0] = 0x1D
  {0x12, "ㅎ"},  // [0,1,0,0,1,0] = 0x12
  
  // 된소리
  {0x03, "ㄲ"},  // [1,1,0,0,0,0] = 0x03
  {0x33, "ㄸ"},  // [1,1,0,0,1,1] = 0x33
  {0x2B, "ㅃ"},  // [1,1,0,1,0,1] = 0x2B
  {0x1E, "ㅆ"},  // [0,1,1,1,1,0] = 0x1E
  {0x31, "ㅉ"},  // [1,0,0,0,1,1] = 0x31
  
  // 기본 모음
  {0x04, "ㅏ"},  // [0,0,1,0,0,0] = 0x04
  {0x14, "ㅑ"},  // [0,0,1,0,1,0] = 0x14
  {0x02, "ㅓ"},  // [0,1,0,0,0,0] = 0x02
  {0x12, "ㅕ"},  // [0,1,0,0,1,0] = 0x12
  {0x0C, "ㅗ"},  // [0,0,1,1,0,0] = 0x0C
  {0x1C, "ㅛ"},  // [0,0,1,1,1,0] = 0x1C
  {0x06, "ㅜ"},  // [0,1,1,0,0,0] = 0x06
  {0x16, "ㅠ"},  // [0,1,1,0,1,0] = 0x16
  {0x0A, "ㅡ"},  // [0,1,0,1,0,0] = 0x0A
  {0x08, "ㅣ"},  // [0,0,0,1,0,0] = 0x08
  
  // 복합 모음
  {0x24, "ㅐ"},  // [0,0,1,0,0,1] = 0x24
  {0x22, "ㅔ"},  // [0,1,0,0,0,1] = 0x22
  {0x34, "ㅒ"},  // [0,0,1,0,1,1] = 0x34
  {0x32, "ㅖ"},  // [0,1,0,0,1,1] = 0x32
  {0x2C, "ㅘ"},  // [0,0,1,1,0,1] = 0x2C
  {0x2C, "ㅙ"},  // [0,0,1,1,0,1] = 0x2C
  {0x2C, "ㅚ"},  // [0,0,1,1,0,1] = 0x2C
  {0x26, "ㅝ"},  // [0,1,1,0,0,1] = 0x26
  {0x26, "ㅞ"},  // [0,1,1,0,0,1] = 0x26
  {0x26, "ㅟ"},  // [0,1,1,0,0,1] = 0x26
  {0x2A, "ㅢ"},  // [0,1,0,1,0,1] = 0x2A
};

const int testCount = sizeof(testPatterns) / sizeof(testPatterns[0]);

// 입력 버퍼 (String 클래스 대신 사용)
char inputBuffer[20];

// 함수 선언
void processInput(char* buffer, int len);
void testCharUTF8(char* utf8, int len);
void sendPattern(uint8_t pattern, bool singleCell);
void setBraille3Cells(byte cell1, byte cell2, byte cell3);
void runAutoTest();
void printHelp();

void setup() {
  Serial.begin(115200);
  BTSerial.begin(BT_BAUD);  // 블루투스 초기화 (9600 baud)
  
  pinMode(DATA_PIN, OUTPUT);
  pinMode(LATCH_PIN, OUTPUT);
  pinMode(CLOCK_PIN, OUTPUT);
  
  digitalWrite(LATCH_PIN, LOW);
  digitalWrite(CLOCK_PIN, LOW);
  digitalWrite(DATA_PIN, LOW);
  
  // F() 매크로로 문자열을 플래시 메모리에서 읽기
  Serial.println(F("========================================"));
  Serial.println(F("  한글 점자 패턴 테스트 도구"));
  Serial.println(F("========================================"));
  Serial.println();
  Serial.println(F("사용법:"));
  Serial.println(F("  1. 16진수 패턴 입력: 01, 03, 05 등"));
  Serial.println(F("  2. 자동 테스트: 'test' 입력"));
  Serial.println(F("  3. 특정 글자 테스트: 'ㄱ', 'ㄴ' 등 입력"));
  Serial.println(F("  4. 도움말: 'help' 입력"));
  Serial.println();
  Serial.println(F("테스트 목적:"));
  Serial.println(F("  - 각 글자의 점자 패턴이 올바른지 확인"));
  Serial.println(F("  - ko_braille.json 데이터 검증"));
  Serial.println(F("  - 하드웨어 출력 확인"));
  Serial.println();
  Serial.println(F("주의: 단일 문자는 첫 번째 셀(오른쪽)에만 표시됩니다."));
  Serial.println();
  Serial.println(F("블루투스 연결 대기 중..."));
  Serial.println();
  
  // 초기화: 모든 셀 OFF
  setBraille3Cells(0x00, 0x00, 0x00);
  delay(100);
}

void loop() {
  // PC(Serial) 입력 처리
  if (Serial.available()) {
    // String 대신 char 배열 사용
    int len = Serial.readBytesUntil('\n', inputBuffer, sizeof(inputBuffer) - 1);
    inputBuffer[len] = '\0';
    
    // 공백 제거
    while (len > 0 && (inputBuffer[len-1] == ' ' || inputBuffer[len-1] == '\r')) {
      inputBuffer[--len] = '\0';
    }
    
    if (len > 0) {
      Serial.print(F("입력됨(PC): "));
      Serial.println(inputBuffer);
      processInput(inputBuffer, len);
    }
  }
  
  // 블루투스(BTSerial) 입력 처리
  if (BTSerial.available()) {
    // String 대신 char 배열 사용
    int len = BTSerial.readBytesUntil('\n', inputBuffer, sizeof(inputBuffer) - 1);
    inputBuffer[len] = '\0';
    
    // 공백 제거
    while (len > 0 && (inputBuffer[len-1] == ' ' || inputBuffer[len-1] == '\r')) {
      inputBuffer[--len] = '\0';
    }
    
    if (len > 0) {
      Serial.print(F("Received(BT): "));
      Serial.println(inputBuffer);
      processInput(inputBuffer, len);
    }
  }
}

// 입력 처리 함수 (Serial과 BTSerial 공통 사용)
void processInput(char* buffer, int len) {
  // 소문자 변환 (ASCII 문자만)
  for (int i = 0; i < len; i++) {
    if (buffer[i] >= 'A' && buffer[i] <= 'Z') {
      buffer[i] += 32;
    }
  }
  
  // 명령 처리
  if (strcmp(buffer, "test") == 0) {
    runAutoTest();
  } else if (strcmp(buffer, "help") == 0) {
    printHelp();
  } else if (strncmp(buffer, "0x", 2) == 0 || strncmp(buffer, "0X", 2) == 0) {
    // 16진수 입력 (0x01 형식)
    uint8_t pattern = (uint8_t)strtol(buffer, NULL, 16);
    sendPattern(pattern, true); // 단일 셀 모드
  } else if (len == 1) {
    // ASCII 단일 문자 입력 - testCharUTF8로 통합 처리
    testCharUTF8(buffer, 1);
  } else if (len == 3 && (buffer[0] & 0xF0) == 0xE0) {
    // UTF-8 한글 문자 입력 (3바이트, 첫 바이트가 0xE0~0xEF 범위)
    // 3바이트 전체를 비교
    testCharUTF8(buffer, 3);
  } else {
    // 16진수 입력 (01 형식) 또는 다른 명령
    uint8_t pattern = (uint8_t)strtol(buffer, NULL, 16);
    if (pattern > 0 || strcmp(buffer, "00") == 0) {
      sendPattern(pattern, true); // 단일 셀 모드
    } else {
      Serial.println(F("❌ 잘못된 입력입니다."));
      Serial.println(F("   'help'를 입력하여 사용법을 확인하세요."));
      Serial.println();
    }
  }
}

// 통합된 문자 테스트 함수 (ASCII 1바이트, UTF-8 3바이트 모두 처리)
void testCharUTF8(char* utf8, int len) {
  for (int i = 0; i < testCount; i++) {
    TestPattern pattern;
    memcpy_P(&pattern, &testPatterns[i], sizeof(TestPattern));
    
    // ASCII 문자 처리 (len == 1)
    if (len == 1 && pattern.name[0] == utf8[0] && pattern.name[1] == 0) {
      Serial.print(F("테스트: "));
      Serial.write((uint8_t)pattern.name[0]);
      Serial.print(F(" -> "));
      sendPattern(pattern.pattern, true);
      return;
    }
    
    // UTF-8 3바이트 한글 문자 처리 (len == 3)
    // 모든 한글 글자는 3바이트 전체를 비교해야 함
    if (len >= 3 && pattern.name[0] == utf8[0] && 
        pattern.name[1] == utf8[1] && 
        pattern.name[2] == utf8[2]) {
      Serial.print(F("테스트: "));
      // UTF-8 문자 출력 (Serial.write 사용)
      for (int j = 0; j < 3 && pattern.name[j] != '\0'; j++) {
        Serial.write((uint8_t)pattern.name[j]);
      }
      Serial.print(F(" -> "));
      sendPattern(pattern.pattern, true); // 단일 셀 모드
      return;
    }
  }
  
  Serial.print(F("❌ '"));
  for (int i = 0; i < len && i < 3; i++) {
    Serial.write((uint8_t)utf8[i]);
  }
  Serial.println(F("'에 대한 테스트 패턴을 찾을 수 없습니다."));
  Serial.println();
}

void sendPattern(uint8_t pattern, bool singleCell) {
  if (singleCell) {
    // 단일 패턴: 첫 번째 셀(오른쪽)만, 나머지는 0
    cellBuf[0] = pattern;
    cellBuf[1] = 0x00;
    cellBuf[2] = 0x00;
  } else {
    // 버퍼 이동 (여러 패턴 연속 전송 시 - 현재 미사용)
    cellBuf[2] = cellBuf[1];
    cellBuf[1] = cellBuf[0];
    cellBuf[0] = pattern;
  }
  
  // 출력 (cell1=오른쪽, cell2=중간, cell3=왼쪽)
  setBraille3Cells(cellBuf[0], cellBuf[1], cellBuf[2]);
  
  Serial.print(F("✅ 패턴 0x"));
  if (pattern < 0x10) Serial.print(F("0"));
  Serial.print(pattern, HEX);
  Serial.println(F(" 전송됨"));
  
  // 패턴 비트 분석 출력
  Serial.print(F("   비트: "));
  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) {
      Serial.print(F("DOT"));
      Serial.print(i + 1);
      Serial.print(F(" "));
    }
  }
  Serial.println();
  
  Serial.print(F("   배열: ["));
  for (int i = 0; i < 6; i++) {
    Serial.print((pattern >> i) & 1);
    if (i < 5) Serial.print(F(","));
  }
  Serial.println(F("]"));
  
  Serial.print(F("   버퍼: [Cell1(오른쪽)=0x"));
  if (cellBuf[0] < 0x10) Serial.print(F("0"));
  Serial.print(cellBuf[0], HEX);
  Serial.print(F(", Cell2(중간)=0x"));
  if (cellBuf[1] < 0x10) Serial.print(F("0"));
  Serial.print(cellBuf[1], HEX);
  Serial.print(F(", Cell3(왼쪽)=0x"));
  if (cellBuf[2] < 0x10) Serial.print(F("0"));
  Serial.print(cellBuf[2], HEX);
  Serial.println(F("]"));
  Serial.println(F("   👉 하드웨어 출력을 확인하세요!"));
  Serial.println();
}

void setBraille3Cells(byte cell1, byte cell2, byte cell3) {
  // 제공하신 테스트 코드와 동일한 함수
  // cell1 = 오른쪽, cell2 = 중간, cell3 = 왼쪽
  digitalWrite(LATCH_PIN, LOW);
  shiftOut(DATA_PIN, CLOCK_PIN, LSBFIRST, cell3);  // 셀3 (왼쪽)
  shiftOut(DATA_PIN, CLOCK_PIN, LSBFIRST, cell2);  // 셀2 (중간)
  shiftOut(DATA_PIN, CLOCK_PIN, LSBFIRST, cell1);  // 셀1 (오른쪽)
  digitalWrite(LATCH_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(LATCH_PIN, LOW);
}

void runAutoTest() {
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  자동 테스트 시작"));
  Serial.println(F("========================================"));
  Serial.print(F("총 "));
  Serial.print(testCount);
  Serial.println(F("개 패턴을 테스트합니다."));
  Serial.println(F("각 패턴을 3초씩 표시합니다."));
  Serial.println(F("하드웨어 출력을 확인하세요!"));
  Serial.println();
  Serial.println(F("⚠️  테스트를 중단하려면 Serial Monitor를 닫으세요."));
  Serial.println();
  delay(2000);
  
  TestPattern pattern;
  
  for (int i = 0; i < testCount; i++) {
    // PROGMEM에서 읽기
    memcpy_P(&pattern, &testPatterns[i], sizeof(TestPattern));
    
    Serial.print(F("["));
    Serial.print(i + 1);
    Serial.print(F("/"));
    Serial.print(testCount);
    Serial.print(F("] "));
    // UTF-8 문자 출력
    for (int j = 0; j < 3 && pattern.name[j] != '\0'; j++) {
      Serial.write((uint8_t)pattern.name[j]);
    }
    Serial.print(F(" - 패턴 0x"));
    if (pattern.pattern < 0x10) Serial.print(F("0"));
    Serial.println(pattern.pattern, HEX);
    
    sendPattern(pattern.pattern, true); // 단일 셀 모드
    
    delay(3000); // 3초 대기
    
    // 다음 테스트 전에 모든 셀 OFF
    setBraille3Cells(0x00, 0x00, 0x00);
    delay(500);
  }
  
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  자동 테스트 완료"));
  Serial.println(F("========================================"));
  Serial.println();
  Serial.println(F("📝 테스트 결과:"));
  Serial.println(F("  1. 각 패턴이 올바르게 출력되었는지 확인하세요."));
  Serial.println(F("  2. 잘못된 패턴이 있다면 ko_braille.json을 수정해야 합니다."));
  Serial.println(F("  3. 올바른 패턴 값을 기록하세요."));
  Serial.println();
}

void printHelp() {
  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F("  도움말"));
  Serial.println(F("========================================"));
  Serial.println();
  Serial.println(F("명령어:"));
  Serial.println(F("  test  - 모든 패턴 자동 테스트"));
  Serial.println(F("  help  - 이 도움말 표시"));
  Serial.println();
  Serial.println(F("입력 형식:"));
  Serial.println(F("  16진수 패턴: 01, 03, 05, 0x01 등"));
  Serial.println(F("  한글 글자: ㄱ, ㄴ, ㄷ 등"));
  Serial.println();
  Serial.println(F("예시:"));
  Serial.println(F("  > 01     → 패턴 0x01 출력 (첫 번째 셀만)"));
  Serial.println(F("  > 0x05   → 패턴 0x05 출력 (첫 번째 셀만)"));
  Serial.println(F("  > ㄱ     → 'ㄱ' 패턴 테스트 (첫 번째 셀만)"));
  Serial.println(F("  > test   → 모든 패턴 자동 테스트"));
  Serial.println();
  Serial.println(F("패턴 값 계산:"));
  Serial.println(F("  배열 [1,0,0,0,0,0] = 0x01 (DOT 1만)"));
  Serial.println(F("  배열 [1,0,1,0,0,0] = 0x05 (DOT 1,3)"));
  Serial.println(F("  배열 [1,1,0,0,0,0] = 0x03 (DOT 1,2)"));
  Serial.println();
  Serial.println(F("비트 매핑:"));
  Serial.println(F("  DOT 1 = bit 0 (LSB)"));
  Serial.println(F("  DOT 2 = bit 1"));
  Serial.println(F("  DOT 3 = bit 2"));
  Serial.println(F("  DOT 4 = bit 3"));
  Serial.println(F("  DOT 5 = bit 4"));
  Serial.println(F("  DOT 6 = bit 5 (MSB)"));
  Serial.println();
  Serial.println(F("셀 순서:"));
  Serial.println(F("  Cell1 = 오른쪽 (첫 번째 셀)"));
  Serial.println(F("  Cell2 = 중간"));
  Serial.println(F("  Cell3 = 왼쪽"));
  Serial.println();
}
