#include "braille.h"

const uint8_t DOT_MAP[7] = {0, 2, 4, 6, 3, 5, 7};

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
  
  // 초기 상태를 명확하게 설정
  digitalWrite(latchPin, LOW);
  digitalWrite(clockPin, LOW);
  digitalWrite(dataPin, LOW);
  delay(10);  // 핀 설정 후 안정화 시간
  
  // 모든 셀을 명확하게 끄기
  all_off();
  refresh();
  delay(20);  // 초기화 후 안정화 시간
}

void braille::all_off() {
  for (int i = 0; i < no_module; i++) {
    cellBuffer[i] = 0;
  }
}

void braille::refresh() {
  digitalWrite(latchPin, LOW);
  
  for (int i = no_module - 1; i >= 0; i--) {
    shiftOut(dataPin, clockPin, MSBFIRST, cellBuffer[i]);
  }
  
  // Latch 신호를 명확하게 전달하기 위해 충분한 시간 확보
  digitalWrite(latchPin, HIGH);
  delayMicroseconds(50);  // 10us -> 50us로 증가 (안정성 향상)
  digitalWrite(latchPin, LOW);
  delayMicroseconds(10);  // 추가 안정화 시간
}

void braille::on(int module, int dot) {
  if (module >= 0 && module < no_module && dot >= 0 && dot < 6) {
    uint8_t dotNumber = 6 - dot;
    
    if (dotNumber >= 1 && dotNumber <= 6) {
      uint8_t hardwareBit = DOT_MAP[dotNumber];
      cellBuffer[module] |= (1 << hardwareBit);
    }
  }
}

void braille::off(int module, int dot) {
  if (module >= 0 && module < no_module && dot >= 0 && dot < 6) {
    uint8_t dotNumber = 6 - dot;
    
    if (dotNumber >= 1 && dotNumber <= 6) {
      uint8_t hardwareBit = DOT_MAP[dotNumber];
      cellBuffer[module] &= ~(1 << hardwareBit);
    }
  }
}