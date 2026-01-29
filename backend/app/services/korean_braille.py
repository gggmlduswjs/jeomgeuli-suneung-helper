"""
표준 한글 점자 변환 (한글점자규정 해설서 기준)
- 초성·중성·종성 자모자, 약자(그래서/그러나 등), 문장 부호 지원
- Unicode Braille (U+2800–U+283F) 출력 → cells 변환
"""
from __future__ import annotations

import re
from typing import List, Tuple

try:
    import hgtk
except ImportError:
    hgtk = None  # type: ignore

# 초성 점자 (한·점 제1장 제1항~제3항)
CHO = {
    "ㄱ": "⠈", "ㄴ": "⠉", "ㄷ": "⠊", "ㄹ": "⠐", "ㅁ": "⠑", "ㅂ": "⠘", "ㅅ": "⠠",
    "ㅇ": "", "ㅈ": "⠨", "ㅊ": "⠰", "ㅋ": "⠋", "ㅌ": "⠓", "ㅍ": "⠙", "ㅎ": "⠚",
    "ㄲ": "⠠⠈", "ㄸ": "⠠⠊", "ㅃ": "⠠⠘", "ㅆ": "⠠⠠", "ㅉ": "⠠⠨",
}

# 중성 점자 (한·점 제1장 제7항~제8항)
JUNG = {
    "ㅏ": "⠣", "ㅑ": "⠜", "ㅓ": "⠎", "ㅕ": "⠱", "ㅗ": "⠥", "ㅛ": "⠬", "ㅜ": "⠍",
    "ㅠ": "⠩", "ㅡ": "⠪", "ㅣ": "⠕", "ㅐ": "⠗", "ㅔ": "⠝", "ㅒ": "⠜⠗", "ㅖ": "⠌",
    "ㅘ": "⠧", "ㅙ": "⠧⠗", "ㅚ": "⠽", "ㅝ": "⠏", "ㅞ": "⠏⠗", "ㅟ": "⠍⠗", "ㅢ": "⠺",
}

# 종성 점자 (한·점 제1장 제4항~제6항)
JONG = {
    "ㄱ": "⠁", "ㄴ": "⠒", "ㄷ": "⠔", "ㄹ": "⠂", "ㅁ": "⠢", "ㅂ": "⠃", "ㅅ": "⠄",
    "ㅇ": "⠶", "ㅈ": "⠅", "ㅊ": "⠆", "ㅋ": "⠖", "ㅌ": "⠦", "ㅍ": "⠲", "ㅎ": "⠴",
    "ㄲ": "⠁⠁", "ㄳ": "⠁⠄", "ㄵ": "⠒⠅", "ㄶ": "⠒⠴", "ㄺ": "⠂⠁", "ㄻ": "⠂⠢",
    "ㄼ": "⠂⠃", "ㄽ": "⠂⠄", "ㄾ": "⠂⠦", "ㄿ": "⠂⠲", "ㅀ": "⠂⠴",
    "ㅄ": "⠃⠄", "ㅆ": "⠌", "": "",
}

# 문장 부호 (한·점 제12절)
PUNCT = {
    ".": "⠲", "?": "⠦", "!": "⠖", ",": "⠐", "·": "⠐⠆", ":": "⠐⠂", ";": "⠰⠆",
    "/": "⠸⠌", "-": "⠤", "―": "⠤⠤", "~": "⠤⠤", "'": "⠄", "(": "⠦⠄", ")": "⠠⠴",
    "「": "⠐⠦", "」": "⠴⠂", "『": "⠰⠦", "』": "⠴⠆", " ": "⠀",
}

# 초성+ㅏ 약자 (한·점 제12항) 가, 나, 다, 마, 바, 사, 자, 카, 타, 파, 하
ABBR_CJ = {
    ("ㄱ", "ㅏ"): "⠫", ("ㄴ", "ㅏ"): "⠉", ("ㄷ", "ㅏ"): "⠊", ("ㅁ", "ㅏ"): "⠑",
    ("ㅂ", "ㅏ"): "⠘", ("ㅅ", "ㅏ"): "⠇", ("ㅈ", "ㅏ"): "⠨", ("ㅋ", "ㅏ"): "⠋",
    ("ㅌ", "ㅏ"): "⠓", ("ㅍ", "ㅏ"): "⠙", ("ㅎ", "ㅏ"): "⠚",
}

# 약어 (한·점 제16항)
ABBR_WORD = {
    "그래서": "⠁⠎", "그러나": "⠁⠉", "그러면": "⠁⠒", "그러므로": "⠁⠢",
    "그런데": "⠁⠝", "그리고": "⠁⠥", "그리하여": "⠁⠱",
}

# 영문 6점 점자 (a–z = A–Z, Grade 1)
ENG_BRAILLE = (
    "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚⠅⠇⠍⠝⠕⠏⠟⠗⠎⠞⠥⠧⠺⠭⠽⠵"
)
NUM_BRAILLE = "⠼" + "⠁⠃⠉⠙⠑⠋⠛⠓⠊⠚"  # ⠼ + 1–9,0


def _unicode_braille_to_cells(s: str) -> List[List[int]]:
    """Unicode Braille 문자열 → 6점 셀 배열 (점1~6 순서)."""
    cells: List[List[int]] = []
    for c in s:
        if c in "\n\t":
            continue
        o = ord(c)
        if not (0x2800 <= o <= 0x28FF):
            continue
        v = o - 0x2800
        cells.append([
            (v >> 0) & 1, (v >> 1) & 1, (v >> 2) & 1,
            (v >> 3) & 1, (v >> 4) & 1, (v >> 5) & 1,
        ])
    return cells


def _abbr_spans(text: str) -> List[Tuple[int, int, str]]:
    """비겹치는 약어 구간 (시작, 끝, 점자) 목록. 긴 단어 우선."""
    repls: List[Tuple[int, int, str]] = []
    for word, bra in sorted(ABBR_WORD.items(), key=lambda x: -len(x[0])):
        for m in re.finditer(re.escape(word), text):
            start, end = m.start(), m.end()
            if any(s < end and e > start for s, e, _ in repls):
                continue
            repls.append((start, end, bra))
    repls.sort(key=lambda x: x[0])
    return repls


def _hangul_to_braille(cho: str, jung: str, jong: str, use_abbr_cj: bool) -> str:
    """한글 자모 → 점자 유니코드. use_abbr_cj: 초성+ㅏ 약자 사용 여부."""
    c = CHO.get(cho, "")
    j = JUNG.get(jung, "")
    e = JONG.get(jong, "")
    if use_abbr_cj and (cho, jung) in ABBR_CJ and jong == "":
        return ABBR_CJ[(cho, jung)]
    # ㅇ 단독 초성(받침 없음) → ⠛ (한·점 제9항)
    if cho == "ㅇ" and jung and not jong:
        c = "⠛"
    return (c or "") + (j or "") + (e or "")


def _text_to_braille_unicode(text: str) -> str:
    """텍스트 → Unicode Braille 문자열 (표준 한글 점자)."""
    if not hgtk:
        return _fallback_braille(text)

    n = len(text)
    spans = _abbr_spans(text)
    abbr_at: dict[int, Tuple[int, str]] = {s: (e, b) for s, e, b in spans}

    res: List[str] = []
    i = 0
    while i < n:
        if i in abbr_at:
            end, bra = abbr_at[i]
            res.append(bra)
            i = end
            continue
        ch = text[i]
        if ch in PUNCT:
            res.append(PUNCT[ch])
            i += 1
            continue
        if hgtk.checker.is_hangul(ch):
            cho, jung, jong = hgtk.letter.decompose(ch)
            # 단독 자모: 앞에 온표 ⠿ (한·점 제9항)
            if (not cho and jung) or (cho and not jung):
                res.append("⠿")
            res.append(_hangul_to_braille(cho or "ㅇ", jung or "", jong or "", True))
            i += 1
            continue
        if ch in "\n\t":
            res.append("⠀")
            i += 1
            continue
        if "a" <= ch <= "z" or "A" <= ch <= "Z":
            idx = (ord(ch) & 31) - 1  # a/A=0 .. z/Z=25
            res.append(ENG_BRAILLE[idx])
            i += 1
            continue
        if "0" <= ch <= "9":
            d = ord(ch) - ord("0")
            res.append(NUM_BRAILLE[0])  # ⠼
            res.append(NUM_BRAILLE[1 + ((d - 1) % 10)])  # 1–9, 0
            i += 1
            continue
        res.append("⠀")
        i += 1

    return "".join(res)


def _fallback_braille(text: str) -> str:
    """hgtk 미설치 시 단순 매핑 (공백·기호만)."""
    res = []
    for c in text:
        if c in PUNCT:
            res.append(PUNCT[c])
        elif c in " \n\t":
            res.append("⠀")
        else:
            res.append("⠀")
    return "".join(res)


def text_to_braille_cells(text: str) -> List[List[int]]:
    """
    텍스트를 표준 한글 점자 셀 배열로 변환.
    - 한글점자규정: 초·중·종성, 약자(그래서/그러나 등), 문장 부호 적용.
    - 반환: [[d1..d6], ...] (각 셀 6점, 0/1)
    """
    s = _text_to_braille_unicode(text)
    return _unicode_braille_to_cells(s)
