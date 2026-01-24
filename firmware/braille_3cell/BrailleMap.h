#ifndef BRAILLE_MAP_H
#define BRAILLE_MAP_H

#include <stdint.h>
#include <Arduino.h>
#include <avr/pgmspace.h>

// ============================================================================
// 점자 패턴 구조체
// ============================================================================
struct BraillePattern {
  uint8_t dots[6];  // 점 번호 배열 (1-6, 0은 사용 안 함)
  uint8_t count;    // 점 개수
};

// 빈 패턴
const BraillePattern EMPTY_PATTERN = {{0}, 0};

// ============================================================================
// 유틸리티 함수
// ============================================================================

/**
 * 점 번호 배열을 비트마스크로 변환
 * @param dots 점 번호 배열 (예: {1, 4} -> 0b001001)
 * @return 비트마스크 (0-63)
 */
inline uint8_t dotsToBitmask(const uint8_t dots[], uint8_t count) {
  uint8_t mask = 0;
  for (uint8_t i = 0; i < count; i++) {
    if (dots[i] >= 1 && dots[i] <= 6) {
      mask |= (1 << (dots[i] - 1));
    }
  }
  return mask;
}

/**
 * 비트마스크를 점 번호 배열로 변환
 * @param mask 비트마스크 (0-63)
 * @param dots 출력 배열
 * @return 점 개수
 */
inline uint8_t bitmaskToDots(uint8_t mask, uint8_t dots[]) {
  uint8_t count = 0;
  for (uint8_t i = 0; i < 6; i++) {
    if (mask & (1 << i)) {
      dots[count++] = i + 1;
    }
  }
  return count;
}

// ============================================================================
// 1. 초성 (Initial Consonants) - 규정 제1장 제1절
// ============================================================================
const BraillePattern INITIAL_CONSONANTS[19] PROGMEM = {
  {{4}, 1},                    // ㄱ (0)
  {{6, 4}, 2},                 // ㄲ (1) - 된소리표(6) + ㄱ(4)
  {{1, 4}, 2},                 // ㄴ (2)
  {{2, 4}, 2},                 // ㄷ (3)
  {{6, 2, 4}, 3},              // ㄸ (4) - 된소리표(6) + ㄷ(2,4)
  {{5}, 1},                    // ㄹ (5)
  {{1, 5}, 2},                 // ㅁ (6)
  {{4, 5}, 2},                 // ㅂ (7)
  {{6, 4, 5}, 3},              // ㅃ (8) - 된소리표(6) + ㅂ(4,5)
  {{6}, 1},                    // ㅅ (9)
  {{6, 6}, 2},                 // ㅆ (10) - 된소리표(6) + ㅅ(6)
  {{1, 2, 4, 5}, 4},          // ㅇ (11) - 1, 2, 4, 5번 점
  {{4, 6}, 2},                 // ㅈ (12)
  {{6, 4, 6}, 3},              // ㅉ (13) - 된소리표(6) + ㅈ(4,6)
  {{5, 6}, 2},                 // ㅊ (14)
  {{1, 2, 4}, 3},              // ㅋ (15)
  {{1, 2, 5}, 3},              // ㅌ (16)
  {{1, 4, 5}, 3},              // ㅍ (17)
  {{2, 4, 5}, 3}               // ㅎ (18)
};

inline BraillePattern getInitialConsonant(uint8_t index) {
  if (index >= 19) return EMPTY_PATTERN;
  BraillePattern pattern;
  memcpy_P(&pattern, &INITIAL_CONSONANTS[index], sizeof(BraillePattern));
  return pattern;
}

// ============================================================================
// 2. 종성 (Final Consonants / 받침) - 규정 제1장 제2절
// ============================================================================
const BraillePattern FINAL_CONSONANTS[28] PROGMEM = {
  {{}, 0},                     // 없음 (0)
  {{1}, 1},                    // ㄱ (1)
  {{1, 6}, 2},                 // ㄲ (2) - 쌍받침 약자
  {{1, 3}, 2},                 // ㄳ (3) - 두 셀: ㄱ(1) + ㅅ(3)
  {{2, 4, 5}, 3},              // ㄴ (4)
  {{2, 4, 5, 1, 3}, 5},        // ㄵ (5) - 두 셀: ㄴ(2,4,5) + ㅈ(1,3)
  {{2, 4, 5, 3, 5, 6}, 6},     // ㄶ (6) - 두 셀: ㄴ(2,4,5) + ㅎ(3,5,6)
  {{3, 5}, 2},                 // ㄷ (7)
  {{2}, 1},                    // ㄹ (8)
  {{2, 1}, 2},                 // ㄺ (9) - 두 셀: ㄹ(2) + ㄱ(1)
  {{2, 2, 6}, 3},              // ㄻ (10) - 두 셀: ㄹ(2) + ㅁ(2,6)
  {{2, 1, 2}, 3},              // ㄼ (11) - 두 셀: ㄹ(2) + ㅂ(1,2)
  {{2, 3}, 2},                 // ㄽ (12) - 두 셀: ㄹ(2) + ㅅ(3)
  {{2, 2, 3, 6}, 4},           // ㄾ (13) - 두 셀: ㄹ(2) + ㅌ(2,3,6)
  {{2, 2, 5, 6}, 4},           // ㄿ (14) - 두 셀: ㄹ(2) + ㅍ(2,5,6)
  {{2, 3, 5, 6}, 4},           // ㅀ (15) - 두 셀: ㄹ(2) + ㅎ(3,5,6)
  {{2, 6}, 2},                 // ㅁ (16)
  {{1, 2}, 2},                 // ㅂ (17)
  {{1, 2, 3}, 3},              // ㅄ (18) - 두 셀: ㅂ(1,2) + ㅅ(3)
  {{3}, 1},                    // ㅅ (19)
  {{3, 4}, 2},                 // ㅆ (20) - 쌍받침 약자
  {{2, 3, 5, 6}, 4},           // ㅇ (21) - 주의: 초성과 다름!
  {{1, 3}, 2},                 // ㅈ (22)
  {{1, 2, 6}, 3},              // ㅊ (23)
  {{2, 3, 5}, 3},              // ㅋ (24)
  {{2, 3, 6}, 3},              // ㅌ (25)
  {{2, 5, 6}, 3},              // ㅍ (26)
  {{3, 5, 6}, 3}               // ㅎ (27)
};

inline BraillePattern getFinalConsonant(uint8_t index) {
  if (index >= 28) return EMPTY_PATTERN;
  BraillePattern pattern;
  memcpy_P(&pattern, &FINAL_CONSONANTS[index], sizeof(BraillePattern));
  return pattern;
}

// ============================================================================
// 3. 모음 (Vowels) - 규정 제1장 제3절
// ============================================================================
// 복합 모음 구조체 (두 셀 차지)
struct CompoundVowel {
  BraillePattern first;   // 첫 번째 셀
  BraillePattern second;  // 두 번째 셀
};

const BraillePattern VOWELS[21] PROGMEM = {
  {{1, 2, 6}, 3},              // ㅏ (0)
  {{1, 2, 3, 5}, 4},           // ㅐ (1)
  {{3, 4, 5}, 3},              // ㅑ (2)
  {{3, 4, 5}, 3},              // ㅒ (3) - 첫 번째 셀만 (두 번째는 ㅐ)
  {{2, 3, 4}, 3},              // ㅓ (4)
  {{1, 3, 4, 5}, 4},           // ㅔ (5)
  {{1, 5, 6}, 3},              // ㅕ (6)
  {{3, 4}, 2},                 // ㅖ (7)
  {{1, 3, 6}, 3},              // ㅗ (8)
  {{1, 2, 3, 6}, 4},           // ㅘ (9) - 첫 번째 셀만 (두 번째는 ㅐ)
  {{1, 2, 3, 6}, 4},           // ㅙ (10) - 첫 번째 셀만 (두 번째는 ㅐ)
  {{1, 3, 4, 5, 6}, 5},        // ㅚ (11)
  {{3, 4, 6}, 3},              // ㅛ (12)
  {{1, 3, 4}, 3},              // ㅜ (13)
  {{1, 2, 3, 4}, 4},           // ㅝ (14) - 첫 번째 셀만 (두 번째는 ㅐ)
  {{1, 2, 3, 4}, 4},           // ㅞ (15) - 첫 번째 셀만 (두 번째는 ㅐ)
  {{1, 3, 4}, 3},              // ㅟ (16) - 첫 번째 셀만 (두 번째는 ㅐ)
  {{1, 4, 6}, 3},              // ㅠ (17)
  {{2, 4, 6}, 3},              // ㅡ (18)
  {{2, 4, 5, 6}, 4},           // ㅢ (19)
  {{1, 3, 5}, 3}               // ㅣ (20)
};

// 복합 모음 두 번째 셀 매핑 (ㅐ 패턴)
const BraillePattern COMPOUND_VOWEL_SECOND PROGMEM = {{1, 2, 3, 5}, 4}; // ㅐ

inline BraillePattern getVowel(uint8_t index) {
  if (index >= 21) return EMPTY_PATTERN;
  BraillePattern pattern;
  memcpy_P(&pattern, &VOWELS[index], sizeof(BraillePattern));
  return pattern;
}

// ============================================================================
// 4. 약자 (Abbreviations) - 규정 제2장
// ============================================================================
struct Abbreviation {
  BraillePattern pattern1;     // 첫 번째 셀
  BraillePattern pattern2;     // 두 번째 셀 (없으면 EMPTY_PATTERN)
  uint8_t cellCount;           // 셀 개수 (1 또는 2)
};

// 약자 텍스트는 별도로 처리 (UTF-8 문자열 비교)
const Abbreviation ABBREVIATIONS[] PROGMEM = {
  {{{1, 2, 4, 6}, 4}, EMPTY_PATTERN, 1},  // 가
  {{{1, 4}, 2}, EMPTY_PATTERN, 1},        // 나
  {{{2, 4}, 2}, EMPTY_PATTERN, 1},        // 다
  {{{1, 5}, 2}, EMPTY_PATTERN, 1},        // 마
  {{{4, 5}, 2}, EMPTY_PATTERN, 1},        // 바
  {{{1, 2, 3}, 3}, EMPTY_PATTERN, 1},     // 사
  {{{4, 6}, 2}, EMPTY_PATTERN, 1},        // 자
  {{{1, 2, 4}, 3}, EMPTY_PATTERN, 1},     // 카
  {{{1, 2, 5}, 3}, EMPTY_PATTERN, 1},     // 타
  {{{1, 4, 5}, 3}, EMPTY_PATTERN, 1},     // 파
  {{{2, 4, 5}, 3}, EMPTY_PATTERN, 1},     // 하
  {{{5, 6}, 2}, {{2, 3, 4}, 3}, 2},       // 것 (두 칸)
  {{{1, 4, 5, 6}, 4}, EMPTY_PATTERN, 1},  // 억
  {{{2, 3, 4, 5, 6}, 5}, EMPTY_PATTERN, 1}, // 언
  {{{2, 3, 4, 5}, 4}, EMPTY_PATTERN, 1},   // 얼
  {{{1, 6}, 2}, EMPTY_PATTERN, 1},        // 연
  {{{1, 2, 5, 6}, 4}, EMPTY_PATTERN, 1},   // 열
  {{{1, 2, 4, 5, 6}, 5}, EMPTY_PATTERN, 1}, // 영
  {{{1, 3, 4, 6}, 4}, EMPTY_PATTERN, 1},   // 옥
  {{{1, 2, 3, 5, 6}, 5}, EMPTY_PATTERN, 1}, // 온
  {{{1, 2, 3, 4, 5, 6}, 6}, EMPTY_PATTERN, 1}, // 옹
  {{{1, 2, 4, 5}, 4}, EMPTY_PATTERN, 1},   // 운
  {{{1, 2, 3, 4, 6}, 5}, EMPTY_PATTERN, 1}, // 울
  {{{1, 3, 5, 6}, 4}, EMPTY_PATTERN, 1},   // 은
  {{{2, 3, 4, 6}, 4}, EMPTY_PATTERN, 1},   // 을
  {{{1, 3, 4, 5, 6}, 5}, EMPTY_PATTERN, 1}  // 인
};

const uint8_t ABBREVIATION_COUNT = 26;

// 약자 텍스트 매핑 (인덱스로 접근)
// 인덱스 순서: 가(0), 나(1), 다(2), 마(3), 바(4), 사(5), 자(6), 카(7), 타(8), 파(9), 하(10),
//            것(11), 억(12), 언(13), 얼(14), 연(15), 열(16), 영(17), 옥(18), 온(19), 옹(20),
//            운(21), 울(22), 은(23), 을(24), 인(25)
inline Abbreviation getAbbreviation(uint8_t index) {
  if (index >= ABBREVIATION_COUNT) {
    Abbreviation empty = {EMPTY_PATTERN, EMPTY_PATTERN, 0};
    return empty;
  }
  Abbreviation abbr;
  memcpy_P(&abbr, &ABBREVIATIONS[index], sizeof(Abbreviation));
  return abbr;
}

/**
 * 약자 텍스트를 인덱스로 변환
 * @param text UTF-8 약자 텍스트
 * @return 인덱스 (찾지 못하면 255)
 */
uint8_t findAbbreviationIndex(const char* text);

// ============================================================================
// 5. 숫자 (Numbers) - 규정 제3장
// ============================================================================
const BraillePattern NUMBER_SIGN PROGMEM = {{3, 4, 5, 6}, 4};  // 수표

const BraillePattern NUMBERS[10] PROGMEM = {
  {{2, 4, 5}, 3},              // 0
  {{1}, 1},                    // 1
  {{1, 2}, 2},                 // 2
  {{1, 4}, 2},                 // 3
  {{1, 4, 5}, 3},              // 4
  {{1, 5}, 2},                 // 5
  {{1, 2, 4}, 3},              // 6
  {{1, 2, 4, 5}, 4},           // 7
  {{1, 2, 5}, 3},              // 8
  {{2, 4}, 2}                  // 9
};

inline BraillePattern getNumber(uint8_t digit) {
  if (digit >= 10) return EMPTY_PATTERN;
  BraillePattern pattern;
  memcpy_P(&pattern, &NUMBERS[digit], sizeof(BraillePattern));
  return pattern;
}

// ============================================================================
// 6. 영어 (English) - 규정 제4장
// ============================================================================
const BraillePattern ROMAN_LETTER_SIGN PROGMEM = {{3, 5, 6}, 3};  // 로마자표

const BraillePattern ENGLISH_LETTERS[26] PROGMEM = {
  {{1}, 1},                    // a
  {{1, 2}, 2},                 // b
  {{1, 4}, 2},                 // c
  {{1, 4, 5}, 3},              // d
  {{1, 5}, 2},                 // e
  {{1, 2, 4}, 3},              // f
  {{1, 2, 4, 5}, 4},           // g
  {{1, 2, 5}, 3},              // h
  {{2, 4}, 2},                 // i
  {{2, 4, 5}, 3},              // j
  {{1, 3}, 2},                 // k
  {{1, 2, 3}, 3},              // l
  {{1, 3, 4}, 3},              // m
  {{1, 3, 4, 5}, 4},           // n
  {{1, 3, 5}, 3},              // o
  {{1, 2, 3, 4}, 4},           // p
  {{1, 2, 3, 4, 5}, 5},        // q
  {{1, 2, 3, 5}, 4},           // r
  {{2, 3, 4}, 3},              // s
  {{2, 3, 4, 5}, 4},           // t
  {{1, 3, 4, 6}, 4},          // u
  {{1, 2, 3, 6}, 4},           // v
  {{2, 4, 5, 6}, 4},          // w
  {{1, 3, 4, 5, 6}, 5},        // x
  {{1, 3, 4, 5, 6, 2}, 6},     // y
  {{1, 3, 5, 6}, 4}            // z
};

inline BraillePattern getEnglishLetter(uint8_t index) {
  if (index >= 26) return EMPTY_PATTERN;
  BraillePattern pattern;
  memcpy_P(&pattern, &ENGLISH_LETTERS[index], sizeof(BraillePattern));
  return pattern;
}

// ============================================================================
// 디버깅 함수
// ============================================================================
inline void printPattern(const BraillePattern& pattern) {
  Serial.print("{");
  for (uint8_t i = 0; i < pattern.count; i++) {
    Serial.print(pattern.dots[i]);
    if (i < pattern.count - 1) Serial.print(", ");
  }
  Serial.print("}");
}

#endif // BRAILLE_MAP_H
