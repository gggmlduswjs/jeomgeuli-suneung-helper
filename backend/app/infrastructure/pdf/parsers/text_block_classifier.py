"""
Text Block Classifier Module

Handles text block classification using example-based matching.
Calculates text similarity and classifies blocks into unit types.
"""
import logging
from typing import Dict, List, Optional, Tuple
from .extraction_config import ExtractionConfig, DEFAULT_CONFIG
from .extraction_types import TextMatchResult

logger = logging.getLogger(__name__)


class TextBlockClassifier:
    """Example-based text block classifier

    Responsibilities:
    - Calculate text similarity using multiple methods
    - Classify text blocks using region_text_examples
    - Score and rank classification results
    """

    def __init__(
        self,
        region_text_examples: Dict[str, List[str]],
        config: Optional[ExtractionConfig] = None
    ):
        """
        Args:
            region_text_examples: Example texts for each unit type
                                 e.g., {'concept': ['개념 정리', '핵심 개념'],
                                       'passage': ['작품 이해하기']}
            config: Extraction configuration (optional)
        """
        self.region_text_examples = region_text_examples or {}
        self.config = config or DEFAULT_CONFIG

        if self.region_text_examples:
            total_examples = sum(len(v) for v in self.region_text_examples.values())
            logger.info(
                f"[TextBlockClassifier] Initialized with "
                f"{len(self.region_text_examples)} unit types, "
                f"{total_examples} total examples"
            )
            for label, examples in self.region_text_examples.items():
                logger.info(f"  - {label}: {len(examples)} examples")

    def calculate_similarity(
        self,
        text: str,
        example: str
    ) -> Tuple[float, str]:
        """Calculate similarity between text and example

        Uses multiple similarity methods:
        1. Exact containment (highest score)
        2. Keyword matching (medium score)
        3. Prefix matching (lower score)

        Args:
            text: Text to classify
            example: Example text for comparison

        Returns:
            Tuple of (score, method)
            - score: Similarity score (0.0-1.0)
            - method: Method used ('exact', 'keyword', 'prefix')
        """
        if not text or not example:
            return (0.0, 'empty')

        # Method 1: Exact containment
        if example in text or text in example:
            return (self.config.text_block_exact_match_score, 'exact')

        # Method 2: Keyword matching
        example_words = set(example.split())
        text_words = set(text.split())
        common_words = example_words & text_words

        if common_words:
            # Score based on overlap ratio
            score = len(common_words) / max(len(example_words), 1)
            score *= self.config.text_block_keyword_score
            return (score, 'keyword')

        # Method 3: Prefix matching
        if len(example) >= 5:
            prefix = example[:5]
            if prefix in text:
                return (self.config.text_block_prefix_score, 'prefix')

        return (0.0, 'no_match')

    def classify_text(
        self,
        text: str,
        threshold: Optional[float] = None
    ) -> TextMatchResult:
        """Classify text using region_text_examples

        Args:
            text: Text to classify
            threshold: Minimum score threshold (default from config)

        Returns:
            TextMatchResult with classification information
        """
        if not text or not self.region_text_examples:
            return TextMatchResult(matched=False, method='no_examples')

        if threshold is None:
            threshold = self.config.text_block_min_threshold

        best_match_type = None
        best_match_score = 0.0
        best_match_method = None

        # Compare with all examples
        for unit_type, examples in self.region_text_examples.items():
            for example_text in examples:
                score, method = self.calculate_similarity(text, example_text)

                if score > best_match_score:
                    best_match_score = score
                    best_match_type = unit_type
                    best_match_method = method

        # Check if best match exceeds threshold
        if best_match_type and best_match_score >= threshold:
            logger.debug(
                f"[TextBlockClassifier] Matched: '{text[:30]}...' -> "
                f"{best_match_type} (score: {best_match_score:.2f}, "
                f"method: {best_match_method})"
            )
            return TextMatchResult(
                matched=True,
                match_type=best_match_type,
                score=best_match_score,
                method=best_match_method
            )

        return TextMatchResult(
            matched=False,
            score=best_match_score,
            method='below_threshold'
        )

    def classify_text_for_section_titles(
        self,
        text: str
    ) -> TextMatchResult:
        """Classify text specifically for section titles

        Uses higher threshold for more precision.

        Args:
            text: Text to classify

        Returns:
            TextMatchResult with classification information
        """
        return self.classify_text(
            text,
            threshold=self.config.text_block_min_threshold
        )

    def classify_text_for_general_blocks(
        self,
        text: str
    ) -> TextMatchResult:
        """Classify text for general text blocks

        Uses lower threshold for higher recall.

        Args:
            text: Text to classify

        Returns:
            TextMatchResult with classification information
        """
        return self.classify_text(
            text,
            threshold=self.config.text_block_general_threshold
        )

    def get_best_match_for_multiple_texts(
        self,
        texts: List[str],
        threshold: Optional[float] = None
    ) -> List[TextMatchResult]:
        """Classify multiple texts and return results

        Args:
            texts: List of texts to classify
            threshold: Minimum score threshold (optional)

        Returns:
            List of TextMatchResult for each text
        """
        return [self.classify_text(text, threshold) for text in texts]
