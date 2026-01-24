"""
Pattern Matching Module

Handles pattern-based text matching and validation for section extraction.
Includes noise filtering, concept/content pattern matching, and fallback heuristics.
"""
import re
import logging
from typing import List, Optional, Tuple
from .extraction_config import ExtractionConfig, DEFAULT_CONFIG
from .extraction_types import TextMatchResult
from .base import BaseParser

logger = logging.getLogger(__name__)


class PatternMatcher:
    """Pattern-based text matcher for section extraction

    Responsibilities:
    - Validate text against patterns
    - Filter out noise (dates, page numbers, TOC)
    - Match concept patterns
    - Match content patterns
    - Apply fallback heuristics
    """

    def __init__(
        self,
        concept_patterns: List[str],
        content_patterns: List[str],
        config: Optional[ExtractionConfig] = None
    ):
        """
        Args:
            concept_patterns: Regular expressions for concept titles
            content_patterns: Regular expressions for content headers
            config: Extraction configuration (optional)
        """
        self.concept_patterns = concept_patterns or []
        self.content_patterns = content_patterns or []
        self.config = config or DEFAULT_CONFIG

        # Set default patterns if not provided
        if not self.concept_patterns:
            self.concept_patterns = [
                r'^(\d+)\s*[\.]\s*([가-힣\s]{2,20})$',
                r'^\d+\s+[가-힣]{2,}\s*[가-힣]*$'
            ]

    def is_noise(self, text: str) -> bool:
        """Check if text is noise that should be filtered out

        Args:
            text: Text to check

        Returns:
            True if text is noise (date, page number, TOC, etc.)
        """
        if not text:
            return True

        text = text.strip()

        # Empty text
        if not text:
            return True

        # Numbers only (e.g., "1", "2.")
        if re.match(r'^\d+\.?\s*$', text):
            return True

        # TOC pattern (3 digits)
        if re.search(r'\d{3}', text) and len(text) < self.config.short_text_max_length:
            return True

        # Date/time pattern (e.g., "25. 1. 6. 오후 6:01")
        if re.search(r'\d+\.\s*\d+\.\s*\d+\.\s*(오전|오후|AM|PM)\s*\d+:\d+', text):
            return True

        # Page number pattern (e.g., "128 EBS", "202 EBS")
        if re.match(r'^\d+\s+EBS\s*$', text):
            return True

        return False

    def matches_concept_pattern(self, text: str) -> Optional[Tuple[str, str]]:
        """Check if text matches concept title patterns

        Args:
            text: Text to check

        Returns:
            Tuple of (matched_text, pattern_type) if matched, None otherwise
        """
        if not text:
            return None

        # Pattern 1: "1. 시적 표현" (number with period)
        main_concept_match = re.match(
            r'^(\d+)\s*[\.]\s*([가-힣\s]{4,50})$',  # Min 4 chars
            text
        )
        if main_concept_match:
            return (text, 'numbered_with_period')

        # Pattern 2: "1 시적 표현" (number without period)
        if (
            re.match(r'^\d+\s+[가-힣]{4,}\s*[가-힣]*$', text)
            and len(text.split()) <= self.config.max_concept_title_words
        ):
            return (text, 'numbered_without_period')

        # Pattern 3: Custom patterns from config
        if self.concept_patterns:
            for pattern in self.concept_patterns:
                if re.search(pattern, text):
                    # Additional validation after pattern match
                    if not self.is_noise(text):
                        return (text, 'custom_pattern')

        return None

    def matches_content_pattern(self, text: str) -> bool:
        """Check if text matches content header patterns

        Args:
            text: Text to check

        Returns:
            True if matches content pattern
        """
        if not text or not self.content_patterns:
            return False

        return BaseParser.matches_patterns(text, self.content_patterns)

    def apply_fallback_heuristic(self, text: str) -> bool:
        """Apply fallback heuristic for concept detection

        When pattern matching fails, use lenient heuristics:
        - Korean text (3+ chars)
        - Short text (<= 30 chars)
        - Starts with number

        Args:
            text: Text to check

        Returns:
            True if likely a concept title
        """
        if not text:
            return False

        if (
            len(text) <= self.config.short_text_max_length
            and len(text) >= self.config.min_text_length
        ):
            korean_chars = len(re.findall(r'[가-힣]', text))
            if korean_chars >= self.config.min_korean_chars_fallback:
                # Must start with number (not too lenient)
                if re.match(r'^\d+[\.\s]', text):
                    return True

        return False

    def extract_title_with_next_line(
        self,
        current_text: str,
        next_line_text: Optional[str]
    ) -> str:
        """Extract title with potential subtitle from next line

        For content sections like "작품으로 이해하기", the actual
        work title may be on the next line (e.g., "춘향전 [작자 미상]")

        Args:
            current_text: Current line text
            next_line_text: Next line text (optional)

        Returns:
            Combined title if next line contains work title, else current text
        """
        if not next_line_text:
            return current_text

        # Check for work title patterns
        # Pattern 1: "작품명 [저자명]"
        if re.search(r'[가-힣]+\s*\[[가-힣]+\]', next_line_text):
            return f"{current_text} - {next_line_text}"

        # Pattern 2: "작품명 「저자명」"
        if re.search(r'[가-힣]+\s*「[가-힣]+」', next_line_text):
            return f"{current_text} - {next_line_text}"

        return current_text

    def match_text(self, text: str) -> TextMatchResult:
        """Match text against all available patterns

        Args:
            text: Text to match

        Returns:
            TextMatchResult with match information
        """
        # Check noise first
        if self.is_noise(text):
            return TextMatchResult(matched=False, method='noise_filter')

        # Try concept patterns
        concept_match = self.matches_concept_pattern(text)
        if concept_match:
            _, pattern_type = concept_match
            return TextMatchResult(
                matched=True,
                match_type='concept',
                score=1.0,
                method=pattern_type
            )

        # Try content patterns
        if self.matches_content_pattern(text):
            return TextMatchResult(
                matched=True,
                match_type='content',
                score=1.0,
                method='content_pattern'
            )

        # Try fallback heuristic
        if self.apply_fallback_heuristic(text):
            return TextMatchResult(
                matched=True,
                match_type='concept',
                score=0.6,
                method='fallback_heuristic'
            )

        return TextMatchResult(matched=False, method='no_match')
