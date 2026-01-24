"""
중복 제거기 (래핑 버전)
기존 ml/deduplicator.py를 래핑
"""
import logging
from typing import List, Optional

from app.infrastructure.pdf.types import BlockData

logger = logging.getLogger(__name__)


class Deduplicator:
    """
    콘텐츠 중복 제거기
    기존 ContentDeduplicator 래핑
    """

    def __init__(self, threshold: float = 0.85):
        """
        Args:
            threshold: 유사도 임계값
        """
        try:
            from app.infrastructure.ai.ml.deduplicator import ContentDeduplicator
            self.deduplicator = ContentDeduplicator(similarity_threshold=threshold)
            self.available = True
            logger.info("Deduplicator 초기화 완료")
        except Exception as e:
            logger.warning(f"Deduplicator 초기화 실패: {e}")
            self.deduplicator: Optional[object] = None
            self.available = False

    def deduplicate(self, items: List[BlockData]) -> List[BlockData]:
        """
        항목 중복 제거

        Args:
            items: 항목 리스트

        Returns:
            중복 제거된 항목 리스트
        """
        if not self.available or not self.deduplicator:
            logger.warning("중복 제거기를 사용할 수 없습니다. 원본 반환")
            return items

        try:
            return self.deduplicator.deduplicate(items)
        except Exception as e:
            logger.error(f"중복 제거 실패: {e}")
            return items
