"""
파싱 관련 유틸리티 함수
"""
import re
from typing import List, Dict, Any


def group_texts_by_line(
    texts: List[str],
    tops: List[int],
    lefts: List[int],
    widths: List[int],
    heights: List[int],
    y_threshold: int = 10
) -> List[List[Dict[str, Any]]]:
    """
    y좌표 기준으로 같은 줄의 단어들을 그룹화
    
    Args:
        texts: 단어 텍스트 리스트
        tops: y좌표 리스트
        lefts: x좌표 리스트
        widths: 너비 리스트
        heights: 높이 리스트
        y_threshold: 같은 줄 판단 임계값
        
    Returns:
        줄별 단어 리스트 (각 줄은 단어 딕셔너리 리스트)
    """
    if not texts or not tops:
        return []
    
    # 단어 정보 수집
    words = []
    for i in range(len(texts)):
        text = texts[i].strip() if i < len(texts) else ""
        if not text:
            continue
        
        word = {
            'text': text,
            'top': tops[i] if i < len(tops) else 0,
            'left': lefts[i] if i < len(lefts) else 0,
            'width': widths[i] if i < len(widths) else 0,
            'height': heights[i] if i < len(heights) else 0,
            'index': i
        }
        words.append(word)
    
    if not words:
        return []
    
    # y좌표 기준으로 정렬
    words.sort(key=lambda w: (w['top'], w['left']))
    
    # 같은 줄로 그룹화
    lines = []
    current_line = [words[0]]
    current_y = words[0]['top']
    
    for word in words[1:]:
        # 같은 줄인지 확인 (y좌표 차이가 threshold 이하)
        if abs(word['top'] - current_y) <= y_threshold:
            current_line.append(word)
        else:
            # 새 줄 시작
            if current_line:
                # x좌표 기준으로 정렬 (왼쪽부터)
                current_line.sort(key=lambda w: w['left'])
                lines.append(current_line)
            current_line = [word]
            current_y = word['top']
    
    # 마지막 줄 추가
    if current_line:
        current_line.sort(key=lambda w: w['left'])
        lines.append(current_line)
    
    return lines


def matches_patterns(text: str, patterns: List[str]) -> bool:
    """
    텍스트가 패턴 중 하나와 매칭되는지 확인
    
    Args:
        text: 검사할 텍스트
        patterns: 정규식 패턴 리스트
        
    Returns:
        매칭 여부
    """
    if not text or len(text.strip()) < 2:
        return False
    
    # 텍스트 정규화 (공백 정리)
    normalized_text = re.sub(r'\s+', ' ', text.strip())
    
    for pattern in patterns:
        try:
            # 정확한 매칭 시도
            if re.match(pattern, text) or re.match(pattern, normalized_text):
                return True
            # 부분 매칭도 시도 (패턴이 텍스트 시작 부분과 일치하는지)
            if re.search(pattern, text) or re.search(pattern, normalized_text):
                # 패턴이 텍스트의 앞부분과 일치하는지 확인
                match = re.search(pattern, text) or re.search(pattern, normalized_text)
                if match and match.start() == 0:
                    return True
        except re.error:
            # 잘못된 정규식 패턴은 스킵
            continue
    return False
