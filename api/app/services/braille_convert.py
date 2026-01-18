"""
점자 변환 서비스
기존 backend/utils/braille_converter.py 로직을 FastAPI로 이전
"""
import json
import os
import unicodedata
from pathlib import Path
from typing import List
from app.core.config import settings

# 전역 점자 매핑 캐시
_BRAILLE_MAP = None
_BRAILLE_MAP_MTIME = None  # 파일 수정 시간 캐시

# 점자 데이터 파일 경로 (기존 backend/data 또는 새 위치)
BRAILLE_DATA_PATH = settings.BASE_DIR / "backend" / "data" / "ko_braille.json"
if not BRAILLE_DATA_PATH.exists():
    # 대체 경로 시도
    BRAILLE_DATA_PATH = settings.DATA_DIR / "ko_braille.json"


def _load_braille_map() -> dict:
    """점자 매핑 테이블을 안전하게 로드 (캐시 사용, 파일 수정 시간 체크)"""
    global _BRAILLE_MAP, _BRAILLE_MAP_MTIME
    
    try:
        current_mtime = os.path.getmtime(BRAILLE_DATA_PATH) if BRAILLE_DATA_PATH.exists() else None
        
        # 캐시가 있고 파일이 수정되지 않았으면 캐시 반환
        if _BRAILLE_MAP is not None and _BRAILLE_MAP_MTIME == current_mtime:
            return _BRAILLE_MAP
        
        # 파일 로드
        if BRAILLE_DATA_PATH.exists():
            with open(BRAILLE_DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                _BRAILLE_MAP = data
                _BRAILLE_MAP_MTIME = current_mtime
                return data
        else:
            print(f"[braille_convert] Warning: ko_braille.json not found at {BRAILLE_DATA_PATH}")
            _BRAILLE_MAP = {}
            _BRAILLE_MAP_MTIME = None
            return {}
    except Exception as e:
        print(f"[braille_convert] Error loading braille map: {e}")
        _BRAILLE_MAP = {}
        _BRAILLE_MAP_MTIME = None
        return {}


def dots_to_bit_array(dots: List[int]) -> List[int]:
    """점 번호 리스트를 비트 배열로 변환"""
    bit_array = [0] * 6
    for dot in dots:
        if 1 <= dot <= 6:
            bit_array[dot - 1] = 1
    return bit_array


def normalize_braille_entry(entry, braille_map: dict = None) -> List[int]:
    """JSON 엔트리를 정규화"""
    if not isinstance(entry, list):
        return [0] * 6
    
    if len(entry) == 0:
        return [0] * 6
    
    # 2차원 배열 형식
    if len(entry) > 0 and isinstance(entry[0], list):
        return normalize_braille_entry(entry[0], braille_map)
    
    # 문자열 참조 형식
    if all(isinstance(x, str) for x in entry):
        if braille_map:
            result = []
            for ref in entry:
                ref_entry = None
                for section in ["vowel", "special", "initial", "final"]:
                    if section in braille_map and ref in braille_map[section]:
                        ref_entry = braille_map[section][ref]
                        break
                if ref_entry:
                    normalized = normalize_braille_entry(ref_entry, braille_map)
                    result.append(normalized)
                else:
                    result.append([0] * 6)
            return result[0] if result else [0] * 6
        return [0] * 6
    
    # 비트 배열 형식
    if len(entry) == 6 and all(x in [0, 1] for x in entry):
        return [int(x) for x in entry]
    
    # 점 번호 리스트 형식
    if all(isinstance(x, int) and 1 <= x <= 6 for x in entry):
        return dots_to_bit_array(entry)
    
    return [0] * 6


def _find_abbreviation(text: str, start_pos: int, braille_map: dict) -> tuple:
    """약자 찾기"""
    if "abbreviation" not in braille_map:
        return (0, None)
    
    abbreviations = braille_map["abbreviation"]
    sorted_abbrs = sorted(abbreviations.items(), key=lambda x: len(x[0]), reverse=True)
    
    for abbr_text, abbr_pattern in sorted_abbrs:
        abbr_len = len(abbr_text)
        if start_pos + abbr_len <= len(text):
            if text[start_pos:start_pos + abbr_len] == abbr_text:
                patterns = []
                if isinstance(abbr_pattern, list) and len(abbr_pattern) > 0:
                    if isinstance(abbr_pattern[0], list):
                        for sub_pattern in abbr_pattern:
                            normalized = normalize_braille_entry(sub_pattern, braille_map)
                            if any(normalized):
                                patterns.append(normalized)
                    else:
                        normalized = normalize_braille_entry(abbr_pattern, braille_map)
                        if any(normalized):
                            patterns.append(normalized)
                
                if patterns:
                    return (abbr_len, patterns)
    
    return (0, None)


def text_to_braille(text: str) -> str:
    """
    한글 텍스트 → 점자 텍스트 변환 (가상 출력용)
    
    Args:
        text: 변환할 텍스트
    
    Returns:
        점자 텍스트 (유니코드 점자 문자)
    """
    cells = text_to_cells(text)
    # 점자 셀을 유니코드 점자 문자로 변환
    # 점자 유니코드 범위: U+2800 ~ U+28FF
    braille_text = ""
    for cell in cells:
        pattern = 0
        for i, bit in enumerate(cell):
            if bit:
                pattern |= (1 << i)
        braille_char = chr(0x2800 + pattern)
        braille_text += braille_char
    
    return braille_text


def text_to_cells(text: str) -> List[List[int]]:
    """
    텍스트를 점자 셀로 변환
    
    Args:
        text: 변환할 텍스트
    
    Returns:
        점자 셀 리스트 [[0|1 x 6], ...]
    """
    try:
        normalized_text = unicodedata.normalize("NFC", text or "")
        braille_map = _load_braille_map()
        
        if not braille_map:
            return []
        
        res = []
        i = 0
        while i < len(normalized_text):
            # 약자 우선 매칭
            matched_len, abbr_patterns = _find_abbreviation(normalized_text, i, braille_map)
            if matched_len > 0 and abbr_patterns:
                res.extend(abbr_patterns)
                i += matched_len
                continue
            
            # 일반 문자 처리 (간소화된 버전)
            ch = normalized_text[i]
            
            # 완전한 글자로 매핑 시도
            arr = braille_map.get(ch)
            if isinstance(arr, list) and len(arr) == 6:
                normalized = normalize_braille_entry(arr, braille_map)
                if any(normalized):
                    res.append(normalized)
                i += 1
                continue
            
            # 한글 분해 처리
            if '가' <= ch <= '힣':
                base = ord(ch) - ord('가')
                initial = base // (21 * 28)
                medial = (base % (21 * 28)) // 28
                final = base % 28
                
                consonants = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
                vowels = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
                
                # 초성 처리
                if initial < len(consonants):
                    initial_char = consonants[initial]
                    if "initial" in braille_map and initial_char in braille_map["initial"]:
                        entry = braille_map["initial"][initial_char]
                        normalized = normalize_braille_entry(entry, braille_map)
                        if any(normalized):
                            res.append(normalized)
                
                # 중성 처리
                if medial < len(vowels):
                    medial_char = vowels[medial]
                    if "vowel" in braille_map and medial_char in braille_map["vowel"]:
                        entry = braille_map["vowel"][medial_char]
                        normalized = normalize_braille_entry(entry, braille_map)
                        if any(normalized):
                            res.append(normalized)
                
                # 종성 처리
                if final > 0 and final < len(consonants):
                    final_char = consonants[final]
                    if "final" in braille_map and final_char in braille_map["final"]:
                        entry = braille_map["final"][final_char]
                        normalized = normalize_braille_entry(entry, braille_map)
                        if any(normalized):
                            res.append(normalized)
            
            i += 1
        
        return res
    except Exception as e:
        print(f"[braille_convert] Error in text_to_cells: {e}")
        return []
