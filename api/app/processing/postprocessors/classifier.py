"""
블록 분류기 (래핑 버전)
기존 ml/block_classifier.py를 래핑
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class BlockClassifier:
    """
    블록 타입 분류기
    기존 HybridBlockClassifier 래핑
    """

    def __init__(self):
        """분류기 초기화"""
        try:
            from app.ml.block_classifier import HybridBlockClassifier
            self.classifier = HybridBlockClassifier()
            self.available = True
            logger.info("BlockClassifier 초기화 완료")
        except Exception as e:
            logger.warning(f"BlockClassifier 초기화 실패: {e}")
            self.classifier = None
            self.available = False

    def classify(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        블록 리스트 분류

        Args:
            blocks: 블록 리스트

        Returns:
            분류 결과가 추가된 블록 리스트
        """
        if not self.available or not self.classifier:
            logger.warning("분류기를 사용할 수 없습니다. 원본 반환")
            return blocks

        try:
            return self.classifier.classify_blocks(blocks)
        except Exception as e:
            logger.error(f"블록 분류 실패: {e}")
            return blocks
