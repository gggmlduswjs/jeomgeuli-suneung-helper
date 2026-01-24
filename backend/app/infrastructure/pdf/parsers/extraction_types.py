"""
Extraction Type Definitions

Type definitions specific to section extraction operations.
These complement the general types in app.infrastructure.pdf.types.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from app.infrastructure.pdf.types import SectionData, JSONDict


@dataclass
class SectionExtractionResult:
    """섹션 추출 결과

    Attributes:
        sections: 추출된 섹션 리스트
        confidence: 추출 신뢰도 (0.0-1.0)
        method: 사용된 추출 방법 ('pattern', 'ai', 'heuristic', 'combined')
        metadata: 추가 메타데이터
    """
    sections: List[SectionData]
    confidence: float
    method: str
    metadata: JSONDict = field(default_factory=dict)


@dataclass
class RegionClassification:
    """Y좌표 기반 영역 분류 결과

    Attributes:
        unit_type: 분류된 단위 타입 ('concept', 'passage', 'problem')
        confidence: 분류 신뢰도 (0.0-1.0)
        y_ratio: 페이지 내 Y좌표 비율 (0.0-1.0)
        lecture_info: 강의 정보 (선택적)
        from_region_hint: region_hint를 사용한 분류 여부
    """
    unit_type: str
    confidence: float
    y_ratio: float
    lecture_info: Optional[JSONDict] = None
    from_region_hint: bool = False


@dataclass
class TextMatchResult:
    """텍스트 매칭 결과

    Attributes:
        matched: 매칭 성공 여부
        match_type: 매칭된 단위 타입
        score: 매칭 점수 (0.0-1.0)
        method: 매칭 방법 ('exact', 'keyword', 'partial', 'prefix')
    """
    matched: bool
    match_type: Optional[str] = None
    score: float = 0.0
    method: Optional[str] = None
