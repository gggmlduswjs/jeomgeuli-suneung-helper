#ifndef BRAILLE_CONVERTER_H
#define BRAILLE_CONVERTER_H

#include "BrailleMap.h"
#include <stdint.h>

// 최대 점자 셀 개수
#define MAX_BRAILLE_CELLS 3

// 점자 변환 결과
struct BrailleConversionResult {
  BraillePattern patterns[MAX_BRAILLE_CELLS];
  uint8_t count;  // 변환된 패턴 개수
};

// 텍스트를 점자 패턴으로 변환
// @param text 입력 텍스트 (UTF-8)
// @param result 변환 결과를 저장할 구조체
// @return 변환 성공 여부
bool convertToBraille(const char* text, BrailleConversionResult& result);

#endif // BRAILLE_CONVERTER_H

