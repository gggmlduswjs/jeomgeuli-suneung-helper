#include "braille.h"

// ============================================================================
// 하드웨어 매핑 테이블
// ============================================================================
// 점자 번호 1~6번을 실제 하드웨어 비트(2~7)로 변환
// 규칙: 1번점(비트2), 2번점(비트4), 3번점(비트6), 4번점(비트3), 5번점(비트5), 6번점(비트7)
const uint8_t DOT_MAP[7] = {0, 2, 4, 6, 3, 5, 7}; // 인덱스 0은 사용 안 함, 1~6 사용

braille::braille(int dataPin, int latchPin, int clockPin, int no_module) {
  this->dataPin = dataPin;
  this->latchPin = latchPin;
  this->clockPin = clockPin;
  this->no_module = no_module;
  this->cellBuffer = new byte[no_module];
  for (int i = 0; i < no_module; i++) {
    this->cellBuffer[i] = 0;
  }
}

braille::~braille() {
  delete[] cellBuffer;
}

void braille::begin() {
  pinMode(dataPin, OUTPUT);
  pinMode(latchPin, OUTPUT);
  pinMode(clockPin, OUTPUT);
  
  digitalWrite(latchPin, LOW);
  digitalWrite(clockPin, LOW);
  digitalWrite(dataPin, LOW);
  
  all_off();
  refresh();
}

void braille::all_off() {
  for (int i = 0; i < no_module; i++) {
    cellBuffer[i] = 0;
  }
}

void braille::refresh() {
  digitalWrite(latchPin, LOW);
  
  // 셀3 → 셀2 → 셀1 순서로 전송 (왼쪽 → 중간 → 오른쪽 표시)
  // MSBFIRST 사용 (하드웨어 세팅에 맞춤)
  for (int i = no_module - 1; i >= 0; i--) {
    shiftOut(dataPin, clockPin, MSBFIRST, cellBuffer[i]);
  }
  
  digitalWrite(latchPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(latchPin, LOW);
}

void braille::on(int module, int dot) {
  if (module >= 0 && module < no_module && dot >= 0 && dot < 6) {
    // dot은 0-5 (인덱스)
    // 역순 매핑: dot 0 → Dot 6번, dot 1 → Dot 5번, ..., dot 5 → Dot 1번
    uint8_t dotNumber = 6 - dot; // 6~1 (역순)
    
    // DOT_MAP을 사용하여 실제 하드웨어 비트 위치 찾기
    if (dotNumber >= 1 && dotNumber <= 6) {
      uint8_t hardwareBit = DOT_MAP[dotNumber]; // 2, 4, 6, 3, 5, 7 중 하나
      cellBuffer[module] |= (1 << hardwareBit);
    }
  }
}

void braille::off(int module, int dot) {
  if (module >= 0 && module < no_module && dot >= 0 && dot < 6) {
    // dot은 0-5 (인덱스)
    // 역순 매핑: dot 0 → Dot 6번, dot 1 → Dot 5번, ..., dot 5 → Dot 1번
    uint8_t dotNumber = 6 - dot; // 6~1 (역순)
    
    // DOT_MAP을 사용하여 실제 하드웨어 비트 위치 찾기
    if (dotNumber >= 1 && dotNumber <= 6) {
      uint8_t hardwareBit = DOT_MAP[dotNumber]; // 2, 4, 6, 3, 5, 7 중 하나
      cellBuffer[module] &= ~(1 << hardwareBit);
    }
  }
}

