#ifndef BRAILLE_CONVERTER_H
#define BRAILLE_CONVERTER_H

#include "BrailleMap.h"
#include <stdint.h>

#define MAX_BRAILLE_CELLS 3

struct BrailleConversionResult {
  BraillePattern patterns[MAX_BRAILLE_CELLS];
  uint8_t count;
};

bool convertToBraille(const char* text, BrailleConversionResult& result);

#endif