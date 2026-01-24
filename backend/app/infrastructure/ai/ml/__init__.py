"""
ML Post-Processing Module

Level 1 ML 기능 (ML 기초 탄탄함 증명):
- Content Deduplication: TF-IDF + Semantic Similarity로 중복 제거
- Hybrid Block Classifier: 규칙 + ML 하이브리드 블록 분류

사용 예시:
    from app.ml import MLPostProcessor

    processor = MLPostProcessor(
        enable_deduplication=True,
        enable_classification=True
    )

    # 강의 데이터 처리
    enriched_data, stats = processor.process(lecture_data)
    print(f"중복 제거: {stats['deduplication']['lectures']['duplicate_count']}개")
    print(f"ML 분류: {stats['classification']['classification_methods']}")
"""
from app.ml.deduplicator import (
    ContentDeduplicator,
    DuplicationStrategy,
    deduplicate_lecture_content
)
from app.ml.block_classifier import (
    HybridBlockClassifier,
    BlockType,
    classify_and_enrich_lecture_content
)


__all__ = [
    "ContentDeduplicator",
    "DuplicationStrategy",
    "HybridBlockClassifier",
    "BlockType",
    "MLPostProcessor",
    "deduplicate_lecture_content",
    "classify_and_enrich_lecture_content"
]


class MLPostProcessor:
    """
    ML Post-Processing Pipeline

    Assembly 단계 이후에 실행되어 데이터를 enrichment합니다.
    - 중복 제거
    - ML 기반 블록 분류
    - 메타데이터 추가

    사용 예시:
        processor = MLPostProcessor()
        enriched_data, stats = processor.process(lecture_data)
    """

    def __init__(
        self,
        enable_deduplication: bool = True,
        enable_classification: bool = True,
        deduplication_threshold: float = 0.95,
        deduplication_strategy: str = "mark_only",
        classification_threshold: float = 0.8,
        update_block_type: bool = False
    ):
        """
        Args:
            enable_deduplication: 중복 제거 활성화
            enable_classification: ML 분류 활성화
            deduplication_threshold: 중복 판정 유사도 임계값
            deduplication_strategy: 중복 처리 전략
            classification_threshold: 규칙 확신도 임계값
            update_block_type: block_type 필드 업데이트 여부
        """
        self.enable_deduplication = enable_deduplication
        self.enable_classification = enable_classification
        self.deduplication_threshold = deduplication_threshold
        self.deduplication_strategy = deduplication_strategy
        self.classification_threshold = classification_threshold
        self.update_block_type = update_block_type

    def process(self, lecture_data: dict) -> tuple[dict, dict]:
        """
        강의 데이터 처리

        Args:
            lecture_data: 강의 데이터 (lectures, problems 포함)

        Returns:
            (enriched 강의 데이터, 통계 정보)
        """
        import time
        start_time = time.time()

        stats = {
            "deduplication": {},
            "classification": {},
            "total_processing_time_ms": 0.0
        }

        # Step 1: 중복 제거
        if self.enable_deduplication:
            lecture_data, dedup_stats = deduplicate_lecture_content(
                lecture_data,
                similarity_threshold=self.deduplication_threshold,
                strategy=self.deduplication_strategy
            )
            stats["deduplication"] = dedup_stats

        # Step 2: ML 기반 블록 분류
        if self.enable_classification:
            lecture_data, class_stats = classify_and_enrich_lecture_content(
                lecture_data,
                rule_confidence_threshold=self.classification_threshold,
                update_type=self.update_block_type
            )
            stats["classification"] = class_stats

        # 총 처리 시간
        stats["total_processing_time_ms"] = (time.time() - start_time) * 1000

        return lecture_data, stats
