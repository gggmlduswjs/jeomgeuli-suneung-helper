"""
ML Features 테스트 스크립트

Level 1 ML 기능 테스트:
- Content Deduplication
- Hybrid Block Classifier

사용법:
    python scripts/examples/test_ml_features.py
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.ml import (
    ContentDeduplicator,
    HybridBlockClassifier,
    MLPostProcessor,
    DuplicationStrategy
)


def test_content_deduplication():
    """중복 제거 테스트"""
    print("\n" + "="*60)
    print("Test 1: Content Deduplication")
    print("="*60)

    # 테스트 데이터
    blocks = [
        {
            "text": "형상화는 시의 주제나 정서를 구체적 이미지로 표현하는 기법이다.",
            "title": "개념 설명 1"
        },
        {
            "text": "형상화는 시의 주제나 정서를 구체적 이미지로 표현하는 기법이다.",
            "title": "개념 설명 2"  # 중복!
        },
        {
            "text": "비유는 사물이나 개념을 다른 것에 빗대어 표현하는 방법이다.",
            "title": "개념 설명 3"
        },
        {
            "text": "상징은 구체적인 사물로 추상적인 개념을 나타내는 표현 기법이다.",
            "title": "개념 설명 4"
        },
        {
            "text": "상징은 구체적인 사물로 추상적인 개념을 나타내는 표현 기법입니다.",
            "title": "개념 설명 5"  # 거의 중복!
        }
    ]

    print(f"\n원본 블록 수: {len(blocks)}")

    # Deduplicator 생성
    deduplicator = ContentDeduplicator(
        similarity_threshold=0.95,
        strategy=DuplicationStrategy.MARK_ONLY,
        use_semantic=True,
        use_tfidf=True
    )

    # 중복 제거 실행
    result_blocks, result = deduplicator.deduplicate_blocks(blocks)

    # 결과 출력
    print(f"\n중복 탐지 결과:")
    print(f"  - 원본: {result.original_count}개")
    print(f"  - 중복: {result.duplicate_count}개")
    print(f"  - 유일: {result.unique_count}개")
    print(f"  - 처리 시간: {result.processing_time_ms:.2f}ms")

    print(f"\n중복 쌍:")
    for idx1, idx2, similarity in result.duplicate_pairs[:3]:
        print(f"  - 블록 {idx1} ↔ 블록 {idx2}: {similarity:.3f}")

    print(f"\n중복 그룹:")
    for i, group in enumerate(result.duplicate_groups):
        print(f"  - 그룹 {i}: {group}")

    # 마킹된 블록 확인
    print(f"\n마킹된 중복 블록:")
    for i, block in enumerate(result_blocks):
        if block.get("metadata", {}).get("is_duplicate"):
            print(f"  - 블록 {i}: \"{block['text'][:50]}...\"")


def test_hybrid_block_classifier():
    """하이브리드 블록 분류 테스트"""
    print("\n" + "="*60)
    print("Test 2: Hybrid Block Classifier")
    print("="*60)

    # 테스트 데이터
    blocks = [
        {
            "title": "개념 설명",
            "text": "형상화는 시의 주제나 정서를 구체적 이미지로 표현하는 기법이다."
        },
        {
            "title": "",
            "text": "다음 중 밑줄 친 부분의 의미를 바르게 해석한 것은?"
        },
        {
            "title": "작품",
            "text": "해 - 박두진\n\n햇빛 찬란히 내리어\n풀잎마다 구슬 맺고"
        },
        {
            "title": "예시",
            "text": "예를 들어 다음과 같은 표현이 있습니다."
        },
        {
            "title": "",
            "text": "이 단원에서는 문학 작품의 표현 기법을 학습합니다."
        }
    ]

    # Classifier 생성
    classifier = HybridBlockClassifier(
        rule_confidence_threshold=0.8,
        ml_confidence_threshold=0.6,
        use_ml=True
    )

    print(f"\n블록 분류 결과:")
    print("-" * 60)

    for i, block in enumerate(blocks):
        result = classifier.classify_block(block)

        print(f"\n블록 {i}:")
        print(f"  Title: \"{block['title']}\"")
        print(f"  Text: \"{block['text'][:50]}...\"")
        print(f"  ➜ Type: {result.block_type}")
        print(f"  ➜ Confidence: {result.confidence:.3f}")
        print(f"  ➜ Method: {result.method}")

        if result.rule_prediction:
            print(f"  ➜ Rule: {result.rule_prediction} ({result.rule_confidence:.3f})")
        if result.ml_prediction:
            print(f"  ➜ ML: {result.ml_prediction} ({result.ml_confidence:.3f})")


def test_ml_post_processor():
    """MLPostProcessor 통합 테스트"""
    print("\n" + "="*60)
    print("Test 3: ML Post-Processor (통합)")
    print("="*60)

    # 테스트 강의 데이터
    lecture_data = {
        "lectures": [
            {
                "title": "개념 설명 1",
                "content": "형상화는 시의 주제를 구체적 이미지로 표현하는 기법이다.",
                "type": "concept"
            },
            {
                "title": "개념 설명 2",
                "content": "형상화는 시의 주제를 구체적 이미지로 표현하는 기법이다.",
                "type": "concept"  # 중복!
            },
            {
                "title": "작품",
                "content": "해 - 박두진\n햇빛 찬란히 내리어",
                "type": "passage"
            }
        ],
        "problems": [
            {
                "question_text": "다음 중 밑줄 친 부분의 의미를 바르게 해석한 것은?",
                "type": "question"
            },
            {
                "question_text": "다음 중 밑줄 친 부분의 의미를 바르게 해석한 것은?",
                "type": "question"  # 중복!
            }
        ]
    }

    # MLPostProcessor 생성
    processor = MLPostProcessor(
        enable_deduplication=True,
        enable_classification=True,
        deduplication_threshold=0.95,
        deduplication_strategy="mark_only"
    )

    # 처리 실행
    print("\n강의 데이터 처리 중...")
    enriched_data, stats = processor.process(lecture_data)

    # 통계 출력
    print("\n" + "-"*60)
    print("처리 결과:")
    print("-"*60)

    print(f"\n중복 제거 통계:")
    if "lectures" in stats["deduplication"]:
        lec_stats = stats["deduplication"]["lectures"]
        print(f"  Lectures:")
        print(f"    - 원본: {lec_stats['original_count']}개")
        print(f"    - 중복: {lec_stats['duplicate_count']}개")
        print(f"    - 유일: {lec_stats['unique_count']}개")

    if "problems" in stats["deduplication"]:
        prob_stats = stats["deduplication"]["problems"]
        print(f"  Problems:")
        print(f"    - 원본: {prob_stats['original_count']}개")
        print(f"    - 중복: {prob_stats['duplicate_count']}개")
        print(f"    - 유일: {prob_stats['unique_count']}개")

    print(f"\n분류 통계:")
    if "classification_methods" in stats["classification"]:
        methods = stats["classification"]["classification_methods"]
        print(f"  Methods: {methods}")

    print(f"\n총 처리 시간: {stats['total_processing_time_ms']:.2f}ms")


def main():
    """메인 함수"""
    print("\n" + "🚀"*30)
    print("ML Features 테스트 시작")
    print("🚀"*30)

    try:
        # Test 1: Content Deduplication
        test_content_deduplication()

        # Test 2: Hybrid Block Classifier
        test_hybrid_block_classifier()

        # Test 3: ML Post-Processor
        test_ml_post_processor()

        print("\n" + "✅"*30)
        print("모든 테스트 완료!")
        print("✅"*30 + "\n")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
