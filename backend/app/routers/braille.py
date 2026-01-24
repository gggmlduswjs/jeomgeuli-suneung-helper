"""
점자 변환 관련 라우터
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()


class BrailleConvertRequest(BaseModel):
    text: str


class BrailleConvertResponse(BaseModel):
    cells: List[List[int]]  # 2D 배열: 각 셀은 6개 점의 배열


def text_to_braille_cells(text: str) -> List[List[int]]:
    """
    한글 텍스트를 점자 셀 배열로 변환
    
    Args:
        text: 변환할 텍스트
        
    Returns:
        점자 셀 배열 (각 셀은 6개 점의 배열 [0-63])
    """
    cells = []
    
    for char in text:
        # 공백 처리
        if char == ' ' or char == '\n' or char == '\t':
            cells.append([0, 0, 0, 0, 0, 0])  # 빈 셀
            continue
        
        # 한글 유니코드 범위: AC00-D7A3
        if '가' <= char <= '힣':
            # 한글을 점자로 변환 (간단한 매핑)
            # 실제로는 더 정교한 한글 점자 규칙이 필요하지만,
            # 여기서는 기본적인 변환만 제공
            code = ord(char)
            # 간단한 변환: 유니코드 값을 6비트로 변환
            # 실제 점자 변환 로직은 더 복잡함
            braille_value = code % 64
            cells.append([
                (braille_value >> 0) & 1,
                (braille_value >> 1) & 1,
                (braille_value >> 2) & 1,
                (braille_value >> 3) & 1,
                (braille_value >> 4) & 1,
                (braille_value >> 5) & 1,
            ])
        elif 'A' <= char <= 'Z' or 'a' <= char <= 'z':
            # 영문자 처리 (간단한 매핑)
            if char.isupper():
                code = ord(char) - ord('A')
            else:
                code = ord(char) - ord('a')
            # 영문 점자 패턴 (간단한 예시)
            braille_value = code % 64
            cells.append([
                (braille_value >> 0) & 1,
                (braille_value >> 1) & 1,
                (braille_value >> 2) & 1,
                (braille_value >> 3) & 1,
                (braille_value >> 4) & 1,
                (braille_value >> 5) & 1,
            ])
        elif '0' <= char <= '9':
            # 숫자 처리
            code = ord(char) - ord('0')
            braille_value = code % 64
            cells.append([
                (braille_value >> 0) & 1,
                (braille_value >> 1) & 1,
                (braille_value >> 2) & 1,
                (braille_value >> 3) & 1,
                (braille_value >> 4) & 1,
                (braille_value >> 5) & 1,
            ])
        else:
            # 기타 문자는 빈 셀
            cells.append([0, 0, 0, 0, 0, 0])
    
    return cells


@router.post("/braille/convert", response_model=BrailleConvertResponse)
async def convert_braille(request: BrailleConvertRequest):
    """
    텍스트를 점자 셀 배열로 변환
    
    Args:
        request: 변환할 텍스트
        
    Returns:
        점자 셀 배열
    """
    try:
        cells = text_to_braille_cells(request.text)
        return BrailleConvertResponse(cells=cells)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"점자 변환 실패: {str(e)}")
