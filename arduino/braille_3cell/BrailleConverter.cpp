#include "BrailleConverter.h"
#include "BrailleMap.h"
#include <Arduino.h>
#include <string.h>
#include <avr/pgmspace.h>

// 약자 텍스트 배열 (PROGMEM에 저장하여 RAM 절약)
// 각 약자는 UTF-8로 3바이트 (한글 1글자), "것"만 6바이트 (2글자)
// PSTR() 매크로를 사용하여 PROGMEM에 저장
const char abbr_0[] PROGMEM = "가";
const char abbr_1[] PROGMEM = "나";
const char abbr_2[] PROGMEM = "다";
const char abbr_3[] PROGMEM = "마";
const char abbr_4[] PROGMEM = "바";
const char abbr_5[] PROGMEM = "사";
const char abbr_6[] PROGMEM = "자";
const char abbr_7[] PROGMEM = "카";
const char abbr_8[] PROGMEM = "타";
const char abbr_9[] PROGMEM = "파";
const char abbr_10[] PROGMEM = "하";
const char abbr_11[] PROGMEM = "것";
const char abbr_12[] PROGMEM = "억";
const char abbr_13[] PROGMEM = "언";
const char abbr_14[] PROGMEM = "얼";
const char abbr_15[] PROGMEM = "연";
const char abbr_16[] PROGMEM = "열";
const char abbr_17[] PROGMEM = "영";
const char abbr_18[] PROGMEM = "옥";
const char abbr_19[] PROGMEM = "온";
const char abbr_20[] PROGMEM = "옹";
const char abbr_21[] PROGMEM = "운";
const char abbr_22[] PROGMEM = "울";
const char abbr_23[] PROGMEM = "은";
const char abbr_24[] PROGMEM = "을";
const char abbr_25[] PROGMEM = "인";

// PROGMEM 포인터 배열
const char* const ABBREVIATION_TEXTS[] PROGMEM = {
  abbr_0, abbr_1, abbr_2, abbr_3, abbr_4, abbr_5, abbr_6, abbr_7, abbr_8, abbr_9, abbr_10,
  abbr_11, abbr_12, abbr_13, abbr_14, abbr_15, abbr_16, abbr_17, abbr_18, abbr_19, abbr_20,
  abbr_21, abbr_22, abbr_23, abbr_24, abbr_25
};

/**
 * 약자 텍스트를 인덱스로 변환 (문장 내에서 가장 긴 약자 찾기)
 */
uint8_t findAbbreviationIndex(const char* text) {
  if (!text) return 255;
  
  uint8_t bestIndex = 255;
  uint8_t bestLength = 0;
  
  for (uint8_t i = 0; i < ABBREVIATION_COUNT; i++) {
    uint8_t abbrLength = 0;
    bool match = false;
    
    // PROGMEM에서 약자 텍스트 읽기
    const char* abbrPtr = (const char*)pgm_read_word(&ABBREVIATION_TEXTS[i]);
    char abbrText[7];
    strcpy_P(abbrText, abbrPtr);
    abbrLength = strlen(abbrText);
    
    // 텍스트 비교
    if (strlen(text) >= abbrLength) {
      if (strncmp(text, abbrText, abbrLength) == 0) {
        match = true;
      }
    }
    
    // 가장 긴 약자 선택 (우선순위)
    if (match && abbrLength > bestLength) {
      bestIndex = i;
      bestLength = abbrLength;
    }
  }
  
  return bestIndex;
}

/**
 * UTF-8 문자를 유니코드로 변환
 */
uint16_t utf8ToUnicode(const char* utf8, uint8_t& byteCount) {
  byteCount = 0;
  if (!utf8 || utf8[0] == 0) return 0;
  
  unsigned char c0 = (unsigned char)utf8[0];
  if ((c0 & 0x80) == 0x00) {
    // 1바이트 ASCII
    byteCount = 1;
    return (uint16_t)c0;
  } else if ((c0 & 0xE0) == 0xC0) {
    // 2바이트
    byteCount = 2;
    if (utf8[1] == 0) return 0;
    return (uint16_t)(((c0 & 0x1F) << 6) | ((unsigned char)utf8[1] & 0x3F));
  } else if ((c0 & 0xF0) == 0xE0) {
    // 3바이트 (한글)
    byteCount = 3;
    if (utf8[1] == 0 || utf8[2] == 0) return 0;
    uint16_t unicode = (uint16_t)(((c0 & 0x0F) << 12) | (((unsigned char)utf8[1] & 0x3F) << 6) | ((unsigned char)utf8[2] & 0x3F));
    return unicode;
  } else if ((c0 & 0xF8) == 0xF0) {
    // 4바이트
    byteCount = 4;
    return 0; // 지원 안 함
  }
  return 0;
}

/**
 * 한글 유니코드를 초성/중성/종성으로 분리
 */
void splitHangul(uint16_t unicode, int8_t& cho, int8_t& jung, int8_t& jong) {
  cho = -1; jung = -1; jong = -1;
  
  if (unicode >= 0xAC00 && unicode <= 0xD7A3) {
    // 완성형 한글 (가~힣)
    uint16_t code = unicode - 0xAC00;
    jong = code % 28;        // 종성 (0: 없음, 1: ㄱ, ..., 27: ㅎ)
    jung = (code / 28) % 21; // 중성 (0: ㅏ, ..., 20: ㅣ)
    cho = (code / 28) / 21;  // 초성 (0: ㄱ, ..., 18: ㅎ)
  }
}

/**
 * 텍스트를 점자 패턴으로 변환 (문장 처리용)
 * 한 글자씩 순차적으로 처리: 문장의 첫 글자만 변환하여 3셀에 표시
 */
bool convertToBraille(const char* text, BrailleConversionResult& result) {
  result.count = 0;
  
  if (!text || strlen(text) == 0) {
    return false;
  }
  
  // 문장의 첫 글자만 처리 (한 글자씩 순차 출력)
  const char* ptr = text;
  uint8_t byteCount = 0;
  uint16_t unicode = utf8ToUnicode(ptr, byteCount);
  
  // 디버깅 출력 (최소화)
  // Serial.print("[convertToBraille] 입력: '");
  // Serial.print(text);
  // Serial.print("', 길이: ");
  // Serial.print(strlen(text));
  // Serial.print(", UTF-8 바이트: ");
  // if (strlen(text) >= 3) {
  //   Serial.print("0x");
  //   Serial.print((unsigned char)text[0], HEX);
  //   Serial.print(" 0x");
  //   Serial.print((unsigned char)text[1], HEX);
  //   Serial.print(" 0x");
  //   Serial.print((unsigned char)text[2], HEX);
  // }
  // Serial.print(", 유니코드: 0x");
  // if (unicode < 0x10) Serial.print("0");
  // if (unicode < 0x100) Serial.print("0");
  // if (unicode < 0x1000) Serial.print("0");
  // Serial.print(unicode, HEX);
  // Serial.print(", byteCount: ");
  // Serial.println(byteCount);
  
  if (byteCount == 0 || unicode == 0) {
    // Serial.println("[convertToBraille] UTF-8 디코딩 실패");
    return false;
  }
  
  // 1. 약자 우선 매칭 (첫 글자가 약자인지 확인)
  if (strlen(ptr) >= 3) {
    uint8_t abbrIndex = findAbbreviationIndex(ptr);
    if (abbrIndex != 255) {
      // 약자 매칭 성공
      Abbreviation abbr = getAbbreviation(abbrIndex);
      if (result.count < MAX_BRAILLE_CELLS) {
        result.patterns[result.count++] = abbr.pattern1;
      }
      if (abbr.cellCount == 2 && result.count < MAX_BRAILLE_CELLS) {
        result.patterns[result.count++] = abbr.pattern2;
      }
      return result.count > 0;
    }
  }
  
  // 2. 완성형 한글 처리 (가~힣) - 초성/중성/종성으로 분리하여 3셀에 표시
  if (unicode >= 0xAC00 && unicode <= 0xD7A3) {
    int8_t cho, jung, jong;
    splitHangul(unicode, cho, jung, jong);
    
    // Serial.print("[convertToBraille] 한글 분리: 초성=");
    // Serial.print(cho);
    // Serial.print(", 중성=");
    // Serial.print(jung);
    // Serial.print(", 종성=");
    // Serial.println(jong);
    
    // 초성 출력 (셀 0) - ㅇ은 표기 안 함
    if (cho != -1 && cho != 11 && result.count < MAX_BRAILLE_CELLS) {
      result.patterns[result.count++] = getInitialConsonant(cho);
    }
    
    // 중성 출력 (셀 1)
    if (jung != -1 && result.count < MAX_BRAILLE_CELLS) {
      result.patterns[result.count++] = getVowel(jung);
      
      // 복합 모음 두 번째 셀 처리 (셀 2)
      if (jung == 3 || jung == 9 || jung == 10 || jung == 14 || jung == 15 || jung == 16) {
        if (result.count < MAX_BRAILLE_CELLS) {
          BraillePattern second;
          memcpy_P(&second, &COMPOUND_VOWEL_SECOND, sizeof(BraillePattern));
          result.patterns[result.count++] = second;
        }
      }
    }
    
    // 종성 출력 (셀 2 또는 3) - 없음은 표기 안 함
    // 복합 모음이 있으면 종성은 다음 셀로 밀림 (하지만 3셀 제한)
    if (jong != -1 && jong != 0 && result.count < MAX_BRAILLE_CELLS) {
      BraillePattern finalPattern = getFinalConsonant(jong);
      if (finalPattern.count > 0) {
        result.patterns[result.count++] = finalPattern;
      }
    }
    return result.count > 0;
  } else {
    // Serial.print("[convertToBraille] 한글 범위 밖: 0x");
    // Serial.println(unicode, HEX);
  }
  
  // 3. 숫자 처리
  if (unicode >= '0' && unicode <= '9') {
    BraillePattern numberSign;
    memcpy_P(&numberSign, &NUMBER_SIGN, sizeof(BraillePattern));
    if (result.count < MAX_BRAILLE_CELLS) {
      result.patterns[result.count++] = numberSign;
    }
    if (result.count < MAX_BRAILLE_CELLS) {
      result.patterns[result.count++] = getNumber(unicode - '0');
    }
    return result.count > 0;
  }
  
  // 4. 영문자 처리
  if ((unicode >= 'A' && unicode <= 'Z') || (unicode >= 'a' && unicode <= 'z')) {
    BraillePattern romanSign;
    memcpy_P(&romanSign, &ROMAN_LETTER_SIGN, sizeof(BraillePattern));
    if (result.count < MAX_BRAILLE_CELLS) {
      result.patterns[result.count++] = romanSign;
    }
    if (result.count < MAX_BRAILLE_CELLS) {
      uint8_t letterIndex = (unicode >= 'a') ? (unicode - 'a') : (unicode - 'A');
      result.patterns[result.count++] = getEnglishLetter(letterIndex);
    }
    return result.count > 0;
  }
  
  // 5. 공백 처리
  if (unicode == ' ') {
    // 공백은 점자 없음 (빈 패턴)
    if (result.count < MAX_BRAILLE_CELLS) {
      result.patterns[result.count++] = EMPTY_PATTERN;
    }
    return result.count > 0;
  }
  
  return false;
}

