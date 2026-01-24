"""
Region Classifier Module

Handles Y-coordinate based region classification for section extraction.
Classifies text blocks based on their position within a page and lecture.
"""
import logging
from typing import Optional, Tuple, Dict, List
from .extraction_config import ExtractionConfig, DEFAULT_CONFIG
from .extraction_types import RegionClassification
from app.infrastructure.pdf.types import LectureInfo, BoundingBox, JSONDict

logger = logging.getLogger(__name__)


class RegionClassifier:
    """Y-coordinate based region classifier

    Responsibilities:
    - Classify text based on Y-coordinate position
    - Analyze lecture position for context-aware classification
    - Calculate confidence based on position certainty
    """

    def __init__(
        self,
        region_hints: Dict[str, JSONDict],
        unit_order: List[str],
        lecture_page_ranges: Optional[Dict[int, JSONDict]] = None,
        config: Optional[ExtractionConfig] = None
    ):
        """
        Args:
            region_hints: Y-coordinate ranges for each unit type
                         e.g., {'concept': {'y_min': 0.0, 'y_max': 0.3}}
            unit_order: Order of units in document (e.g., ['concept', 'passage', 'problem'])
            lecture_page_ranges: Page ranges for each lecture (optional)
            config: Extraction configuration (optional)
        """
        self.region_hints = region_hints or {}
        self.unit_order = unit_order or ['concept', 'passage', 'problem']
        self.lecture_page_ranges = lecture_page_ranges or {}
        self.config = config or DEFAULT_CONFIG

        if self.region_hints:
            logger.info(
                f"[RegionClassifier] Initialized with region_hints: "
                f"{list(self.region_hints.keys())}"
            )

    def get_lecture_info_for_page(self, page_num: int) -> Optional[LectureInfo]:
        """Get lecture information for a specific page

        Args:
            page_num: Page number

        Returns:
            Lecture information dict or None
            {
                'lecture_id': int,
                'start_page': int,
                'end_page': Optional[int],
                'page_index': int,  # Relative position within lecture (0-based)
                'page_ratio': float  # Relative position (0.0-1.0)
            }
        """
        if not self.lecture_page_ranges:
            return None

        for lecture_id, range_info in self.lecture_page_ranges.items():
            start = range_info.get('start_page')
            end = range_info.get('end_page')

            if start is not None:
                if end is not None:
                    if start <= page_num <= end:
                        total_pages = end - start + 1
                        page_index = page_num - start
                        page_ratio = page_index / total_pages if total_pages > 0 else 0.0
                        return {
                            'lecture_id': lecture_id,
                            'start_page': start,
                            'end_page': end,
                            'page_index': page_index,
                            'page_ratio': page_ratio,
                            'total_pages': total_pages
                        }
                else:
                    # Last lecture (end_page is None)
                    if page_num >= start:
                        return {
                            'lecture_id': lecture_id,
                            'start_page': start,
                            'end_page': None,
                            'page_index': page_num - start,
                            'page_ratio': 0.5,  # Approximate middle
                            'total_pages': None
                        }

        return None

    def classify_by_region_hint(
        self,
        y_ratio: float,
        page_height: float = 1400.0,
        lecture_info: Optional[LectureInfo] = None
    ) -> Optional[Tuple[str, float]]:
        """Classify region based on Y-coordinate ratio

        Args:
            y_ratio: Y-coordinate ratio within page (0.0-1.0)
            page_height: Page height in pixels (default 1400)
            lecture_info: Lecture information (optional, for position-aware classification)

        Returns:
            Tuple of (unit_type, confidence) or None
            - unit_type: 'concept', 'passage', 'problem'
            - confidence: 0.0-1.0 (higher near region center)
        """
        if not self.region_hints:
            return None

        best_match = None
        best_confidence = 0.0

        # Check in unit_order sequence
        for unit_type in self.unit_order:
            if unit_type not in self.region_hints:
                continue

            hint = self.region_hints[unit_type]
            y_min = hint.get('y_min', 0.0)
            y_max = hint.get('y_max', 1.0)

            # Check if y_ratio is within hint range
            if y_min <= y_ratio <= y_max:
                # Confidence increases toward region center
                y_center = (y_min + y_max) / 2.0
                distance_from_center = abs(y_ratio - y_center)
                range_size = y_max - y_min

                if range_size > 0:
                    # Center: 1.0, Edge: 0.5
                    confidence = 1.0 - (distance_from_center / (range_size / 2.0)) * 0.5
                    confidence = max(
                        self.config.region_confidence_min,
                        min(self.config.region_confidence_max, confidence)
                    )
                else:
                    confidence = 1.0

                # Adjust confidence based on lecture position
                if lecture_info:
                    confidence = self._adjust_confidence_by_lecture_position(
                        unit_type,
                        confidence,
                        lecture_info
                    )

                if confidence > best_confidence:
                    best_match = unit_type
                    best_confidence = confidence

        if best_match:
            return (best_match, best_confidence)
        return None

    def _adjust_confidence_by_lecture_position(
        self,
        unit_type: str,
        confidence: float,
        lecture_info: LectureInfo
    ) -> float:
        """Adjust confidence based on expected position within lecture

        Args:
            unit_type: Unit type being classified
            confidence: Initial confidence
            lecture_info: Lecture information

        Returns:
            Adjusted confidence
        """
        page_ratio = lecture_info.get('page_ratio', 0.5)

        # Expected position ranges from config
        expected_ranges = self.config.expected_position_ranges

        if unit_type in expected_ranges:
            expected_min, expected_max = expected_ranges[unit_type]

            if expected_min <= page_ratio <= expected_max:
                # Position matches expectation -> increase confidence
                confidence = min(
                    self.config.region_confidence_max,
                    confidence * self.config.lecture_position_match_multiplier
                )
                logger.debug(
                    f"[Lecture position boost] {unit_type} at expected position "
                    f"({expected_min:.1f}-{expected_max:.1f}), "
                    f"page_ratio={page_ratio:.2f}"
                )
            else:
                # Position doesn't match -> decrease confidence
                confidence = confidence * self.config.lecture_position_mismatch_multiplier
                logger.debug(
                    f"[Lecture position penalty] {unit_type} NOT at expected position "
                    f"({expected_min:.1f}-{expected_max:.1f}), "
                    f"page_ratio={page_ratio:.2f}"
                )

        return confidence

    def get_dynamic_threshold(
        self,
        unit_type: str,
        lecture_info: Optional[LectureInfo]
    ) -> float:
        """Get dynamic confidence threshold based on lecture position

        Returns a lower threshold when the unit type is expected
        at the current lecture position.

        Args:
            unit_type: Unit type to check
            lecture_info: Lecture information

        Returns:
            Confidence threshold (0.0-1.0)
        """
        if not lecture_info:
            return self.config.region_hint_high_confidence

        page_ratio = lecture_info.get('page_ratio', 0.5)
        expected_ranges = self.config.expected_position_ranges

        if unit_type in expected_ranges:
            expected_min, expected_max = expected_ranges[unit_type]

            if expected_min <= page_ratio <= expected_max:
                # At expected position -> use relaxed threshold
                return self.config.region_hint_relaxed_threshold
            else:
                # Not at expected position -> use normal threshold
                return self.config.region_hint_dynamic_threshold

        return self.config.region_hint_high_confidence

    def is_in_region_hint(
        self,
        y_ratio: float,
        unit_type: Optional[str] = None
    ) -> bool:
        """Check if Y-coordinate is within region hint area

        Args:
            y_ratio: Y-coordinate ratio (0.0-1.0)
            unit_type: Specific unit type to check (None for any type)

        Returns:
            True if within region hint area
        """
        if not self.region_hints:
            return False

        if unit_type:
            if unit_type not in self.region_hints:
                return False
            hint = self.region_hints[unit_type]
            y_min = hint.get('y_min', 0.0)
            y_max = hint.get('y_max', 1.0)
            return y_min <= y_ratio <= y_max
        else:
            # Check all types
            for hint in self.region_hints.values():
                y_min = hint.get('y_min', 0.0)
                y_max = hint.get('y_max', 1.0)
                if y_min <= y_ratio <= y_max:
                    return True
            return False
