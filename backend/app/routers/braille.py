"""
점자 변환 관련 라우터
- 표준 한글 점자(한글점자규정): 초·중·종성, 약자, 문장 부호 사용
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.services.korean_braille import text_to_braille_cells

router = APIRouter()


class BrailleConvertRequest(BaseModel):
    text: str


class BrailleConvertResponse(BaseModel):
    cells: List[List[int]]  # 2D 배열: 각 셀은 6개 점 [점1..점6]


@router.post("/braille/convert", response_model=BrailleConvertResponse)
async def convert_braille(request: BrailleConvertRequest):
    """
    텍스트를 표준 한글 점자 셀 배열로 변환.
    한글점자규정(초·중·종성, 약자, 문장 부호) 적용.
    """
    try:
        cells = text_to_braille_cells(request.text)
        return BrailleConvertResponse(cells=cells)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"점자 변환 실패: {str(e)}")
