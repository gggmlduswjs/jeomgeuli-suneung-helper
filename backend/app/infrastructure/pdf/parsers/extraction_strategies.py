"""
Extraction Strategies Module

Implements extraction strategies for section extraction.
Breaks down the monolithic _extract_by_pattern() method into focused components.
"""
import logging
from typing import List, Optional, Dict
from .base import BaseParser
from .text_preprocessor import TextPreprocessor
from .font_classifier import FontBasedClassifier
from .layout_validator import LayoutBasedValidator
from .problem_pattern_matcher import ProblemPatternMatcher
from .section_spacing_validator import SectionSpacingValidator
from .extraction_config import ExtractionConfig, DEFAULT_CONFIG
from .pattern_matching import PatternMatcher
from .region_classifier import RegionClassifier
from .text_block_classifier import TextBlockClassifier
from app.infrastructure.pdf.types import (
    OCRPageData,
    SectionData,
    LectureInfo,
    JSONDict
)

logger = logging.getLogger(__name__)


class ExtractionStrategies:
    """Extraction strategies for section extraction

    Implements multiple extraction strategies:
    1. Pattern-based extraction (fast, 70-80% accuracy)
    2. AI-based extraction (slow, 85-95% accuracy)
    3. Heuristic fallback (stability, 50-70% accuracy)
    """

    def __init__(
        self,
        config: JSONDict,
        parser: Optional[BaseParser] = None,
        config_obj: Optional[ExtractionConfig] = None
    ):
        """
        Args:
            config: Parser configuration dict
            parser: BaseParser instance (for AI parsing)
            config_obj: ExtractionConfig instance (optional)
        """
        self.config = config
        self.parser = parser
        self.config_obj = config_obj or DEFAULT_CONFIG

        # Initialize pattern matcher
        self.pattern_matcher = PatternMatcher(
            concept_patterns=config.get('concept_title_patterns', []),
            content_patterns=config.get('content_header_patterns', []),
            config=self.config_obj
        )

        # Initialize region classifier
        self.region_classifier = RegionClassifier(
            region_hints=config.get('region_hints', {}),
            unit_order=config.get('unit_order', ['concept', 'passage', 'problem']),
            lecture_page_ranges=config.get('lecture_page_ranges', {}),
            config=self.config_obj
        )

        # Initialize text block classifier
        self.text_block_classifier = TextBlockClassifier(
            region_text_examples=config.get('region_text_examples', {}),
            config=self.config_obj
        )

        # Initialize validators and classifiers
        self.font_classifier = FontBasedClassifier(config.get('font_info'))
        self.layout_validator = LayoutBasedValidator(config.get('layout_info'))
        self.problem_matcher = ProblemPatternMatcher(config.get('problem_patterns'))
        self.spacing_validator = SectionSpacingValidator(config.get('section_spacing'))

    def extract_by_pattern(
        self,
        lecture_ocr_data: List[OCRPageData]
    ) -> JSONDict:
        """Pattern-based section extraction (orchestrator)

        Args:
            lecture_ocr_data: OCR data for the lecture

        Returns:
            Dict with sections, confidence, and metadata
        """
        try:
            if not lecture_ocr_data:
                logger.warning("[Strategy] OCR data is empty")
                return {
                    'sections': [],
                    'confidence': 0.0,
                    'metadata': {'error': 'Empty OCR data'}
                }

            logger.info(f"[Strategy] Starting pattern extraction: {len(lecture_ocr_data)} pages")

            sections = []
            matched_count = 0
            total_lines = 0

            start_page = self.config.get(
                'start_content_page',
                self.config_obj.default_start_page
            )

            # Find actual start page
            actual_start_page = min(
                ocr_data.get('page_num', 0)
                for ocr_data in lecture_ocr_data
            )
            search_start_page = min(start_page, actual_start_page)

            # Process each page
            for ocr_data in lecture_ocr_data:
                page_sections, page_matched, page_total = self._process_page(
                    ocr_data,
                    search_start_page
                )
                sections.extend(page_sections)
                matched_count += page_matched
                total_lines += page_total

            # Apply validators
            sections = self._apply_validators(sections)

            # Calculate confidence
            confidence = self._calculate_confidence(
                sections,
                matched_count,
                total_lines
            )

            logger.info(
                f"[Strategy] Pattern extraction complete: {len(sections)} sections, "
                f"confidence: {confidence:.2f}"
            )

            return {
                'sections': sections,
                'confidence': confidence,
                'metadata': {
                    'matched_count': matched_count,
                    'total_lines': total_lines,
                    'method': 'pattern'
                }
            }

        except Exception as e:
            logger.error(f"[Strategy] Pattern extraction error: {e}", exc_info=True)
            return {
                'sections': [],
                'confidence': 0.0,
                'metadata': {'error': str(e)}
            }

    def _process_page(
        self,
        ocr_data: OCRPageData,
        start_page: int
    ) -> tuple[List[SectionData], int, int]:
        """Process a single page for pattern matching

        Args:
            ocr_data: OCR data for the page
            start_page: Starting page number to process

        Returns:
            Tuple of (sections, matched_count, total_lines)
        """
        page_num = ocr_data.get('page_num', 0)

        if page_num < start_page:
            return ([], 0, 0)

        texts = ocr_data.get('text', [])
        if not texts:
            return ([], 0, 0)

        # Group lines
        lines = BaseParser.group_lines(
            ocr_data,
            y_threshold=self.config_obj.line_grouping_threshold
        )

        # Get lecture info
        lecture_info = self.region_classifier.get_lecture_info_for_page(page_num)

        # Process each line
        sections = []
        matched_count = 0

        for line_idx, line in enumerate(lines):
            section = self._process_line(
                line,
                line_idx,
                lines,
                ocr_data,
                lecture_info
            )

            if section:
                sections.append(section)
                matched_count += 1

        return (sections, matched_count, len(lines))

    def _process_line(
        self,
        line: List[JSONDict],
        line_idx: int,
        lines: List[List[JSONDict]],
        ocr_data: OCRPageData,
        lecture_info: Optional[LectureInfo]
    ) -> Optional[SectionData]:
        """Process a single line for section matching

        Args:
            line: Line data (list of word dicts)
            line_idx: Line index
            lines: All lines on the page
            ocr_data: OCR data for the page
            lecture_info: Lecture information

        Returns:
            SectionData if matched, None otherwise
        """
        try:
            line_text = BaseParser.join_line_text(line)
            line_text = TextPreprocessor.normalize_text(line_text)
        except Exception as e:
            logger.warning(f"[Strategy] Line processing error: {e}")
            return None

        if not line_text:
            return None

        # Check for noise
        if self.pattern_matcher.is_noise(line_text):
            return None

        section_type = None
        section_title = None

        # Try font-based classification
        if self.font_classifier.enabled and line:
            font_result = self.font_classifier.classify_by_font(
                line[0],
                line_text
            )
            if (
                font_result
                and font_result.get('confidence', 0) >= self.config_obj.region_hint_high_confidence
            ):
                section_type = font_result.get('type')
                section_title = line_text

        # Try text block classification
        if not section_type:
            text_result = self.text_block_classifier.classify_text_for_section_titles(
                line_text
            )
            if text_result.matched:
                section_type = text_result.match_type
                section_title = line_text

        # Try pattern matching
        if not section_type:
            pattern_result = self.pattern_matcher.match_text(line_text)
            if pattern_result.matched:
                section_type = pattern_result.match_type
                section_title = line_text

                # Check if content pattern with next line
                if (
                    section_type == 'content'
                    and line_idx + 1 < len(lines)
                ):
                    next_line = lines[line_idx + 1]
                    next_text = BaseParser.join_line_text(next_line)
                    next_text = TextPreprocessor.normalize_text(next_text)
                    section_title = self.pattern_matcher.extract_title_with_next_line(
                        section_title,
                        next_text
                    )

        if not section_type or not section_title:
            return None

        # Get bbox
        bbox = BaseParser.get_line_bbox(line)

        # Apply region classification
        section_type, region_confidence = self._apply_region_classification(
            section_type,
            bbox,
            ocr_data,
            lecture_info
        )

        # Create section
        section: SectionData = {
            "title": section_title[:self.config_obj.max_title_length],
            "type": section_type,
            "page": ocr_data.get('page_num', 0),
            "bbox": bbox
        }

        # Add region metadata
        if region_confidence > 0:
            section["region_confidence"] = region_confidence
            section["from_region_hint"] = True

        # Add lecture metadata
        if lecture_info:
            section["lecture_id"] = lecture_info.get('lecture_id')
            section["lecture_page_ratio"] = lecture_info.get('page_ratio')

        return section

    def _apply_region_classification(
        self,
        section_type: str,
        bbox: Optional[tuple],
        ocr_data: OCRPageData,
        lecture_info: Optional[LectureInfo]
    ) -> tuple[str, float]:
        """Apply region-based classification to adjust section type

        Args:
            section_type: Initial section type
            bbox: Bounding box
            ocr_data: OCR data
            lecture_info: Lecture information

        Returns:
            Tuple of (adjusted_type, region_confidence)
        """
        if not bbox or len(bbox) < 4:
            return (section_type, 0.0)

        page_height = ocr_data.get('page_height', self.config_obj.default_page_height)
        if page_height <= 0:
            page_height = self.config_obj.default_page_height

        y_center = (bbox[1] + bbox[3]) / 2.0
        y_ratio = y_center / page_height

        # Get region classification
        hint_result = self.region_classifier.classify_by_region_hint(
            y_ratio,
            page_height,
            lecture_info
        )

        if not hint_result:
            return (section_type, 0.0)

        hint_type, hint_confidence = hint_result

        # Get dynamic threshold
        threshold = self.region_classifier.get_dynamic_threshold(
            hint_type,
            lecture_info
        )

        # Apply classification if confidence is high enough
        if hint_confidence > threshold:
            # Type mapping
            if section_type == 'content' and hint_type == 'passage':
                section_type = 'passage'
            elif not section_type or section_type == 'unknown':
                section_type = hint_type
            elif section_type != hint_type:
                # Override if confidence is very high
                logger.debug(
                    f"[Region] Type override: {section_type} -> {hint_type} "
                    f"(confidence: {hint_confidence:.2f})"
                )
                section_type = hint_type

        return (section_type, hint_confidence)

    def _apply_validators(
        self,
        sections: List[SectionData]
    ) -> List[SectionData]:
        """Apply validators to filter and refine sections

        Args:
            sections: List of sections

        Returns:
            Filtered and refined sections
        """
        # Layout validation (header/footer filtering)
        if self.layout_validator.enabled:
            sections = self.layout_validator.filter_header_footer(sections)

        # Section spacing validation
        if self.spacing_validator.enabled and len(sections) > 1:
            sections = self.spacing_validator.find_section_boundaries(sections)

        return sections

    def _calculate_confidence(
        self,
        sections: List[SectionData],
        matched_count: int,
        total_lines: int
    ) -> float:
        """Calculate extraction confidence

        Args:
            sections: Extracted sections
            matched_count: Number of matched lines
            total_lines: Total lines processed

        Returns:
            Confidence score (0.0-1.0)
        """
        if total_lines == 0:
            return 0.0

        # Base confidence from match ratio
        match_ratio = matched_count / total_lines
        confidence = min(
            match_ratio * self.config_obj.match_ratio_multiplier,
            1.0
        )

        # Bonus for multiple sections
        if len(sections) >= 3:
            confidence = min(
                confidence + self.config_obj.bonus_multiple_sections,
                1.0
            )

        # Bonus for region hints
        region_based_count = sum(
            1 for s in sections
            if s.get("from_region_hint", False)
        )
        if len(sections) > 0:
            region_ratio = region_based_count / len(sections)
            if region_ratio > 0.5:
                confidence = min(
                    confidence + self.config_obj.bonus_high_region_ratio,
                    1.0
                )
            elif region_ratio > 0.3:
                confidence = min(
                    confidence + self.config_obj.bonus_medium_region_ratio,
                    1.0
                )

        # Bonus for enabled features
        if self.font_classifier.enabled:
            confidence = min(
                confidence + self.config_obj.bonus_font_classifier,
                1.0
            )

        if self.layout_validator.enabled:
            confidence = min(
                confidence + self.config_obj.bonus_layout_validator,
                1.0
            )

        return confidence

    def extract_by_ai(
        self,
        lecture_ocr_data: List[OCRPageData]
    ) -> JSONDict:
        """AI-based section extraction

        Args:
            lecture_ocr_data: OCR data for the lecture

        Returns:
            Dict with sections, confidence, and metadata
        """
        if not self.parser or not hasattr(self.parser, 'extract_sections'):
            return {'sections': [], 'confidence': 0.0}

        try:
            sections = self.parser.extract_sections(lecture_ocr_data)
            confidence = 0.85 if sections else 0.0

            return {
                'sections': sections,
                'confidence': confidence,
                'metadata': {'method': 'ai_parser'}
            }
        except Exception as e:
            logger.error(f"[Strategy] AI extraction error: {e}")
            return {'sections': [], 'confidence': 0.0}

    def extract_by_heuristic(
        self,
        lecture_ocr_data: List[OCRPageData]
    ) -> JSONDict:
        """Heuristic-based fallback extraction

        Args:
            lecture_ocr_data: OCR data for the lecture

        Returns:
            Dict with sections, confidence, and metadata
        """
        sections = []
        start_page = self.config.get(
            'start_content_page',
            self.config_obj.default_start_page
        )

        # Try region hints only approach first
        if self.region_classifier.region_hints:
            logger.info("[Strategy] Trying region hints only extraction")
            region_sections = self.extract_sections_by_region_hints_only(
                lecture_ocr_data,
                start_page
            )
            if region_sections:
                return {
                    'sections': region_sections,
                    'confidence': self.config_obj.region_hints_only_confidence,
                    'metadata': {'method': 'region_hints_only'}
                }

        # Fall back to basic heuristics
        for ocr_data in lecture_ocr_data:
            page_sections = self._extract_page_heuristic(ocr_data, start_page)
            sections.extend(page_sections)

        # Calculate confidence
        confidence = self.config_obj.heuristic_base_confidence if sections else 0.0
        if len(sections) >= 2:
            confidence = self.config_obj.heuristic_multi_section_confidence

        return {
            'sections': sections,
            'confidence': confidence,
            'metadata': {'method': 'heuristic'}
        }

    def _extract_page_heuristic(
        self,
        ocr_data: OCRPageData,
        start_page: int
    ) -> List[SectionData]:
        """Extract sections from a page using heuristics

        Args:
            ocr_data: OCR data for the page
            start_page: Starting page number

        Returns:
            List of sections
        """
        page_num = ocr_data.get('page_num', 0)
        if page_num < start_page:
            return []

        texts = ocr_data.get('text', [])
        heights = ocr_data.get('height', [])

        if not texts:
            return []

        sections = []
        lines = BaseParser.group_lines(
            ocr_data,
            y_threshold=self.config_obj.line_grouping_threshold
        )
        lecture_info = self.region_classifier.get_lecture_info_for_page(page_num)

        for line in lines:
            if not line:
                continue

            line_text = BaseParser.join_line_text(line)
            line_text = TextPreprocessor.normalize_text(line_text)

            if not line_text or len(line_text) < 2:
                continue

            # Heuristic 1: Number-prefixed short text
            if (
                line_text[0].isdigit()
                and len(line_text) < self.config_obj.short_text_max_length
            ):
                # Check font height
                avg_height = sum(
                    heights[word.get('index', 0)]
                    for word in line
                    if word.get('index', 0) < len(heights)
                ) / len(line) if line else 0

                if avg_height >= self.config_obj.title_font_height_threshold:
                    bbox = BaseParser.get_line_bbox(line)
                    section_type = "concept"

                    # Apply region classification
                    if bbox and self.region_classifier.region_hints:
                        section_type, _ = self._apply_region_classification(
                            section_type,
                            bbox,
                            ocr_data,
                            lecture_info
                        )

                    sections.append({
                        "title": line_text,
                        "type": section_type,
                        "page": page_num,
                        "bbox": bbox
                    })

            # Heuristic 2: Content keywords
            if any(kw in line_text for kw in self.config_obj.content_keywords):
                line_y = line[0].get('top', 0) if line else 0
                if line_y < self.config_obj.page_header_max_y:
                    sections.append({
                        "title": line_text,
                        "type": "content",
                        "page": page_num,
                        "bbox": BaseParser.get_line_bbox(line)
                    })

        return sections

    def extract_sections_by_region_hints_only(
        self,
        lecture_ocr_data: List[OCRPageData],
        start_page: int
    ) -> List[SectionData]:
        """Extract sections using only region hints (Y-coordinate based)

        Args:
            lecture_ocr_data: OCR data for the lecture
            start_page: Starting page number

        Returns:
            List of sections
        """
        if not self.region_classifier.region_hints:
            return []

        sections = []

        for ocr_data in lecture_ocr_data:
            page_sections = self._extract_page_by_region_hints(
                ocr_data,
                start_page
            )
            sections.extend(page_sections)

        return sections

    def _extract_page_by_region_hints(
        self,
        ocr_data: OCRPageData,
        start_page: int
    ) -> List[SectionData]:
        """Extract sections from a page using region hints

        Args:
            ocr_data: OCR data for the page
            start_page: Starting page number

        Returns:
            List of sections
        """
        page_num = ocr_data.get('page_num', 0)
        if page_num < start_page:
            return []

        texts = ocr_data.get('text', [])
        if not texts:
            return []

        page_height = ocr_data.get('page_height', self.config_obj.default_page_height)
        if page_height <= 0:
            page_height = self.config_obj.default_page_height

        lecture_info = self.region_classifier.get_lecture_info_for_page(page_num)
        lines = BaseParser.group_lines(
            ocr_data,
            y_threshold=self.config_obj.region_line_threshold
        )

        # Collect texts by region
        region_texts: Dict[str, List[Dict]] = {
            unit_type: []
            for unit_type in self.region_classifier.region_hints.keys()
        }

        for line in lines:
            if not line:
                continue

            line_text = BaseParser.join_line_text(line)
            line_text = TextPreprocessor.normalize_text(line_text)

            if (
                not line_text
                or len(line_text) < self.config_obj.min_region_text_length
            ):
                continue

            # Skip noise
            if self.pattern_matcher.is_noise(line_text):
                continue

            bbox = BaseParser.get_line_bbox(line)
            if not bbox or len(bbox) < 4:
                continue

            y_center = (bbox[1] + bbox[3]) / 2.0
            y_ratio = y_center / page_height

            # Classify by region
            hint_result = self.region_classifier.classify_by_region_hint(
                y_ratio,
                page_height,
                lecture_info
            )

            if hint_result:
                unit_type, confidence = hint_result
                if confidence >= self.config_obj.region_hint_fallback_threshold:
                    region_texts[unit_type].append({
                        'text': line_text,
                        'bbox': bbox,
                        'y_ratio': y_ratio,
                        'confidence': confidence
                    })

        # Create sections from regions
        sections = []
        for unit_type, text_items in region_texts.items():
            if not text_items:
                continue

            # Sort by Y position
            text_items.sort(key=lambda x: x['y_ratio'])

            # Find best title candidate (longest text >= 5 chars)
            candidate = None
            for item in text_items:
                if len(item['text']) >= self.config_obj.min_region_text_length:
                    candidate = item
                    break

            if not candidate:
                candidate = text_items[0]

            # Normalize type
            if unit_type == 'content':
                unit_type = 'passage'

            section: SectionData = {
                "title": candidate['text'][:self.config_obj.max_title_length],
                "type": unit_type,
                "page": page_num,
                "bbox": candidate['bbox'],
                "from_region_hint": True,
                "region_confidence": candidate['confidence'],
                "source": "region_hints_only"
            }

            if lecture_info:
                section["lecture_id"] = lecture_info.get('lecture_id')
                section["lecture_page_ratio"] = lecture_info.get('page_ratio')

            sections.append(section)

        return sections

    def merge_sections(
        self,
        sections1: List[SectionData],
        sections2: List[SectionData]
    ) -> List[SectionData]:
        """Merge two section lists (remove duplicates)

        Args:
            sections1: First section list
            sections2: Second section list

        Returns:
            Merged section list
        """
        merged = []
        seen = set()

        for section in sections1 + sections2:
            key = (section.get('page', 0), section.get('title', ''))
            if key not in seen:
                seen.add(key)
                merged.append(section)

        return merged
