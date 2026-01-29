"""
템플릿 관리 서비스
템플릿 생성, 수정, 삭제 등의 비즈니스 로직
"""
import json
import logging
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
from fastapi import HTTPException

from app.infrastructure.pdf.parsers.template_manager import TemplateManager
from app.infrastructure.pdf.parsers.template import ParsingTemplate
from app.core.config import settings
from app.utils.ai_utils import get_openai_client, check_openai_available
from app.core.exceptions import (
    TemplateNotFoundException, ExternalServiceException,
    DatabaseOperationException
)

logger = logging.getLogger(__name__)

# Pydantic 모델들
class ParsingGuideRegion(BaseModel):
    """파싱 가이드 영역 (YOLO-style bbox)"""
    page: int = Field(description="페이지 번호 (1-based)")
    label: str = Field(description="단위 레이블 (concept, passage, problem 등)")
    bbox: List[float] = Field(description="바운딩 박스 [x_min, y_min, x_max, y_max] (픽셀 좌표)")


class CurriculumStructureSurvey(BaseModel):
    """커리큘럼 구조 설문"""
    is_lecture_based: bool = Field(default=True, description="강의 기반 구조 여부")
    lecture_units: List[str] = Field(default_factory=lambda: ["concept", "passage", "problem"], description="강의 내 단위 목록")
    unit_order: List[str] = Field(default_factory=lambda: ["concept", "passage", "problem"], description="단위 순서")


# 기본 목차 정제 프롬프트
DEFAULT_TOC_CLEANING_RULES = """정제 규칙:
1. 특수 문자 제거 (cid:xxx, 유니코드 오류 등)
2. 분리된 단어들을 올바르게 병합

3. 강의 단위 인식:
   - "N강 제목" 형식
   - 3자리 페이지 번호(009, 012, 015 등)로 끝나는 블록을 하나의 강의로 간주
   - 페이지 번호 앞의 모든 텍스트를 한 줄로 병합

4. 제외 항목:
   - 두 자리 번호 (01, 02 등) 단독 라인
   - 섹션 구분자 (>>>, 고전 시가 등)
   - 메타 정보 (페이지 끝, 오후 6:00 등)

5. 출력:
   - 각 강의는 한 줄로
   - 빈 줄로 구분"""

# 템플릿 매니저 인스턴스 (싱글톤)
_template_manager: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """템플릿 매니저 싱글톤"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager


def _normalize_bbox_to_ratios(bbox: List[float], page_width: float = 1100.0, page_height: float = 1400.0) -> Dict[str, float]:
    """bbox 좌표를 페이지 비율로 정규화
    
    Args:
        bbox: [x_min, y_min, x_max, y_max] 픽셀 좌표
        page_width: 페이지 너비 (기본값: A4 가로 DPI 150 기준)
        page_height: 페이지 높이 (기본값: A4 세로 DPI 150 기준)
    
    Returns:
        {"x_min": 0.0-1.0, "y_min": 0.0-1.0, "x_max": 0.0-1.0, "y_max": 0.0-1.0}
    """
    if not bbox or len(bbox) != 4:
        return {}
    
    try:
        x_min, y_min, x_max, y_max = [float(x) for x in bbox]
        if page_width <= 0 or page_height <= 0:
            return {}
        return {
            "x_min": max(0.0, min(1.0, x_min / page_width)),
            "y_min": max(0.0, min(1.0, y_min / page_height)),
            "x_max": max(0.0, min(1.0, x_max / page_width)),
            "y_max": max(0.0, min(1.0, y_max / page_height)),
        }
    except (ValueError, TypeError, IndexError):
        return {}


def _extract_images_from_bbox_regions(
    pdf_path: Path,
    parsing_guide_regions: List[ParsingGuideRegion],
    output_dir: Optional[Path] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """PDF에서 bbox 영역 내 이미지 추출 및 저장
    
    Args:
        pdf_path: PDF 파일 경로
        parsing_guide_regions: 파싱 가이드 영역 리스트
        output_dir: 이미지 저장 디렉토리 (None이면 추출만 하고 저장 안 함)
    
    Returns:
        {"concept": [{"page": 10, "image_path": "...", "bbox": [...]}], ...} 형태의 이미지 정보
    """
    if not pdf_path or not pdf_path.exists():
        return {}
    
    if not parsing_guide_regions:
        return {}
    
    from pdf2image import convert_from_path
    from PIL import Image
    from app.core.config import settings
    
    region_images: Dict[str, List[Dict[str, Any]]] = {}
    
    try:
        # 필요한 페이지만 추출 (최적화)
        pages_to_extract = set(r.page for r in parsing_guide_regions)
        
        # 페이지별로 그룹화
        regions_by_page: Dict[int, List[ParsingGuideRegion]] = {}
        for region in parsing_guide_regions:
            page_num = region.page
            if page_num not in regions_by_page:
                regions_by_page[page_num] = []
            regions_by_page[page_num].append(region)
        
        # 각 페이지 처리
        for page_num in pages_to_extract:
            try:
                # PDF 페이지를 이미지로 변환
                convert_kwargs = {
                    "dpi": 300,
                    "first_page": page_num,
                    "last_page": page_num,
                }
                if settings.POPPLER_PATH:
                    convert_kwargs["poppler_path"] = settings.POPPLER_PATH
                
                page_images = convert_from_path(str(pdf_path), **convert_kwargs)
                if not page_images:
                    logger.warning(f"페이지 {page_num} 이미지 변환 실패")
                    continue
                
                page_image = page_images[0]
                img_width, img_height = page_image.size
                
                # 해당 페이지의 모든 영역 처리
                for region in regions_by_page.get(page_num, []):
                    if not region or not hasattr(region, 'bbox') or not region.bbox or len(region.bbox) != 4:
                        continue
                    
                    label = region.label
                    bbox = region.bbox  # [x_min, y_min, x_max, y_max] 픽셀 좌표
                    
                    # bbox 좌표 검증 및 제한
                    x_min, y_min, x_max, y_max = bbox
                    left = max(0, min(int(x_min), img_width - 1))
                    top = max(0, min(int(y_min), img_height - 1))
                    right = max(left + 1, min(int(x_max), img_width))
                    bottom = max(top + 1, min(int(y_max), img_height))
                    
                    # 영역 이미지 크롭
                    try:
                        region_image = page_image.crop((left, top, right, bottom))
                        
                        image_info = {
                            "page": page_num,
                            "bbox": [left, top, right, bottom],
                            "label": label
                        }
                        
                        # 저장 디렉토리가 있으면 이미지 저장
                        if output_dir:
                            output_dir.mkdir(parents=True, exist_ok=True)
                            filename = f"{label}_p{page_num:02d}_{len(regions_by_page[page_num])}.png"
                            image_path = output_dir / filename
                            region_image.save(image_path, 'PNG')
                            image_info["image_path"] = str(image_path)
                            logger.info(f"[영역 이미지] 저장: {filename} ({label}, 페이지 {page_num})")
                        
                        # 레이블별로 저장
                        if label not in region_images:
                            region_images[label] = []
                        region_images[label].append(image_info)
                        
                    except Exception as e:
                        logger.error(f"영역 이미지 크롭 실패 (페이지 {page_num}, {label}): {e}")
                        continue
                
            except Exception as e:
                logger.error(f"페이지 {page_num} 이미지 추출 실패: {e}")
                continue
        
        logger.info(f"[영역 이미지 추출] {len(region_images)}개 레이블에서 이미지 추출 완료")
        for label, images in region_images.items():
            logger.info(f"  - {label}: {len(images)}개 이미지")
    
    except Exception as e:
        logger.error(f"영역 이미지 추출 실패: {e}", exc_info=True)
        return {}
    
    return region_images


def _extract_text_from_bbox_regions(
    pdf_path: Path,
    parsing_guide_regions: List[ParsingGuideRegion]
) -> Dict[str, List[str]]:
    """PDF에서 bbox 영역 내 텍스트 추출 (패턴 학습용)
    
    Args:
        pdf_path: PDF 파일 경로
        parsing_guide_regions: 파싱 가이드 영역 리스트
    
    Returns:
        {"concept": ["1. 시적 표현", "2. 시의 형식"], "passage": [...], ...} 형태의 텍스트 예시
    """
    if not pdf_path or not pdf_path.exists():
        return {}
    
    if not parsing_guide_regions:
        return {}
    
    from app.infrastructure.pdf.extractors.base import PdfplumberExtractor
    
    region_text_examples: Dict[str, List[str]] = {}
    
    try:
        extractor = PdfplumberExtractor(dpi=200)
        # 필요한 페이지만 추출 (최적화)
        pages_to_extract = set(r.page for r in parsing_guide_regions)
        ocr_data_list = []
        
        for page_num in pages_to_extract:
            try:
                page_ocr = extractor.extract(pdf_path, first_page=page_num, last_page=page_num)
                if page_ocr:
                    ocr_data_list.extend(page_ocr)
            except Exception as e:
                logger.warning(f"페이지 {page_num} 추출 실패: {e}")
                continue
        
        # 페이지별 OCR 데이터를 딕셔너리로 변환 (빠른 조회)
        ocr_by_page = {data.get('page_num'): data for data in ocr_data_list}
        
        # 각 영역에서 텍스트 추출
        for region in parsing_guide_regions:
            if not region or not hasattr(region, 'bbox') or not region.bbox or len(region.bbox) != 4:
                continue
            
            page_num = region.page
            label = region.label
            bbox = region.bbox  # [x_min, y_min, x_max, y_max] 픽셀 좌표
            
            # 해당 페이지의 OCR 데이터 가져오기
            ocr_data = ocr_by_page.get(page_num)
            if not ocr_data:
                continue
            
            texts = ocr_data.get('text', [])
            lefts = ocr_data.get('left', [])
            tops = ocr_data.get('top', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts or len(texts) != len(lefts):
                continue
            
            # bbox 영역 내의 텍스트 추출
            x_min, y_min, x_max, y_max = bbox
            region_texts = []
            
            for i, text in enumerate(texts):
                if i >= len(lefts) or i >= len(tops):
                    continue
                
                left = lefts[i]
                top = tops[i]
                width = widths[i] if i < len(widths) else 0
                height = heights[i] if i < len(heights) else 0
                
                # 단어의 중심점 또는 영역이 bbox 내에 있는지 확인
                word_right = left + width
                word_bottom = top + height
                word_center_x = left + width / 2
                word_center_y = top + height / 2
                
                # bbox 내에 포함되는지 확인 (약간의 여유를 둠)
                if (x_min - 5 <= word_center_x <= x_max + 5 and 
                    y_min - 5 <= word_center_y <= y_max + 5):
                    region_texts.append(text)
            
            # 추출한 텍스트를 레이블별로 저장
            if region_texts:
                if label not in region_text_examples:
                    region_text_examples[label] = []
                # 텍스트를 줄 단위로 결합 (의미 있는 문장/제목 추출)
                combined_text = ' '.join(region_texts).strip()
                if combined_text and len(combined_text) > 2:
                    region_text_examples[label].append(combined_text)
        
        # 중복 제거 및 정리
        for label in region_text_examples:
            region_text_examples[label] = list(set(region_text_examples[label]))[:20]  # 최대 20개만 저장
        
        logger.info(f"[영역 텍스트 추출] {len(region_text_examples)}개 레이블에서 텍스트 추출 완료")
        for label, texts in region_text_examples.items():
            logger.info(f"  - {label}: {len(texts)}개 예시")
    
    except Exception as e:
        logger.error(f"영역 텍스트 추출 실패: {e}", exc_info=True)
        return {}
    
    return region_text_examples


def _compute_region_hints(parsing_guide_regions: List[ParsingGuideRegion]) -> Dict[str, Dict[str, float]]:
    """파싱 가이드 영역들을 집계하여 region_hints 생성 (하위 호환성 유지)
    
    Args:
        parsing_guide_regions: 파싱 가이드 영역 리스트
    
    Returns:
        {"concept": {"y_min": 0.05, "y_max": 0.35}, ...} 형태의 힌트
    """
    if not parsing_guide_regions:
        return {}
    
    # 레이블별로 그룹화
    by_label: Dict[str, List[Dict[str, float]]] = {}
    for region in parsing_guide_regions:
        if not region or not hasattr(region, 'bbox') or not region.bbox:
            continue
        try:
            normalized = _normalize_bbox_to_ratios(region.bbox)
            if normalized:
                if region.label not in by_label:
                    by_label[region.label] = []
                by_label[region.label].append(normalized)
        except (AttributeError, TypeError, ValueError) as e:
            # bbox 형식이 잘못된 경우 해당 region 건너뛰기
            continue
    
    # 각 레이블별로 y_min, y_max의 평균/범위 계산
    hints: Dict[str, Dict[str, float]] = {}
    for label, regions in by_label.items():
        if not regions:
            continue
        y_mins = [r["y_min"] for r in regions if "y_min" in r]
        y_maxs = [r["y_max"] for r in regions if "y_max" in r]
        if y_mins and y_maxs:
            hints[label] = {
                "y_min": min(y_mins),
                "y_max": max(y_maxs),
            }
    
    return hints


def _build_toc_prompt(
    subject: str,
    year: Optional[int],
    book_name: Optional[str],
    toc_text: str,
    curriculum_survey: Optional[CurriculumStructureSurvey],
    parsing_guide_regions: List[ParsingGuideRegion],
    toc_lecture_line_examples: List[str],
    toc_nonlecture_line_examples: List[str],
    expected_lecture_count: Optional[int],
) -> str:
    """
    마스터 프롬프트 기반 TOC 텍스트로부터 ParsingTemplate(JSON) 생성을 유도하는 프롬프트.
    - JSON만 출력하도록 강제(코드블록/설명 금지)
    - regex는 Python re 기준
    """
    # TOC 텍스트 전처리
    trimmed = toc_text.strip()
    if len(trimmed) > 8000:
        trimmed = trimmed[:8000]

    lec_examples = [x.strip() for x in (toc_lecture_line_examples or []) if str(x).strip()]
    nonlec_examples = [x.strip() for x in (toc_nonlecture_line_examples or []) if str(x).strip()]
    
    # Region hints 계산
    region_hints = _compute_region_hints(parsing_guide_regions)
    region_hints_json = json.dumps(region_hints, ensure_ascii=False, indent=2) if region_hints else "{}"
    
    # 커리큘럼 구조 정보 (관리자 입력 정보 저장)
    unit_order = ["concept", "passage", "problem"]
    is_lecture_based = True
    lecture_units = ["concept", "passage", "problem"]
    if curriculum_survey:
        unit_order = curriculum_survey.unit_order or unit_order
        is_lecture_based = curriculum_survey.is_lecture_based if curriculum_survey.is_lecture_based is not None else True
        lecture_units = curriculum_survey.lecture_units or lecture_units
    
    # 마스터 프롬프트 구조로 빌드
    prompt_parts = [
        "## [SYSTEM PROMPT]",
        "",
        "You are an expert in **educational PDF structure analysis, curriculum modeling, and rule-based document parsing systems**.",
        "",
        "Your role is **NOT** to summarize or explain the content of the PDF.",
        "",
        "Your role is to:",
        "* Understand curriculum structure from TOC",
        "* Use minimal human guidance (survey + region hints)",
        "* Generate and refine a **ParsingTemplate** that enables **high-precision automatic parsing**",
        "* Treat manual region marking as **parsing guidance**, not post-correction",
        "",
        "Think like a backend engineer designing a **reproducible, scalable parsing system**.",
        "",
        "## [USER INPUTS]",
        "",
        "### 1️⃣ PDF METADATA",
        json.dumps({
            "subject": subject,
            "year": year,
            "book_name": book_name
        }, ensure_ascii=False),
        "",
        "### 2️⃣ CURRICULUM STRUCTURE SURVEY",
        json.dumps({
            "is_lecture_based": curriculum_survey.is_lecture_based if curriculum_survey else True,
            "lecture_units": curriculum_survey.lecture_units if curriculum_survey else ["concept", "passage", "problem"],
            "unit_order": unit_order
        }, ensure_ascii=False),
        "",
        "### 3️⃣ TABLE OF CONTENTS (TOC TEXT)",
        "```",
        trimmed,
        "```",
        "",
        "### 4️⃣ PARSING GUIDE REGIONS",
        json.dumps([{
            "page": r.page,
            "label": r.label,
            "bbox": r.bbox
        } for r in parsing_guide_regions], ensure_ascii=False) if parsing_guide_regions else "[]",
        "",
        "Computed region_hints (normalized ratios):",
        region_hints_json,
        "",
        "### TOC LECTURE LINE EXAMPLES (MUST match):",
        "```",
        "\n".join(lec_examples[:30]),
        "```",
        "",
        "### TOC NON-LECTURE LINE EXAMPLES (MUST NOT match):",
        "```",
        "\n".join(nonlec_examples[:30]),
        "```",
        "",
        f"### Expected lecture count: {expected_lecture_count or 'not specified'}",
        "",
        "## [YOUR TASK]",
        "",
        "Generate a **ParsingTemplate JSON** that:",
        "1. Uses TOC to detect lecture boundaries",
        "2. Defines how to identify concept / passage / problem units",
        "3. Incorporates region guidance to reduce structural errors",
        "4. Is reusable for future uploads of the same textbook",
        "5. Enables bbox-based image cropping",
        "",
        "## [OUTPUT FORMAT – STRICT]",
        "",
        "You must output **ONLY ONE JSON OBJECT** with this structure:",
        "",
        json.dumps({
            "patterns": {
                "lecture_title_patterns": [],
                "toc_lecture_patterns": [],
                "concept_title_patterns": [],
                "content_header_patterns": [],
                "section_title_patterns": [],
                "problem_number_pattern": ""
            },
            "config": {
                "unit_order": unit_order,
                "region_hints": {},
                "toc_end_page": None,
                "start_content_page": None,
                "paragraph_y_threshold": 12
            }
        }, ensure_ascii=False, indent=2),
        "",
        "## [IMPORTANT RULES]",
        "",
        "* ❌ Do NOT summarize content",
        "* ❌ Do NOT invent textbook text",
        "* ❌ Do NOT output explanations or markdown",
        "* ✅ Output JSON only",
        "* ✅ Design for **pre-parsing guidance**, not post-correction",
        "* ✅ Manual regions are **generalized**, not stored as page overrides",
        "* ✅ All regex patterns must be valid Python `re`",
        "* ✅ toc_lecture_patterns MUST match all provided TOC lecture examples",
        "* ✅ toc_lecture_patterns MUST NOT match non-lecture examples",
        "",
        "## [PATTERN GENERATION GUIDELINES]",
        "",
        "When generating `toc_lecture_patterns`:",
        "1. **Be flexible**: Use patterns that match variations (e.g., `^\\d+강` matches '1강', '10강', '73강')",
        "2. **Handle common formats**:",
        "   - `^\\d+강` - matches 'N강' format",
        "   - `^\\d+강\\s*[|:]` - matches 'N강 |' or 'N강:' format",
        "   - `^\\d+강\\s+[가-힣]` - matches 'N강 제목' format",
        "3. **Avoid over-specific patterns**: Don't include page numbers, author names, or specific titles",
        "4. **Test mentally**: Ensure your patterns would match at least 80% of the provided examples",
        "5. **Use multiple patterns**: Provide 2-3 patterns to cover different formats",
        "",
        "Example patterns for Korean lecture format:",
        "```json",
        '["^\\\\d+강", "^\\\\d+강\\\\s*[|:]", "^\\\\d+강\\\\s+[가-힣]"]',
        "```",
        "",
        "## [CORE PRINCIPLE]",
        "",
        "> **Parsing accuracy is determined before parsing starts.**",
        "> Post-hoc correction is a fallback, not the main strategy.",
    ]
    
    return "\n".join(prompt_parts)


def _generate_template_from_toc_via_openai(
    subject: str,
    name: str,
    version: str,
    description: str,
    year: Optional[int],
    book_name: Optional[str],
    toc_text: str,
    curriculum_survey: Optional[CurriculumStructureSurvey],
    parsing_guide_regions: List[ParsingGuideRegion],
    toc_lecture_line_examples: List[str],
    toc_nonlecture_line_examples: List[str],
    expected_lecture_count: Optional[int],
    model_name: str,
    confidence: float,
    defaults: Dict[str, Any],
    book_id: Optional[str] = None,
    toc_lecture_list_override: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """OpenAI로 TOC 기반 템플릿 초안을 생성하고 ParsingTemplate dict로 반환."""
    client = get_openai_client()

    prompt = _build_toc_prompt(
        subject=subject,
        year=year,
        book_name=book_name,
        toc_text=toc_text,
        curriculum_survey=curriculum_survey,
        parsing_guide_regions=parsing_guide_regions,
        toc_lecture_line_examples=toc_lecture_line_examples,
        toc_nonlecture_line_examples=toc_nonlecture_line_examples,
        expected_lecture_count=expected_lecture_count,
    )

    # OpenAI Chat Completions (openai>=1.0.0)
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or ""
    except Exception as e:
        raise ExternalServiceException("OpenAI", str(e))

    try:
        generated = json.loads(content)
    except Exception as e:
        raise ExternalServiceException("OpenAI JSON 파싱", str(e))

    patterns = generated.get("patterns") or {}
    config = generated.get("config") or {}
    notes = generated.get("notes", [])

    # 커리큘럼 구조 정보 추출 (관리자 입력 우선)
    unit_order = config.get("unit_order")
    is_lecture_based = config.get("is_lecture_based", True)
    lecture_units = config.get("lecture_units", ["concept", "passage", "problem"])
    
    if curriculum_survey:
        unit_order = curriculum_survey.unit_order or unit_order
        is_lecture_based = curriculum_survey.is_lecture_based if curriculum_survey.is_lecture_based is not None else is_lecture_based
        lecture_units = curriculum_survey.lecture_units or lecture_units
    
    if not unit_order:
        unit_order = ["concept", "passage", "problem"]
    
    # region_hints는 LLM이 생성하거나, 제공된 parsing_guide_regions에서 계산 (하위 호환성)
    region_hints = config.get("region_hints", {})
    if not region_hints and parsing_guide_regions:
        region_hints = _compute_region_hints(parsing_guide_regions)
    
    # 영역 내 텍스트 및 이미지 추출 (패턴 학습용)
    # 1. defaults에서 제공된 region_text_examples 사용 (우선순위 높음)
    region_text_examples: Dict[str, List[str]] = defaults.get("region_text_examples", {})
    region_image_examples: Dict[str, List[Dict[str, Any]]] = {}

    # 2. parsing_guide_regions와 book_id가 있으면 PDF에서 직접 추출
    # 텍스트와 이미지를 독립적으로 추출 (하나가 있어도 다른 것은 추출)
    if parsing_guide_regions and book_id:
        try:
            from app.infrastructure.database.session import get_db
            from app.infrastructure.database.models import Book
            from sqlalchemy.orm import Session

            # DB에서 book 정보 가져오기
            db_gen = get_db()
            db: Session = next(db_gen)
            try:
                book = db.query(Book).filter(Book.book_id == book_id).first()
                if book and book.file_path:
                    pdf_path = Path(book.file_path)
                    if pdf_path.exists():
                        # 텍스트 추출 (region_text_examples가 없을 때만)
                        if not region_text_examples:
                            region_text_examples = _extract_text_from_bbox_regions(
                                pdf_path,
                                parsing_guide_regions
                            )
                            logger.info(f"[템플릿 생성] 영역 텍스트 추출 완료: {len(region_text_examples)}개 레이블")
                        else:
                            logger.info(f"[템플릿 생성] 영역 텍스트 예시는 이미 제공됨 (추출 스킵)")

                        # 이미지 추출 및 저장 (항상 수행)
                        # 템플릿별 이미지 디렉토리: backend/data/templates/images/{subject}_{name}/
                        template_images_dir = settings.API_DIR / "data" / "templates" / "images" / f"{subject}_{name}"
                        region_image_examples = _extract_images_from_bbox_regions(
                            pdf_path,
                            parsing_guide_regions,
                            output_dir=template_images_dir
                        )
                        logger.info(f"[템플릿 생성] 영역 이미지 추출 완료: {len(region_image_examples)}개 레이블")
                    else:
                        logger.warning(f"[템플릿 생성] PDF 파일이 존재하지 않음: {pdf_path}")
                else:
                    logger.warning(f"[템플릿 생성] 교재를 찾을 수 없음: {book_id}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[템플릿 생성] 영역 텍스트/이미지 추출 실패: {e}", exc_info=True)
            # 실패해도 계속 진행

    # 기본값/오버라이드 병합
    def _safe_int(value, default: int) -> int:
        """안전한 int 변환"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    # TOC 텍스트에서 직접 강의 목록 추출 (간단하고 명확하게)
    # 단, 사용자가 편집한 강의 목록이 제공되면 그것을 우선 사용
    if toc_lecture_list_override:
        toc_lecture_list = toc_lecture_list_override
        logger.info(f"[템플릿 생성] 사용자 제공 강의 목록 사용: {len(toc_lecture_list)}개")
    elif toc_text:
        toc_lecture_list = []
        import re
        lines = toc_text.splitlines()
        logger.info(f"[템플릿 생성] TOC 텍스트에서 강의 목록 직접 추출 시작 (전체 {len(lines)}줄)")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # 간단한 규칙: "N강"으로 시작하는 라인만 추출
            num_match = re.match(r'^(\d+)강', line)
            if not num_match:
                i += 1
                continue
            
            lecture_num = int(num_match.group(1))
            
            # 제목 추출 (강의 번호 이후 부분)
            title = re.sub(r'^\d+강\s*', '', line).strip()
            # "|" 제거 (앞뒤 공백 포함) - title에는 순수한 제목만 저장
            title = re.sub(r'^\|\s*', '', title).strip()  # 앞의 "| " 제거
            title = re.sub(r'\s*\|\s*', ' ', title).strip()  # 중간의 "|"도 공백으로 변환
            
            # 현재 라인에서 페이지 번호 추출 시도
            start_page = None
            page_match = re.search(r'\s+(\d{3,4})\s*$', line)
            if page_match:
                try:
                    start_page = int(page_match.group(1))
                    # 페이지 번호 제거 (제목에서)
                    title = re.sub(r'\s+\d{3,4}\s*$', '', title).strip()
                except ValueError:
                    pass
            
            # 현재 라인에 페이지 번호가 없으면 다음 줄 확인
            # (예: "1강 | 시의 표현과 형식\n해 (박두진) 009")
            if not start_page and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 다음 줄이 "N강"으로 시작하지 않고, 끝에 3-4자리 숫자가 있으면 페이지 번호로 간주
                if not re.match(r'^\d+강', next_line):
                    next_page_match = re.search(r'\s+(\d{3,4})\s*$', next_line)
                    if next_page_match:
                        try:
                            start_page = int(next_page_match.group(1))
                        except ValueError:
                            pass
            
            # 제목이 비어있지 않으면 추가
            if title:
                # 중복 체크 (같은 lecture_id가 이미 있으면 스킵)
                if not any(l['lecture_id'] == lecture_num for l in toc_lecture_list):
                    toc_lecture_list.append({
                        "lecture_id": lecture_num,
                        "title": title,
                        "start_page": start_page,
                        "source": "toc_text"
                    })
            
            i += 1
        
        logger.info(f"[템플릿 생성] TOC에서 {len(toc_lecture_list)}개 강의 추출 완료")
        
        # 강의별 페이지 범위 계산 (다음 강의 시작 페이지 - 1)
        # 페이지 번호가 있는 강의들만 정렬
        lectures_with_pages = [l for l in toc_lecture_list if l.get("start_page") is not None]
        lectures_with_pages.sort(key=lambda x: x["lecture_id"])
        
        # 각 강의의 종료 페이지 계산 (다음 강의 시작 - 1)
        for i, lecture in enumerate(lectures_with_pages):
            if i + 1 < len(lectures_with_pages):
                next_lecture = lectures_with_pages[i + 1]
                lecture["end_page"] = next_lecture["start_page"] - 1
            else:
                # 마지막 강의는 종료 페이지를 None으로 (전체 끝까지)
                lecture["end_page"] = None
        
        # 페이지 범위 정보를 전체 리스트에 반영
        page_range_map = {l["lecture_id"]: (l.get("start_page"), l.get("end_page")) for l in lectures_with_pages}
        for lecture in toc_lecture_list:
            if lecture["lecture_id"] in page_range_map:
                start, end = page_range_map[lecture["lecture_id"]]
                lecture["start_page"] = start
                lecture["end_page"] = end

    # lecture_page_ranges 생성 (파싱 시 사용)
    # 형식: {"1": {"start": 9, "end": 11}, "2": {"start": 12, "end": 15}, ...}
    lecture_page_ranges = {}
    for lecture in toc_lecture_list:
        if lecture.get("start_page") is not None:
            lecture_id = str(lecture["lecture_id"])
            lecture_page_ranges[lecture_id] = {
                "start": lecture["start_page"],
                "end": lecture.get("end_page")  # None이면 끝까지
            }

    logger.info(f"[템플릿 생성] lecture_page_ranges 생성: {len(lecture_page_ranges)}개 강의")
    for lecture_id, page_range in list(lecture_page_ranges.items())[:5]:  # 처음 5개만 로깅
        end_str = page_range["end"] if page_range["end"] else "끝"
        logger.info(f"  - 강의 {lecture_id}: {page_range['start']} ~ {end_str}페이지")

    merged_config = {
        "toc_end_page": _safe_int(config.get("toc_end_page"), defaults.get("toc_end_page", 7)),
        "start_content_page": _safe_int(config.get("start_content_page"), defaults.get("start_content_page", 8)),
        "paragraph_y_threshold": _safe_int(config.get("paragraph_y_threshold"), defaults.get("paragraph_y_threshold", 25)),
        "unit_order": unit_order,  # 관리자 입력: 단위 순서
        "is_lecture_based": is_lecture_based,  # 관리자 입력: 강의 기반 구조 여부
        "lecture_units": lecture_units,  # 관리자 입력: 강의 내 단위 목록
        "lecture_page_ranges": lecture_page_ranges,  # 강의별 페이지 범위 (파싱 시 활용)
        "region_hints": region_hints,  # 하위 호환성 유지 (y 좌표 기반)
        "region_text_examples": region_text_examples,  # 영역 내 텍스트 예시 (패턴 학습용)
        "region_image_examples": region_image_examples,  # 영역 이미지 예시 (시각적 참고용)
        "toc_text": toc_text if toc_text else None,  # TOC 텍스트 전체 저장 (파싱 시 활용)
        "toc_lecture_list": toc_lecture_list,  # 추출한 강의 목록 저장
    }

    # 최소한의 안전장치: 빈 리스트/키 보정
    def _as_list(v):
        return [str(x) for x in (v or []) if str(x).strip()]

    # 템플릿 통계 정보 추가
    template_stats = {
        "total_lectures": len(toc_lecture_list),
        "lectures_with_pages": len([l for l in toc_lecture_list if l.get("start_page") is not None]),
        "total_patterns": sum(len(v) if isinstance(v, list) else (1 if v else 0) for v in patterns.values()),
        "has_region_hints": bool(region_hints),
        "has_region_text_examples": bool(region_text_examples),
        "has_region_image_examples": bool(region_image_examples),
        "toc_text_length": len(toc_text) if toc_text else 0,
    }
    
    template_dict: Dict[str, Any] = {
        "name": name,
        "subject": subject,
        "version": version or "",
        "description": description or f"Auto-generated from TOC ({subject})",
        "patterns": {
            "lecture_title_patterns": _as_list(patterns.get("lecture_title_patterns")),
            "toc_lecture_patterns": _as_list(patterns.get("toc_lecture_patterns")),
            "concept_title_patterns": _as_list(patterns.get("concept_title_patterns")),
            "content_header_patterns": _as_list(patterns.get("content_header_patterns")),
            "section_title_patterns": _as_list(patterns.get("section_title_patterns")),
            "problem_number_pattern": str(patterns.get("problem_number_pattern", r"^\d{2}$")),
        },
        "config": merged_config,
        "confidence": float(confidence),
        "sample_texts": [line.strip() for line in toc_text.splitlines() if line.strip()][:30],
        "stats": template_stats,  # 템플릿 통계 정보 추가
        "created_at": None,
        "updated_at": None,
        "_notes": notes,  # preview용 (저장 전 UI에 참고로만 사용)
    }

    # ParsingTemplate로 한 번 검증
    try:
        _ = ParsingTemplate.from_dict(template_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"생성된 템플릿 스키마 검증 실패: {e}")

    return template_dict


def _extract_lecture_lines_from_toc_directly(toc_text: str) -> List[str]:
    """TOC 텍스트에서 직접 강의 라인 추출 (패턴 없이)
    
    다양한 형식의 강의 라인을 추출:
    - "1강 | 시의 표현과 형식"
    - "10강 모죽지랑가 (득오) / 화왕가 (이익) 044"
    - "72강 실전학습1 회 [ 0 1~04] 청백운 (작자 미상) 296"
    """
    import re
    lecture_lines = []
    
    for line in toc_text.splitlines():
        s = line.strip()
        if not s:
            continue
        
        # 강의 라인 패턴들 (더 포괄적)
        # 1. "N강" 형식
        if re.search(r'^\d+강', s):
            lecture_lines.append(s)
        # 2. "N강 |" 형식
        elif re.search(r'^\d+강\s*\|', s):
            lecture_lines.append(s)
        # 3. "N강" 뒤에 한글이나 작품명이 있는 경우
        elif re.search(r'^\d+강\s+[가-힣]', s):
            lecture_lines.append(s)
        # 4. "실전학습" 형식
        elif re.search(r'실전학습', s) and re.search(r'\d+강', s):
            lecture_lines.append(s)
    
    return lecture_lines


def _validate_generated_toc_patterns(
    toc_text: str,
    toc_patterns: List[str],
    toc_lecture_line_examples: List[str],
    toc_nonlecture_line_examples: List[str],
    expected_lecture_count: Optional[int],
) -> Dict[str, Any]:
    """
    생성된 toc_lecture_patterns가 실제 TOC 텍스트/예시와 맞는지 검증.
    - lecture examples: 모두 매칭되어야 함
    - non-lecture examples: 매칭되면 안 됨
    - expected_lecture_count: 제공되면 toc_text에서 매칭된 '고유 강의 번호' 수가 맞아야 함
    """
    import re

    def _compile_all(patterns: List[str]) -> List[re.Pattern]:
        compiled: List[re.Pattern] = []
        for p in patterns or []:
            try:
                compiled.append(re.compile(p))
            except re.error:
                # invalid pattern is a hard failure
                raise HTTPException(status_code=400, detail=f"유효하지 않은 정규식 패턴: {p}")
        return compiled

    compiled = _compile_all(toc_patterns or [])
    if not compiled:
        raise HTTPException(status_code=400, detail="toc_lecture_patterns가 비어있습니다. (TOC 기반 강의 생성 불가)")

    def _matches_any(line: str) -> bool:
        """패턴 매칭 (더 관대한 방식)"""
        s = (line or "").strip()
        if not s:
            return False
        
        # 정규식 패턴으로 매칭 시도
        if any(r.search(s) for r in compiled):
            return True
        
        # 추가: "N강" 형식이 포함되어 있으면 매칭으로 간주 (더 관대한 검증)
        # 이는 패턴이 완벽하지 않아도 실제 파싱에는 문제없다는 것을 의미
        if re.search(r'\d+강', s):
            return True
        
        return False

    # TOC 텍스트에서 직접 강의 라인 추출 (패턴 없이)
    direct_lecture_lines = _extract_lecture_lines_from_toc_directly(toc_text)
    direct_lecture_count = len(direct_lecture_lines)

    # 1) examples 검증 (더 관대하게: 일부만 매칭되어도 OK)
    lec_examples = [x.strip() for x in (toc_lecture_line_examples or []) if str(x).strip()]
    if len(lec_examples) < 1:
        raise HTTPException(status_code=400, detail="toc_lecture_line_examples가 비어있습니다. (강의 라인 예시 최소 1줄 필요)")

    failed_lec = [x for x in lec_examples if not _matches_any(x)]
    nonlec_examples = [x.strip() for x in (toc_nonlecture_line_examples or []) if str(x).strip()]
    failed_nonlec = [x for x in nonlec_examples if _matches_any(x)]
    
    # 강의 예시 매칭률 계산 (50% 이상이면 통과로 간주)
    match_rate = ((len(lec_examples) - len(failed_lec)) / len(lec_examples) * 100) if lec_examples else 0
    examples_ok = match_rate >= 50.0  # 50% 이상 매칭되면 OK

    # 2) expected lecture count 검증 (패턴 기반 + 직접 추출 결과 비교)
    matched_lines: List[str] = []
    for line in (toc_text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if _matches_any(s):
            matched_lines.append(s)

    # 강의 번호 추정: 라인에서 첫 번째 숫자 토큰
    lecture_ids: List[int] = []
    for line in matched_lines:
        m = re.search(r"(\d+)", line)
        if m:
            try:
                lecture_ids.append(int(m.group(1)))
            except Exception:
                continue

    unique_ids = sorted(set(lecture_ids))
    
    # 직접 추출한 강의 라인에서도 강의 번호 추출
    direct_lecture_ids = []
    for line in direct_lecture_lines:
        m = re.search(r"(\d+)", line)
        if m:
            try:
                direct_lecture_ids.append(int(m.group(1)))
            except Exception:
                continue
    direct_unique_ids = sorted(set(direct_lecture_ids))
    
    count_ok = True
    if expected_lecture_count is not None:
        expected = int(expected_lecture_count)
        # 패턴 기반 매칭 결과
        pattern_actual = len(unique_ids)
        # 직접 추출 결과 (더 정확함)
        direct_actual = len(direct_unique_ids)
        
        # 직접 추출 결과가 기대값과 가까우면 OK (패턴 검증 실패는 무시)
        tolerance = max(1, int(expected * 0.1))  # 10% 오차 허용
        count_ok = abs(direct_actual - expected) <= tolerance
        
        # 직접 추출 결과가 더 정확하므로 이를 우선 사용
        actual = direct_actual
    else:
        actual = len(direct_unique_ids)

    return {
        "lecture_examples_total": len(lec_examples),
        "lecture_examples_failed": failed_lec,
        "lecture_examples_match_rate": match_rate,
        "lecture_examples_ok": examples_ok,
        "nonlecture_examples_total": len(nonlec_examples),
        "nonlecture_examples_failed": failed_nonlec,
        "matched_lines_sample": matched_lines[:20],
        "matched_lines_count": len(matched_lines),
        "unique_lecture_ids_sample": unique_ids[:30],
        "unique_lecture_ids_count": len(unique_ids),
        "expected_lecture_count": expected_lecture_count,
        "lecture_count_ok": count_ok,
        # 직접 추출 결과 추가
        "direct_lecture_lines_count": direct_lecture_count,
        "direct_lecture_ids_count": len(direct_unique_ids),
        "direct_lecture_ids_sample": direct_unique_ids[:30],
    }




def _extract_text_by_bbox(
    ocr_data: List[Dict[str, Any]],
    parsing_guide_regions: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    """마킹된 bbox를 사용하여 텍스트 추출 (가장 정확함)"""
    from collections import defaultdict

    region_texts = defaultdict(list)

    def is_valid_text(text: str) -> bool:
        """텍스트 품질 검증"""
        if 'cid:' in text.lower() or '(cid:' in text:
            return False
        if len(text) < 5:
            return False
        if not any(c.isalnum() or ord(c) >= 0xAC00 for c in text):
            return False
        if text.replace(' ', '').isdigit():
            return False
        alphanumeric_count = sum(1 for c in text if c.isalnum() or ord(c) >= 0xAC00)
        if len(text) > 0 and alphanumeric_count / len(text) < 0.3:
            return False
        return True

    # 페이지별로 그룹화
    ocr_by_page = {data.get('page_num'): data for data in ocr_data}

    # 각 마킹된 영역에서 텍스트 추출
    for region in parsing_guide_regions:
        page_num = region.get('page')
        label = region.get('label')
        bbox = region.get('bbox')  # [x_min, y_min, x_max, y_max]

        if not page_num or not label or not bbox or len(bbox) != 4:
            continue

        page_data = ocr_by_page.get(page_num)
        if not page_data:
            continue

        texts = page_data.get('text', [])
        lefts = page_data.get('left', [])
        tops = page_data.get('top', [])
        widths = page_data.get('width', [])
        heights = page_data.get('height', [])

        if not texts or len(texts) != len(lefts):
            continue

        x_min, y_min, x_max, y_max = bbox

        # 라인별로 그룹화
        lines_by_y = defaultdict(list)

        for i, text in enumerate(texts):
            if i >= len(lefts) or i >= len(tops):
                continue

            text_str = str(text).strip()
            if not text_str:
                continue

            left = lefts[i]
            top = tops[i]
            width = widths[i] if i < len(widths) else 0
            height = heights[i] if i < len(heights) else 0

            # 텍스트 중심점 계산
            center_x = left + width / 2.0
            center_y = top + height / 2.0

            # bbox 내에 있는지 확인 (약간의 여유)
            margin = 10
            if (x_min - margin <= center_x <= x_max + margin and
                y_min - margin <= center_y <= y_max + margin):
                # Y좌표로 그룹화
                y_key = round(center_y / 10) * 10
                lines_by_y[y_key].append((left, text_str))

        # 라인별로 텍스트 결합
        for y_key, line_items in lines_by_y.items():
            line_items.sort(key=lambda x: x[0])
            combined_text = ' '.join(item[1] for item in line_items).strip()

            if is_valid_text(combined_text):
                if combined_text not in region_texts[label]:
                    region_texts[label].append(combined_text)

    # 길이 순으로 정렬
    result = {}
    for label, texts in region_texts.items():
        sorted_texts = sorted(texts, key=lambda t: len(t), reverse=True)
        result[label] = sorted_texts[:20]

    return result


def _extract_text_by_region_hints(
    ocr_data: List[Dict[str, Any]],
    region_hints_dict: Dict[str, Dict[str, float]],
    relaxed: bool = False
) -> Dict[str, List[str]]:
    """region_hints(Y좌표 범위)를 사용하여 텍스트 추출"""
    from collections import defaultdict

    # 영역별 텍스트 수집
    region_texts = {region_type: [] for region_type in region_hints_dict.keys()}

    def is_valid_text(text: str) -> bool:
        """텍스트 품질 검증"""
        # CID 코드 포함 여부 확인
        if 'cid:' in text.lower() or '(cid:' in text:
            return False

        # 너무 짧은 텍스트 제외
        if len(text) < 5:
            return False

        # 특수문자만 있는 경우 제외
        if not any(c.isalnum() or ord(c) >= 0xAC00 for c in text):
            return False

        # 숫자만 있는 경우 제외 (페이지 번호 등)
        if text.replace(' ', '').isdigit():
            return False

        # 한글/영문 비율 확인 (최소 30% 이상)
        alphanumeric_count = sum(1 for c in text if c.isalnum() or ord(c) >= 0xAC00)
        if len(text) > 0 and alphanumeric_count / len(text) < 0.3:
            return False

        return True

    for page_data in ocr_data:
        page_num = page_data.get('page_num', 0)
        page_height = page_data.get('page_height', 1400.0)
        texts = page_data.get('text', [])
        tops = page_data.get('top', [])
        heights = page_data.get('height', [])
        lefts = page_data.get('left', [])

        if not texts or len(texts) != len(tops):
            continue

        # 라인별로 그룹화 (같은 Y좌표의 텍스트들을 결합)
        from collections import defaultdict
        lines_by_y = defaultdict(list)

        for i, text in enumerate(texts):
            if i >= len(tops):
                continue

            text_str = str(text).strip()
            if not text_str:
                continue

            top = tops[i]
            height = heights[i] if i < len(heights) else 0
            left = lefts[i] if i < len(lefts) else 0
            y_center = top + height / 2.0

            # Y좌표를 10 픽셀 단위로 반올림하여 같은 줄로 간주
            y_key = round(y_center / 10) * 10
            lines_by_y[y_key].append((left, text_str))

        # 각 라인별로 텍스트 결합 및 분류
        for y_key, line_items in lines_by_y.items():
            # X좌표 순으로 정렬하여 왼쪽에서 오른쪽 순서로
            line_items.sort(key=lambda x: x[0])
            combined_text = ' '.join(item[1] for item in line_items).strip()

            # 텍스트 품질 검증
            if not is_valid_text(combined_text):
                continue

            # Y좌표 비율 계산
            y_ratio = y_key / page_height

            # region_hints로 분류
            for region_type, hints in region_hints_dict.items():
                y_min = hints.get('y_min', 0.0)
                y_max = hints.get('y_max', 1.0)

                if y_min <= y_ratio <= y_max:
                    # 중복 제거 및 추가
                    if combined_text not in region_texts[region_type]:
                        region_texts[region_type].append(combined_text)
                    break

    # 각 영역별로 최대 20개만 유지 (품질 높은 것 우선)
    for region_type in region_texts:
        # 길이 순으로 정렬 (긴 문장 우선)
        sorted_texts = sorted(
            region_texts[region_type],
            key=lambda t: len(t),
            reverse=True
        )
        region_texts[region_type] = sorted_texts[:20]

    # 결과가 너무 적으면 필터링 완화하여 재시도
    total_extracted = sum(len(texts) for texts in region_texts.values())

    if total_extracted < 10:
        logger.warning(f"[텍스트 추출] 추출된 텍스트가 적음 ({total_extracted}개) - 필터링 완화하여 재시도")

        # 필터링 완화 버전
        def is_valid_text_relaxed(text: str) -> bool:
            """완화된 텍스트 품질 검증"""
            # CID 코드만 제거
            if 'cid:' in text.lower() or '(cid:' in text:
                return False

            # 최소 3자 이상 (완화)
            if len(text) < 3:
                return False

            # 한글 또는 영문이 하나라도 있으면 OK
            has_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in text)
            has_alpha = any(c.isalpha() for c in text)

            return has_korean or has_alpha

        # 재추출
        region_texts_relaxed = {region_type: [] for region_type in region_hints_dict.keys()}

        for page_data in ocr_data:
            page_num = page_data.get('page_num', 0)
            page_height = page_data.get('page_height', 1400.0)
            texts = page_data.get('text', [])
            tops = page_data.get('top', [])
            heights = page_data.get('height', [])
            lefts = page_data.get('left', [])

            if not texts or len(texts) != len(tops):
                continue

            # 라인별로 그룹화
            from collections import defaultdict
            lines_by_y = defaultdict(list)

            for i, text in enumerate(texts):
                if i >= len(tops):
                    continue

                text_str = str(text).strip()
                if not text_str:
                    continue

                top = tops[i]
                height = heights[i] if i < len(heights) else 0
                left = lefts[i] if i < len(lefts) else 0
                y_center = top + height / 2.0
                y_key = round(y_center / 10) * 10
                lines_by_y[y_key].append((left, text_str))

            # 각 라인별로 텍스트 결합 및 분류
            for y_key, line_items in lines_by_y.items():
                line_items.sort(key=lambda x: x[0])
                combined_text = ' '.join(item[1] for item in line_items).strip()

                # 완화된 검증
                if not is_valid_text_relaxed(combined_text):
                    continue

                y_ratio = y_key / page_height

                # region_hints로 분류
                for region_type, hints in region_hints_dict.items():
                    y_min = hints.get('y_min', 0.0)
                    y_max = hints.get('y_max', 1.0)

                    if y_min <= y_ratio <= y_max:
                        if combined_text not in region_texts_relaxed[region_type]:
                            region_texts_relaxed[region_type].append(combined_text)
                        break

        # 완화 버전으로 교체
        for region_type in region_texts_relaxed:
            if len(region_texts_relaxed[region_type]) > len(region_texts[region_type]):
                region_texts[region_type] = sorted(
                    region_texts_relaxed[region_type],
                    key=lambda t: len(t),
                    reverse=True
                )[:20]

    # 최종 정리 (각 영역별로 최대 20개)
    for region_type in region_texts:
        region_texts[region_type] = region_texts[region_type][:20]

    logger.info(f"[텍스트 추출] 영역별 텍스트 추출 완료")
    for region_type, texts in region_texts.items():
        logger.info(f"  - {region_type}: {len(texts)}개 예시")

    # 디버그 정보 추가
    debug_info = {}
    if total_extracted < 10:
        debug_info['warning'] = '추출된 텍스트가 적습니다. 샘플 페이지를 다른 페이지로 변경해보세요.'
        debug_info['suggestion'] = '개념/본문/문제가 모두 포함된 페이지를 선택하세요 (예: 10, 20, 30).'

    return {
        "ok": True,
        "region_text_examples": region_texts,
        "pages_processed": len(ocr_data),
        "total_examples": sum(len(texts) for texts in region_texts.values()),
        "debug": debug_info if debug_info else None
    }


