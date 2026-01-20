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

// 버튼 핀 정의 (내부 풀업 사용)
// 첫 번째 버튼 스위치 고장 가능성 - A5로 변경
#define BUTTON_PREV_PIN A5   // 버튼 1: 이전 문자 (A1에서 A5로 변경)
#define BUTTON_NEXT_PIN A2   // 버튼 2: 다음 문자
#define BUTTON_PLAY_PIN A3   // 버튼 3: 재생/일시정지
#define BUTTON_SPEED_PIN A4  // 버튼 4: 속도 조절

// 전역 변수 (메모리 최적화)
char sentenceBuffer[16] = "";  // 24 → 16으로 줄임 (8 bytes 절약)
uint8_t sentenceIndex = 0;
unsigned long lastCharTime = 0;
unsigned long charDisplayDuration = 2000;  // 기본 2초, 버튼으로 조절 가능
bool isPaused = false;  // 재생/일시정지 상태
uint8_t speedLevel = 1;  // 속도 레벨 (1=느림, 2=보통, 3=빠름)

// 함수 선언
void processInput(const char* str);
void displayBraille(uint8_t cellIndex, uint8_t dots[6], bool doRefresh = false);
void displayCharForLearning(const char* str);
void displayPatternOnCell(uint8_t cellNum, const char* str);
void outputBraillePatterns(const BrailleConversionResult& result);
void outputBraillePatternToHardware(const BraillePattern& pattern, uint8_t cellIndex);
void test_all_dots_sequential();
void test_all_cells_all_dots();
void test_each_cell_individual();
void test_specific_cell(uint8_t cellNum);
void processSentenceSequentially();
void checkButtons();
void handleButtonPrev();
void handleButtonNext();
void handleButtonPlay();
void handleButtonSpeed();
uint8_t getCurrentCharByteIndex();
void displayCurrentChar();

void setup() {
  Serial.begin(9600);
  delay(100);
  BTSerial.begin(BT_BAUD);
  
  while (Serial.available()) Serial.read();
  while (BTSerial.available()) BTSerial.read();
  
  bra.begin();
  delay(100);  // begin() 내부에서 이미 딜레이가 있으므로 줄임
  bra.all_off();
  bra.refresh();
  delay(50);  // 초기화 완료 후 안정화
  
  // 버튼 핀 초기화 (내부 풀업 활성화)
  pinMode(BUTTON_PREV_PIN, INPUT_PULLUP);
  pinMode(BUTTON_NEXT_PIN, INPUT_PULLUP);
  pinMode(BUTTON_PLAY_PIN, INPUT_PULLUP);
  pinMode(BUTTON_SPEED_PIN, INPUT_PULLUP);
  
  // 버튼 핀 초기화 확인 (버튼 3개만 사용)
  delay(10);  // 안정화 대기
  Serial.print("[INIT] A2 핀 상태 (버튼1-이전): ");
  Serial.println(digitalRead(BUTTON_NEXT_PIN) == LOW ? "LOW" : "HIGH");
  Serial.print("[INIT] A3 핀 상태 (버튼2-다음): ");
  Serial.println(digitalRead(BUTTON_PLAY_PIN) == LOW ? "LOW" : "HIGH");
  Serial.print("[INIT] A4 핀 상태 (버튼3-재생/일시정지): ");
  Serial.println(digitalRead(BUTTON_SPEED_PIN) == LOW ? "LOW" : "HIGH");
  
  Serial.println("=== 점자 디스플레이 시스템 시작 ===");
  Serial.println("명령어:");
  Serial.println("  test     - 셀0의 점 1~6 순차 테스트");
  Serial.println("  all      - 모든 셀 전체 점등");
  Serial.println("  cells    - 각 셀별 순차 테스트");
  Serial.println("  cell0    - 셀0만 테스트");
  Serial.println("  cell1    - 셀1만 테스트");
  Serial.println("  cell2    - 셀2만 테스트");
  Serial.println("  0:ㄱ     - 셀0에 'ㄱ' 출력");
  Serial.println("  1:ㅏ     - 셀1에 'ㅏ' 출력");
  Serial.println("  2:ㅎ     - 셀2에 'ㅎ' 출력");
  Serial.println("  ㄱ, ㅏ 등 - 기본 (셀0에 출력)");
  Serial.println("\n버튼 제어 (버튼 3개만 사용):");
  Serial.println("  버튼1 (A2) - 이전 문자");
  Serial.println("  버튼2 (A3) - 다음 문자");
  Serial.println("  버튼3 (A4) - 재생/일시정지");
}

void loop() {
  // PC 시리얼 입력 처리
  static char inputBuffer[16] = "";  // 24 → 16으로 줄임 (8 bytes 절약)
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
    } else if (inputIndex < 15) {  // 23 → 15로 변경
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
  static char btBuffer[16] = "";  // 24 → 16으로 줄임 (8 bytes 절약)
  static uint8_t btIndex = 0;
  static unsigned long lastBTTime = 0;
  
  while (BTSerial.available() > 0) {
    char c = BTSerial.read();
    lastBTTime = millis();
    
    // 디버그 메시지 제거 (메모리 절약)
    // Serial.print("[BT] 바이트: 0x");
    // Serial.print((uint8_t)c, HEX);
    // Serial.print(" (");
    // if (c >= 32 && c <= 126) Serial.print(c);
    // else if (c == '\n') Serial.print("\\n");
    // else if (c == '\r') Serial.print("\\r");
    // else Serial.print("?");
    // Serial.print(") 인덱스:");
    // Serial.println(btIndex);
    
    if (c == '\n' || c == '\r') {
      if (btIndex > 0) {
        btBuffer[btIndex] = '\0';
        // Serial.print("[BT] 수신 완료: [");
        // Serial.print(btBuffer);
        // Serial.print("] 길이:");
        // Serial.print(btIndex);
        // Serial.print(" 바이트:");
        // for (uint8_t i = 0; i < btIndex && i < 10; i++) {
        //   Serial.print(" 0x");
        //   Serial.print((uint8_t)btBuffer[i], HEX);
        // }
        // Serial.println();
        processInput(btBuffer);
        btIndex = 0;
      }
    } else if (c == '\b' || c == 127) {
      if (btIndex > 0) btIndex--;
    } else if (btIndex < 15) {  // 23 → 15로 변경
      btBuffer[btIndex++] = c;
      btBuffer[btIndex] = '\0';
    }
  }
  
  // 블루투스 타임아웃 처리
  if (btIndex > 0 && (millis() - lastBTTime > 300)) {
    btBuffer[btIndex] = '\0';
    // Serial.print("[BT] 타임아웃: [");
    // Serial.print(btBuffer);
    // Serial.print("] 길이:");
    // Serial.print(btIndex);
    // Serial.print(" 바이트:");
    // for (uint8_t i = 0; i < btIndex && i < 10; i++) {
    //   Serial.print(" 0x");
    //   Serial.print((uint8_t)btBuffer[i], HEX);
    // }
    // Serial.println();
    processInput(btBuffer);
    btIndex = 0;
  }
  
  // 버튼 입력 확인
  checkButtons();
  
  // 문장 순차 출력
  processSentenceSequentially();
}

void displayCharForLearning(const char* str) {
  displayPatternOnCell(0, str);
}

void displayBraille(uint8_t cellIndex, uint8_t dots[6], bool doRefresh = false) {
  if (cellIndex >= 3) return;
  // 먼저 해당 셀의 모든 점을 명확하게 끄기
  for (uint8_t i = 0; i < 6; i++) bra.off(cellIndex, i);
  
  // 그 다음 원하는 점들을 켜기
  for (uint8_t i = 0; i < 6; i++) {
    if (dots[i] == 1) bra.on(cellIndex, i);
  }
  
  // doRefresh가 true일 때만 refresh (단일 셀 출력 시)
  if (doRefresh) {
    bra.refresh();
    delayMicroseconds(100);
  }
}

void processInput(const char* str) {
  // 디버그 메시지 제거 (메모리 절약)
  // Serial.print("[processInput] 입력: [");
  // Serial.print(str);
  // Serial.print("] 길이:");
  // Serial.println(strlen(str));
  
  if (strcmp(str, "test") == 0) {
    test_all_dots_sequential();
    return;
  }
  if (strcmp(str, "all") == 0) {
    test_all_cells_all_dots();
    return;
  }
  if (strcmp(str, "cells") == 0) {
    test_each_cell_individual();
    return;
  }
  if (strcmp(str, "cell0") == 0) {
    test_specific_cell(0);
    return;
  }
  if (strcmp(str, "cell1") == 0) {
    test_specific_cell(1);
    return;
  }
  if (strcmp(str, "cell2") == 0) {
    test_specific_cell(2);
    return;
  }
  
  // 셀 번호 지정: "0:ㄱ", "1:ㅏ", "2:ㅎ"
  if (strlen(str) >= 3 && str[1] == ':') {
    uint8_t cellNum = str[0] - '0';
    if (cellNum >= 0 && cellNum <= 2) {
      const char* charToPrint = str + 2;
      // Serial.print("[processInput] 셀 ");
      // Serial.print(cellNum);
      // Serial.print("에 출력: ");
      // Serial.println(charToPrint);
      displayPatternOnCell(cellNum, charToPrint);
      return;
    }
  }
  
  // 여러 셀 동시 출력: "0:ㄱ 1:ㅏ 2:ㅎ" 또는 "012" (셀 번호만)
  if (strlen(str) == 3 && str[0] >= '0' && str[0] <= '2' && 
      str[1] >= '0' && str[1] <= '2' && str[2] >= '0' && str[2] <= '2') {
    // "012" 형식: 셀 0, 1, 2에 각각 기본 패턴 출력 (테스트용)
    bra.all_off();
    bra.refresh();
    delayMicroseconds(200);
    
    // 각 셀에 간단한 패턴 출력 (테스트)
    uint8_t testDots0[6] = {1,0,0,0,0,0};  // 셀 0: 점 1
    uint8_t testDots1[6] = {0,1,0,0,0,0};  // 셀 1: 점 2
    uint8_t testDots2[6] = {0,0,1,0,0,0};  // 셀 2: 점 3
    
    // 모든 셀의 상태를 먼저 설정 (refresh 없이)
    displayBraille(0, testDots0, false);
    displayBraille(1, testDots1, false);
    displayBraille(2, testDots2, false);
    // 모든 셀 설정 후 한 번만 refresh
    bra.refresh();
    // Serial.println("[processInput] 셀 0,1,2 테스트 패턴 출력");
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

void displayPatternOnCell(uint8_t cellNum, const char* str) {
  if (cellNum >= 3) return;
  
  // 디버그 메시지 제거 (메모리 절약)
  // Serial.print("[displayPattern] 셀 ");
  // Serial.print(cellNum);
  // Serial.print("에 [");
  // Serial.print(str);
  // Serial.println("] 출력");
  
  // 모든 셀을 명확하게 끄고 반영
  bra.all_off();
  bra.refresh();
  delayMicroseconds(200);  // 상태 초기화 안정화
  
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
  else if (strcmp(str, "ㅇ") == 0) { dots[0] = 1; dots[1] = 1; dots[3] = 1; dots[4] = 1; isFound = true; }
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
    displayBraille(cellNum, step1, true);
    delay(500);
    displayBraille(cellNum, step2, true);
    isFound = true;
  }
  else if (strcmp(str, "ㄸ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,1,0,1,0,0};
    displayBraille(cellNum, step1, true);
    delay(500);
    displayBraille(cellNum, step2, true);
    isFound = true;
  }
  else if (strcmp(str, "ㅃ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,0,0,1,1,0};
    displayBraille(cellNum, step1, true);
    delay(500);
    displayBraille(cellNum, step2, true);
    isFound = true;
  }
  else if (strcmp(str, "ㅆ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,0,0,0,0,1};
    displayBraille(cellNum, step1, true);
    delay(500);
    displayBraille(cellNum, step2, true);
    isFound = true;
  }
  else if (strcmp(str, "ㅉ") == 0) {
    isSequence = true;
    uint8_t step1[6] = {0,0,0,0,0,1};
    uint8_t step2[6] = {0,0,0,1,0,1};
    displayBraille(cellNum, step1, true);
    delay(500);
    displayBraille(cellNum, step2, true);
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
    displayBraille(cellNum, step1, true);
    delay(500);
    displayBraille(cellNum, step2, true);
    isFound = true;
  }
  
  if (isFound && !isSequence) {
    // Serial.print("패턴: ");
    // for (uint8_t i = 0; i < 6; i++) Serial.print(dots[i]);
    // Serial.println();
    displayBraille(cellNum, dots, true);  // 단일 셀 출력이므로 refresh=true
  } else if (!isFound) {
    // Serial.println("매칭 실패! BrailleConverter 사용");
    uint8_t len = strlen(str);
    if (len > 3) {
      if (len > 15) len = 15;  // 23 → 15로 변경
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

void outputBraillePatternToHardware(const BraillePattern& pattern, uint8_t cellIndex) {
  if (cellIndex >= 3) return;
  // 먼저 해당 셀의 모든 점을 명확하게 끄기
  for (uint8_t i = 0; i < 6; i++) bra.off(cellIndex, i);
  
  uint8_t dots[6] = {0};
  for (uint8_t i = 0; i < pattern.count; i++) {
    uint8_t dotNumber = pattern.dots[i];
    if (dotNumber >= 1 && dotNumber <= 6) {
      dots[dotNumber - 1] = 1;
    }
  }
  
  // 원하는 점들을 켜기
  for (uint8_t i = 0; i < 6; i++) {
    if (dots[i] == 1) bra.on(cellIndex, i);
  }
}

void outputBraillePatterns(const BrailleConversionResult& result) {
  // 모든 셀을 명확하게 끄기
  bra.all_off();
  bra.refresh();
  delayMicroseconds(200);  // 상태 초기화 안정화
  
  if (result.count == 0) { 
    bra.refresh(); 
    return; 
  }
  
  uint8_t cellsToUse = (result.count < 3) ? result.count : 3;
  for (uint8_t i = 0; i < cellsToUse; i++) {
    outputBraillePatternToHardware(result.patterns[i], i);
  }
  bra.refresh();  // 모든 패턴 설정 후 한 번에 반영
}

void test_all_dots_sequential() {
  // Serial.println("테스트: 1~6번 점 순차 점등");
  bra.all_off();
  for (uint8_t dot = 0; dot < 6; dot++) {
    bra.all_off();
    bra.on(0, dot);
    bra.refresh();
    // Serial.print("점 ");
    // Serial.print(dot + 1);
    // Serial.println("번 켜짐");
    delay(500);
  }
  bra.all_off();
  bra.refresh();
  // Serial.println("테스트 완료");
}

void test_all_cells_all_dots() {
  bra.all_off();
  for (uint8_t cell = 0; cell < 3; cell++) {
    for (uint8_t dot = 0; dot < 6; dot++) bra.on(cell, dot);
  }
  bra.refresh();
}

void test_each_cell_individual() {
  // Serial.println("=== 각 셀별 개별 테스트 시작 ===");
  
  for (uint8_t cell = 0; cell < 3; cell++) {
    // Serial.print("\n--- 셀 ");
    // Serial.print(cell);
    // Serial.println(" 테스트 ---");
    
    bra.all_off();
    bra.refresh();
    delay(1000);
    
    for (uint8_t dot = 0; dot < 6; dot++) {
      bra.all_off();
      bra.on(cell, dot);
      bra.refresh();
      
      // Serial.print("셀");
      // Serial.print(cell);
      // Serial.print(" - 점");
      // Serial.print(dot);
      // Serial.println("번 켜짐");
      delay(800);
    }
    
    bra.all_off();
    for (uint8_t dot = 0; dot < 6; dot++) {
      bra.on(cell, dot);
    }
    bra.refresh();
    // Serial.print("셀");
    // Serial.print(cell);
    // Serial.println(" - 모든 점 켜짐");
    delay(1500);
  }
  
  bra.all_off();
  bra.refresh();
  // Serial.println("\n=== 테스트 완료 ===");
}

void test_specific_cell(uint8_t cellNum) {
  if (cellNum >= 3) {
    // Serial.println("잘못된 셀 번호");
    return;
  }
  
  // Serial.print("=== 셀 ");
  // Serial.print(cellNum);
  // Serial.println(" 단독 테스트 ===");
  
  bra.all_off();
  bra.refresh();
  delay(500);
  
  for (uint8_t dot = 0; dot < 6; dot++) {
    bra.all_off();
    bra.on(cellNum, dot);
    bra.refresh();
    
    // Serial.print("점 ");
    // Serial.print(dot);
    // Serial.println("번 켜짐");
    delay(700);
  }
  
  bra.all_off();
  for (uint8_t dot = 0; dot < 6; dot++) {
    bra.on(cellNum, dot);
  }
  bra.refresh();
  // Serial.println("모든 점 켜짐");
  delay(1500);
  
  bra.all_off();
  bra.refresh();
  // Serial.println("테스트 완료");
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
  
  // 일시정지 상태면 진행하지 않음
  if (isPaused) return;
  
  unsigned long currentTime = millis();
  if (lastCharTime == 0 || (currentTime - lastCharTime >= charDisplayDuration)) {
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

// 버튼 입력 확인 (디바운싱 포함)
void checkButtons() {
  static unsigned long lastButtonCheck = 0;
  static bool prevButtonState[4] = {true, true, true, true};
  const unsigned long DEBOUNCE_DELAY = 50;  // 50ms 디바운싱
  
  unsigned long currentTime = millis();
  if (currentTime - lastButtonCheck < DEBOUNCE_DELAY) return;
  lastButtonCheck = currentTime;
  
  // 버튼 상태 읽기 (LOW = 눌림, HIGH = 안 눌림, 내부 풀업 사용)
  int rawA1 = digitalRead(BUTTON_PREV_PIN);
  int rawA2 = digitalRead(BUTTON_NEXT_PIN);
  int rawA3 = digitalRead(BUTTON_PLAY_PIN);
  int rawA4 = digitalRead(BUTTON_SPEED_PIN);
  
  bool buttonStates[4] = {
    rawA1 == LOW,
    rawA2 == LOW,
    rawA3 == LOW,
    rawA4 == LOW
  };
  
  // 첫 번째 버튼(A5)은 사용 안 함 - 디버깅 제거
  
  // 버튼이 눌렸을 때만 처리 (엣지 감지)
  // 첫 번째 버튼 고장 - 버튼 2,3,4를 1,2,3처럼 사용
  // 버튼 2 (A2) → 버튼 1 역할 (이전 문자)
  if (buttonStates[1] && !prevButtonState[1]) {
    handleButtonPrev();
  }
  // 버튼 3 (A3) → 버튼 2 역할 (다음 문자)
  if (buttonStates[2] && !prevButtonState[2]) {
    handleButtonNext();
  }
  // 버튼 4 (A4) → 버튼 3 역할 (재생/일시정지)
  if (buttonStates[3] && !prevButtonState[3]) {
    handleButtonPlay();
  }
  
  // 이전 상태 저장
  for (uint8_t i = 0; i < 4; i++) {
    prevButtonState[i] = buttonStates[i];
  }
}

// 버튼 1: 이전 문자 (A2로 매핑됨)
void handleButtonPrev() {
  // 프론트엔드로 버튼 이벤트 전송
  Serial.println("BTN:1");  // 프론트엔드에서 파싱하기 쉬운 형식
  BTSerial.println("BTN:1");  // 블루투스로도 전송
  
  if (sentenceBuffer[0] == '\0') {
    return;
  }
  
  if (sentenceIndex > 0) {
    sentenceIndex--;
    lastCharTime = 0;  // 즉시 표시
    displayCurrentChar();
  }
}

// 버튼 2: 다음 문자 (A3로 매핑됨)
void handleButtonNext() {
  // 프론트엔드로 버튼 이벤트 전송
  Serial.println("BTN:2");  // 프론트엔드에서 파싱하기 쉬운 형식
  BTSerial.println("BTN:2");  // 블루투스로도 전송
  
  if (sentenceBuffer[0] == '\0') {
    return;
  }
  
  uint8_t bufferLen = strlen(sentenceBuffer);
  uint8_t currentByteIndex = getCurrentCharByteIndex();
  
  // 다음 문자로 이동
  if (currentByteIndex < bufferLen) {
    unsigned char c = (unsigned char)sentenceBuffer[currentByteIndex];
    uint8_t charBytes = 1;
    if ((c & 0x80) == 0x00) charBytes = 1;
    else if ((c & 0xE0) == 0xC0) charBytes = 2;
    else if ((c & 0xF0) == 0xE0) charBytes = 3;
    else if ((c & 0xF8) == 0xF0) charBytes = 4;
    
    if (currentByteIndex + charBytes <= bufferLen) {
      sentenceIndex++;
      lastCharTime = 0;  // 즉시 표시
      displayCurrentChar();
    }
  }
}

// 버튼 3: 재생/일시정지 (A4로 매핑됨)
void handleButtonPlay() {
  isPaused = !isPaused;
  // 프론트엔드로 버튼 이벤트 전송
  if (isPaused) {
    Serial.println("BTN:3:PAUSE");  // 프론트엔드에서 파싱하기 쉬운 형식
    BTSerial.println("BTN:3:PAUSE");
  } else {
    Serial.println("BTN:3:PLAY");
    BTSerial.println("BTN:3:PLAY");
    lastCharTime = 0;  // 재생 시 즉시 표시
  }
}

// 버튼 4: 속도 조절 (A4)
void handleButtonSpeed() {
  speedLevel++;
  if (speedLevel > 3) speedLevel = 1;
  
  // 속도 레벨에 따라 표시 시간 조절
  switch (speedLevel) {
    case 1:  // 느림
      charDisplayDuration = 3000;  // 3초
      Serial.println("[BTN4/A4] SPEED:1 (느림)");
      break;
    case 2:  // 보통
      charDisplayDuration = 2000;  // 2초
      Serial.println("[BTN4/A4] SPEED:2 (보통)");
      break;
    case 3:  // 빠름
      charDisplayDuration = 1000;  // 1초
      Serial.println("[BTN4/A4] SPEED:3 (빠름)");
      break;
  }
}

// 현재 문자의 바이트 인덱스 계산
uint8_t getCurrentCharByteIndex() {
  if (sentenceBuffer[0] == '\0') return 0;
  
  uint8_t bufferLen = strlen(sentenceBuffer);
  uint8_t byteIndex = 0;
  
  for (uint8_t i = 0; i < sentenceIndex && byteIndex < bufferLen; i++) {
    unsigned char c = (unsigned char)sentenceBuffer[byteIndex];
    if ((c & 0x80) == 0x00) byteIndex += 1;
    else if ((c & 0xE0) == 0xC0) byteIndex += 2;
    else if ((c & 0xF0) == 0xE0) byteIndex += 3;
    else if ((c & 0xF8) == 0xF0) byteIndex += 4;
    else byteIndex += 1;
  }
  
  return byteIndex;
}

// 현재 문자 표시
void displayCurrentChar() {
  if (sentenceBuffer[0] == '\0') return;
  
  uint8_t bufferLen = strlen(sentenceBuffer);
  uint8_t byteIndex = getCurrentCharByteIndex();
  
  if (byteIndex >= bufferLen) {
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
  }
}
