#include "braille.h"
#include "BrailleMap.h"
#include "BrailleConverter.h"
#include <SoftwareSerial.h>
#include <avr/pgmspace.h>
#include <string.h>

// 블루투스 모듈 설정
#define BT_RX_PIN 12
#define BT_TX_PIN 13
#define BT_BAUD 9600

SoftwareSerial BTSerial(BT_RX_PIN, BT_TX_PIN);

int dataPin = 2;
int latchPin = 3;
int clockPin = 4;
int no_module = 3;

braille bra(dataPin, latchPin, clockPin, no_module);

// 전역 변수 (메모리 최적화)
char sentenceBuffer[24] = "";
uint8_t sentenceIndex = 0;
unsigned long lastCharTime = 0;
const unsigned long CHAR_DISPLAY_DURATION = 2000;

// 함수 선언
void processInput(const char* str);
void displayBraille(uint8_t cellIndex, uint8_t dots[6]);
void displayCharForLearning(const char* str);
void outputBraillePatterns(const BrailleConversionResult& result);
void outputBraillePatternToHardware(const BraillePattern& pattern, uint8_t cellIndex);
void test_all_dots_sequential();
void test_all_cells_all_dots();
void processSentenceSequentially();

void setup() {
  Serial.begin(9600);
  delay(100);
  BTSerial.begin(BT_BAUD);
  
  while (Serial.available()) Serial.read();
  while (BTSerial.available()) BTSerial.read();
  
  bra.begin();
  delay(500);
  bra.all_off();
  bra.refresh();
  
  Serial.println("=== 점자 디스플레이 시스템 시작 ===");
  Serial.println("입력: test, all, 또는 한글 자음/모음");
}

void loop() {
  // PC 시리얼 입력 처리
  static char inputBuffer[24] = "";
  static uint8_t inputIndex = 0;
  static unsigned long lastInputTime = 0;
  
  while (Serial.available() > 0) {
    char c = Serial.read();
    lastInputTime = millis();
    
    if (c == '\n' || c == '\r') {
      if (inputIndex > 0) {
        inputBuffer[inputIndex] = '\0';
        processInput(inputBuffer);
        inputIndex = 0;
      }
    } else if (c == '\b' || c == 127) {
      if (inputIndex > 0) inputIndex--;
    } else if (inputIndex < 23) {
      inputBuffer[inputIndex++] = c;
      inputBuffer[inputIndex] = '\0';
    }
  }
  
  // 타임아웃 처리 (300ms)
  if (inputIndex > 0 && (millis() - lastInputTime > 300)) {
    inputBuffer[inputIndex] = '\0';
    processInput(inputBuffer);
    inputIndex = 0;
  }
  
  // 블루투스 입력 처리
  static char btBuffer[24] = "";
  static uint8_t btIndex = 0;
  static unsigned long lastBTTime = 0;
  
  while (BTSerial.available() > 0) {
    char c = BTSerial.read();
    lastBTTime = millis();
    
    Serial.print("[BT] 바이트: 0x");
    Serial.print((uint8_t)c, HEX);
    Serial.print(" (");
    if (c >= 32 && c <= 126) Serial.print(c);
    else if (c == '\n') Serial.print("\\n");
    else if (c == '\r') Serial.print("\\r");
    else Serial.print("?");
    Serial.print(") 인덱스:");
    Serial.println(btIndex);
    
    if (c == '\n' || c == '\r') {
      if (btIndex > 0) {
        btBuffer[btIndex] = '\0';
        Serial.print("[BT] 수신 완료: [");
        Serial.print(btBuffer);
        Serial.print("] 길이:");
        Serial.print(btIndex);
        Serial.print(" 바이트:");
        for (uint8_t i = 0; i < btIndex && i < 10; i++) {
          Serial.print(" 0x");
          Serial.print((uint8_t)btBuffer[i], HEX);
        }
        Serial.println();
        processInput(btBuffer);
        btIndex = 0;
      }
    } else if (c == '\b' || c == 127) {
      if (btIndex > 0) btIndex--;
    } else if (btIndex < 23) {
      btBuffer[btIndex++] = c;
      btBuffer[btIndex] = '\0';
    }
  }
  
  // 블루투스 타임아웃 처리
  if (btIndex > 0 && (millis() - lastBTTime > 300)) {
    btBuffer[btIndex] = '\0';
    Serial.print("[BT] 타임아웃: [");
    Serial.print(btBuffer);
    Serial.print("] 길이:");
    Serial.print(btIndex);
    Serial.print(" 바이트:");
    for (uint8_t i = 0; i < btIndex && i < 10; i++) {
      Serial.print(" 0x");
      Serial.print((uint8_t)btBuffer[i], HEX);
    }
    Serial.println();
    processInput(btBuffer);
    btIndex = 0;
  }
  
  // 문장 순차 출력
  processSentenceSequentially();
}

void displayCharForLearning(const char* str) {
  Serial.print("[displayChar] 검색: [");
  Serial.print(str);
  Serial.println("]");
  
  uint8_t dots[6] = {0};
  bool isFound = false;
  bool isSequence = false;
  
  // 초성 자음
  if (strcmp(str, "ㄱ") == 0) { dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㄴ") == 0) { dots[0] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㄷ") == 0) { dots[1] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㄹ") == 0) { dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅁ") == 0) { dots[0] = 1; dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅂ") == 0) { dots[3] = 1; dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅅ") == 0) { dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅇ") == 0) { dots[0] = 1; dots[1] = 1; dots[3] = 1; dots[4] = 1; isFound = true; } // 1,2,4,5번 점
  else if (strcmp(str, "ㅈ") == 0) { dots[3] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅊ") == 0) { dots[4] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅋ") == 0) { dots[0] = 1; dots[1] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㅌ") == 0) { dots[0] = 1; dots[1] = 1; dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅍ") == 0) { dots[0] = 1; dots[3] = 1; dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅎ") == 0) { dots[1] = 1; dots[3] = 1; dots[4] = 1; isFound = true; }
  
  // 된소리
  else if (strcmp(str, "ㄲ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,0,0,1,0,0};
    displayBraille(0, step1);
    delay(500);
    displayBraille(0, step2);
    isFound = true;
  }
  else if (strcmp(str, "ㄸ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,1,0,1,0,0};
    displayBraille(0, step1);
    delay(500);
    displayBraille(0, step2);
    isFound = true;
  }
  else if (strcmp(str, "ㅃ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,0,0,1,1,0};
    displayBraille(0, step1);
    delay(500);
    displayBraille(0, step2);
    isFound = true;
  }
  else if (strcmp(str, "ㅆ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,0,0,0,0,1};
    displayBraille(0, step1);
    delay(500);
    displayBraille(0, step2);
    isFound = true;
  }
  else if (strcmp(str, "ㅉ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,0,0,1,0,1};
    displayBraille(0, step1);
    delay(500);
    displayBraille(0, step2);
    isFound = true;
  }
  
  // 모음
  else if (strcmp(str, "ㅏ") == 0) { dots[0] = 1; dots[1] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅑ") == 0) { dots[2] = 1; dots[3] = 1; dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅓ") == 0) { dots[1] = 1; dots[2] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㅕ") == 0) { dots[0] = 1; dots[4] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅗ") == 0) { dots[0] = 1; dots[2] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅛ") == 0) { dots[2] = 1; dots[3] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅜ") == 0) { dots[0] = 1; dots[2] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㅠ") == 0) { dots[0] = 1; dots[3] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅡ") == 0) { dots[1] = 1; dots[3] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅣ") == 0) { dots[0] = 1; dots[2] = 1; dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅐ") == 0) { dots[0] = 1; dots[1] = 1; dots[2] = 1; dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅔ") == 0) { dots[0] = 1; dots[2] = 1; dots[3] = 1; dots[4] = 1; isFound = true; }
  else if (strcmp(str, "ㅒ") == 0) { dots[2] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㅖ") == 0) { dots[2] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㅘ") == 0) { dots[0] = 1; dots[1] = 1; dots[2] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅙ") == 0) { dots[0] = 1; dots[1] = 1; dots[2] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅚ") == 0) { dots[0] = 1; dots[2] = 1; dots[3] = 1; dots[4] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅝ") == 0) { dots[0] = 1; dots[1] = 1; dots[2] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㅞ") == 0) { dots[0] = 1; dots[1] = 1; dots[2] = 1; dots[3] = 1; isFound = true; }
  else if (strcmp(str, "ㅢ") == 0) { dots[1] = 1; dots[3] = 1; dots[4] = 1; dots[5] = 1; isFound = true; }
  else if (strcmp(str, "ㅟ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {1,0,1,1,0,0};
    uint8_t step2[6] = {1,1,1,0,1,0};
    displayBraille(0, step1);
    delay(500);
    displayBraille(0, step2);
    isFound = true;
  }
  
  // 출력 처리
  if (isFound && !isSequence) {
    Serial.print("[displayChar] 매칭 성공! 패턴:");
    for (uint8_t i = 0; i < 6; i++) Serial.print(dots[i]);
    Serial.println();
    displayBraille(0, dots);
  } else if (!isFound) {
    Serial.print("[displayChar] 매칭 실패! 길이:");
    Serial.println(strlen(str));
    uint8_t len = strlen(str);
    if (len > 3) {
      if (len > 23) len = 23;
      strncpy(sentenceBuffer, str, len);
      sentenceBuffer[len] = '\0';
      sentenceIndex = 0;
      lastCharTime = 0;
    } else {
      BrailleConversionResult result;
      if (convertToBraille(str, result)) {
        outputBraillePatterns(result);
      }
    }
  }
}

void displayBraille(uint8_t cellIndex, uint8_t dots[6]) {
  if (cellIndex >= 3) return;
  for (uint8_t i = 0; i < 6; i++) bra.off(cellIndex, i);
  for (uint8_t i = 0; i < 6; i++) {
    if (dots[i] == 1) bra.on(cellIndex, i);
  }
  bra.refresh();
}

void processInput(const char* str) {
  Serial.print("[processInput] 입력: [");
  Serial.print(str);
  Serial.print("] 길이:");
  Serial.println(strlen(str));
  
  if (strcmp(str, "test") == 0) {
    test_all_dots_sequential();
    return;
  }
  if (strcmp(str, "all") == 0) {
    test_all_cells_all_dots();
    return;
  }
  
  // 새 입력 시 문장 버퍼 초기화
  if (sentenceBuffer[0] != '\0') {
    sentenceBuffer[0] = '\0';
    sentenceIndex = 0;
    lastCharTime = 0;
    bra.all_off();
    bra.refresh();
  }
  
  if (strlen(str) > 0) {
    displayCharForLearning(str);
  }
}

void outputBraillePatternToHardware(const BraillePattern& pattern, uint8_t cellIndex) {
  if (cellIndex >= 3) return;
  for (uint8_t i = 0; i < 6; i++) bra.off(cellIndex, i);
  
  uint8_t dots[6] = {0};
  for (uint8_t i = 0; i < pattern.count; i++) {
    uint8_t dotNumber = pattern.dots[i];
    if (dotNumber >= 1 && dotNumber <= 6) {
      dots[dotNumber - 1] = 1;
    }
  }
  
  for (uint8_t i = 0; i < 6; i++) {
    if (dots[i] == 1) bra.on(cellIndex, i);
  }
}

void outputBraillePatterns(const BrailleConversionResult& result) {
  bra.all_off();
  if (result.count == 0) { bra.refresh(); return; }
  uint8_t cellsToUse = (result.count < 3) ? result.count : 3;
  for (uint8_t i = 0; i < cellsToUse; i++) {
    outputBraillePatternToHardware(result.patterns[i], i);
  }
  bra.refresh();
}

void test_all_dots_sequential() {
  Serial.println("테스트: 1~6번 점 순차 점등");
  bra.all_off();
  for (uint8_t dot = 0; dot < 6; dot++) {
    bra.all_off();
    bra.on(0, dot);
    bra.refresh();
    Serial.print("점 ");
    Serial.print(dot + 1);
    Serial.println("번 켜짐");
    delay(500);
  }
  bra.all_off();
  bra.refresh();
  Serial.println("테스트 완료");
}

void test_all_cells_all_dots() {
  bra.all_off();
  for (uint8_t cell = 0; cell < 3; cell++) {
    for (uint8_t dot = 0; dot < 6; dot++) bra.on(cell, dot);
  }
  bra.refresh();
}

void processSentenceSequentially() {
  if (sentenceBuffer[0] == '\0') return;
  if (Serial.available() || BTSerial.available()) return;
  if (sentenceIndex > 100) {
    sentenceBuffer[0] = '\0';
    sentenceIndex = 0;
    lastCharTime = 0;
    return;
  }
  
  unsigned long currentTime = millis();
  if (lastCharTime == 0 || (currentTime - lastCharTime >= CHAR_DISPLAY_DURATION)) {
    uint8_t bufferLen = strlen(sentenceBuffer);
    if (bufferLen == 0) {
      sentenceBuffer[0] = '\0';
      sentenceIndex = 0;
      lastCharTime = 0;
      return;
    }
    
    uint8_t byteIndex = 0;
    for (uint8_t i = 0; i < sentenceIndex && byteIndex < bufferLen; i++) {
      unsigned char c = (unsigned char)sentenceBuffer[byteIndex];
      if ((c & 0x80) == 0x00) byteIndex += 1;
      else if ((c & 0xE0) == 0xC0) byteIndex += 2;
      else if ((c & 0xF0) == 0xE0) byteIndex += 3;
      else if ((c & 0xF8) == 0xF0) byteIndex += 4;
      else byteIndex += 1;
    }
    
    if (byteIndex >= bufferLen) {
      sentenceBuffer[0] = '\0';
      sentenceIndex = 0;
      lastCharTime = 0;
      bra.all_off();
      bra.refresh();
      return;
    }
    
    unsigned char c = (unsigned char)sentenceBuffer[byteIndex];
    uint8_t charBytes = 1;
    if ((c & 0x80) == 0x00) charBytes = 1;
    else if ((c & 0xE0) == 0xC0) charBytes = 2;
    else if ((c & 0xF0) == 0xE0) charBytes = 3;
    else if ((c & 0xF8) == 0xF0) charBytes = 4;
    
    char currentChar[5] = "";
    if (byteIndex + charBytes <= bufferLen) {
      strncpy(currentChar, &sentenceBuffer[byteIndex], charBytes);
      currentChar[charBytes] = '\0';
      
      BrailleConversionResult result;
      if (convertToBraille(currentChar, result)) {
        outputBraillePatterns(result);
      }
      
      sentenceIndex++;
      lastCharTime = currentTime;
    }
  }
}