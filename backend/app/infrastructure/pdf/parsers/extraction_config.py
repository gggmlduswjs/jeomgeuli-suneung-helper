"""
Extraction Configuration Module

Centralized configuration and constants for section extraction.
All magic numbers and thresholds are defined here for easy tuning.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class ExtractionConfig:
    """Configuration for section extraction

    All thresholds and magic numbers are centralized here
    to avoid hard-coding values throughout the codebase.
    """

    # ============================================================================
    # Confidence Thresholds
    # ============================================================================

    # Minimum confidence for pattern matching success
    pattern_confidence_threshold: float = 0.7

    # Minimum confidence for AI extraction success
    ai_confidence_threshold: float = 0.7

    # Region hint confidence thresholds
    region_hint_high_confidence: float = 0.7
    region_hint_dynamic_threshold: float = 0.65
    region_hint_relaxed_threshold: float = 0.55
    region_hint_fallback_threshold: float = 0.5

    # Text block classification thresholds
    text_block_exact_match_score: float = 1.0
    text_block_keyword_score: float = 0.7
    text_block_partial_score: float = 0.6
    text_block_prefix_score: float = 0.5
    text_block_min_threshold: float = 0.5
    text_block_general_threshold: float = 0.4

    # ============================================================================
    # Y-Coordinate Thresholds (for line grouping and layout analysis)
    # ============================================================================

    # Threshold for grouping lines (pixels)
    line_grouping_threshold: int = 10

    # Threshold for paragraph detection
    paragraph_y_threshold: int = 25

    # Threshold for region-based line grouping
    region_line_threshold: int = 15

    # Maximum Y position for page header detection
    page_header_max_y: int = 200

    # ============================================================================
    # Text Length Limits
    # ============================================================================

    # Minimum text length for processing
    min_text_length: int = 3

    # Maximum length for short text (concept titles)
    short_text_max_length: int = 30

    # Maximum length for medium text
    medium_text_max_length: int = 50

    # Maximum title length to store
    max_title_length: int = 100

    # Minimum length for region-based classification
    min_region_text_length: int = 5

    # ============================================================================
    # Confidence Bonuses (incremental improvements)
    # ============================================================================

    # Bonus for having 3+ sections
    bonus_multiple_sections: float = 0.2

    # Bonus for high region hint usage (>50%)
    bonus_high_region_ratio: float = 0.15

    # Bonus for medium region hint usage (>30%)
    bonus_medium_region_ratio: float = 0.1

    # Bonus for region hints enabled
    bonus_region_hints_active: float = 0.1

    # Bonus for font classifier enabled
    bonus_font_classifier: float = 0.1

    # Bonus for layout validator enabled
    bonus_layout_validator: float = 0.05

    # ============================================================================
    # Page and Layout Defaults
    # ============================================================================

    # Default page height in pixels
    default_page_height: float = 1400.0

    # Default start page for content
    default_start_page: int = 8

    # Average font height threshold for titles
    title_font_height_threshold: int = 15

    # ============================================================================
    # Region Position Expectations (for lecture-aware classification)
    # ============================================================================

    # Expected position ranges for each unit type within a lecture
    expected_position_ranges: dict = field(default_factory=lambda: {
        'concept': (0.0, 0.3),    # Concepts usually in first 30% of lecture
        'passage': (0.3, 0.7),    # Passages in middle 30-70%
        'problem': (0.7, 1.0)     # Problems in last 30%
    })

    # ============================================================================
    # Multipliers and Scaling Factors
    # ============================================================================

    # Multiplier for match ratio to confidence
    match_ratio_multiplier: float = 2.0

    # Confidence increase for lecture position match
    lecture_position_match_multiplier: float = 1.3

    # Confidence decrease for lecture position mismatch
    lecture_position_mismatch_multiplier: float = 0.8

    # Region confidence min/max bounds
    region_confidence_min: float = 0.5
    region_confidence_max: float = 1.0

    # ============================================================================
    # Heuristic Confidence Levels
    # ============================================================================

    # Base heuristic confidence (when sections found)
    heuristic_base_confidence: float = 0.5

    # Heuristic confidence with multiple sections
    heuristic_multi_section_confidence: float = 0.6

    # Region hints only strategy confidence
    region_hints_only_confidence: float = 0.7

    # ============================================================================
    # Content Filtering Patterns (noise detection)
    # ============================================================================

    # Keywords for content detection
    content_keywords: List[str] = field(default_factory=lambda: [
        '작품', '이해', '읽기', '분석', '해석',
        '고전', '현대', '시가', '산문', '소설'
    ])

    # ============================================================================
    # Validation Settings
    # ============================================================================

    # Maximum number of words in a concept title
    max_concept_title_words: int = 5

    # Minimum Korean characters for fallback matching
    min_korean_chars_fallback: int = 3


# Default global instance
DEFAULT_CONFIG = ExtractionConfig()
