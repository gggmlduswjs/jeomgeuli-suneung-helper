"""
PDF Processing Type Definitions

Common type definitions for OCR data, parsing results, and other
data structures used throughout the PDF processing pipeline.
"""
from typing import TypedDict, Optional, List, Tuple, Union, Any


# ============================================================================
# OCR Data Types
# ============================================================================

class OCRPageData(TypedDict, total=False):
    """
    OCR 결과 페이지 데이터 구조

    pdfplumber, Tesseract OCR, PyMuPDF 등 모든 추출기가
    이 형식으로 데이터를 반환합니다.
    """
    page_num: int                    # 페이지 번호 (1부터 시작)
    text: List[str]                  # 텍스트 리스트 (단어 단위)
    left: List[int]                  # X 좌표 리스트
    top: List[int]                   # Y 좌표 리스트
    width: List[int]                 # 너비 리스트
    height: List[int]                # 높이 리스트
    color: List[Optional[Tuple[int, int, int]]]  # RGB 색상 리스트 (optional)
    conf: List[float]                # 신뢰도 리스트 (OCR에서만, optional)


# ============================================================================
# Bounding Box Types
# ============================================================================

# Bounding box: [x0, y0, x1, y1] 형식
BoundingBox = Tuple[int, int, int, int]


# ============================================================================
# Section/Block Types
# ============================================================================

class SectionData(TypedDict, total=False):
    """섹션 데이터 구조 (개념, 본문 등)"""
    title: str                       # 섹션 제목
    type: str                        # 섹션 타입 (concept, content, passage, problem 등)
    page: int                        # 시작 페이지 번호
    bbox: Optional[BoundingBox]      # 바운딩 박스
    text: Optional[str]              # 섹션 본문 (있는 경우)
    paragraphs: Optional[List['ParagraphData']]  # 문단 리스트


class ParagraphData(TypedDict, total=False):
    """문단 데이터 구조"""
    text: str                        # 문단 텍스트
    page: int                        # 페이지 번호
    y_start: Optional[int]           # Y 좌표 시작
    y_end: Optional[int]             # Y 좌표 끝
    bbox: Optional[BoundingBox]      # 바운딩 박스


class BlockData(TypedDict, total=False):
    """블록 데이터 구조 (ML 분류용)"""
    text: str                        # 블록 텍스트
    type: str                        # 블록 타입 (title, content, image 등)
    page: int                        # 페이지 번호
    bbox: Optional[BoundingBox]      # 바운딩 박스
    confidence: Optional[float]      # 분류 신뢰도


# ============================================================================
# Lecture/Content Types
# ============================================================================

class LectureInfo(TypedDict, total=False):
    """강의 정보 구조"""
    lecture_id: int                  # 강의 번호
    title: str                       # 강의 제목
    page: int                        # 시작 페이지
    start_page: Optional[int]        # 시작 페이지 (명시적)
    end_page: Optional[int]          # 종료 페이지
    source: Optional[str]            # 출처 (toc, content, template_toc 등)


class ProblemInfo(TypedDict, total=False):
    """문제 정보 구조"""
    problem_id: str                  # 문제 번호
    page: int                        # 페이지 번호
    text: Optional[str]              # 문제 텍스트
    bbox: Optional[BoundingBox]      # 바운딩 박스


# ============================================================================
# Parsing Result Types
# ============================================================================

class ParsingMetadata(TypedDict, total=False):
    """파싱 메타데이터"""
    total_lectures: int              # 총 강의 수
    total_problems: int              # 총 문제 수
    status: str                      # 상태 (implemented, error 등)
    template_used: Optional[str]     # 사용된 템플릿 이름
    error: Optional[str]             # 에러 메시지 (있는 경우)
    parsing_method: Optional[str]    # 파싱 방법 (template, ai, fallback 등)


class ParsingResult(TypedDict, total=False):
    """파싱 결과 구조"""
    lectures: List[LectureInfo]      # 강의 리스트
    problems: List[ProblemInfo]      # 문제 리스트
    sections: List[SectionData]      # 섹션 리스트 (optional)
    metadata: ParsingMetadata        # 메타데이터


# ============================================================================
# Template Types
# ============================================================================

class TemplatePatterns(TypedDict, total=False):
    """템플릿 패턴 구조"""
    lecture_title_patterns: List[str]
    toc_lecture_patterns: List[str]
    concept_title_patterns: List[str]
    content_header_patterns: List[str]
    section_title_patterns: List[str]
    problem_number_pattern: str


class TemplateConfig(TypedDict, total=False):
    """템플릿 설정 구조"""
    toc_end_page: int
    start_content_page: int
    paragraph_y_threshold: int
    unit_order: List[str]
    region_hints: dict[str, BoundingBox]
    region_text_examples: dict[str, List[str]]
    toc_text: Optional[str]
    toc_lecture_list: Optional[List[LectureInfo]]
    lecture_page_ranges: Optional[dict[int, dict[str, Optional[int]]]]


# ============================================================================
# Error Detail Types
# ============================================================================

# Error details can contain various types of information
ErrorDetails = dict[str, Union[str, int, float, bool, None, List[Any], dict[str, Any]]]


# ============================================================================
# Generic JSON Types (for external APIs, config files, etc.)
# ============================================================================

# JSON value types
JSONValue = Union[str, int, float, bool, None, List['JSONValue'], dict[str, 'JSONValue']]
JSONDict = dict[str, JSONValue]
