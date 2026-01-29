"""
빠른 테스트 스크립트
실제 데이터로 섹션 추출기 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.infrastructure.pdf.parsers.section_extractor import ImprovedSectionExtractor
from app.infrastructure.pdf.parsers.text_preprocessor import TextPreprocessor


def test_text_preprocessor():
    """텍스트 전처리기 테스트"""
    print("=" * 60)
    print("텍스트 전처리기 테스트")
    print("=" * 60)
    
    # 테스트 케이스
    test_cases = [
        "1. 시적 표현",
        "1. 시적 표현 (cid:123)",
        "작품으로 이해하기",
        "   여러   공백   ",
        "０１２３",  # 전각 숫자
    ]
    
    for text in test_cases:
        normalized = TextPreprocessor.normalize_text(text)
        quality = TextPreprocessor.calculate_quality_score(normalized)
        print(f"원본: {text!r}")
        print(f"정규화: {normalized!r}")
        print(f"품질 점수: {quality:.2f}")
        print()


def test_section_extractor():
    """섹션 추출기 테스트"""
    print("=" * 60)
    print("섹션 추출기 테스트")
    print("=" * 60)
    
    config = {
        'concept_title_patterns': [r'^(\d+)\s*[\.]\s*([가-힣\s]{2,20})$'],
        'content_header_patterns': [r'작품으로 이해하기'],
        'start_content_page': 8
    }
    
    extractor = ImprovedSectionExtractor(config=config)
    
    # 테스트 OCR 데이터
    ocr_data = [
        {
            'page_num': 8,
            'text': ['1.', '시적', '표현'],
            'top': [100, 100, 100],
            'left': [50, 80, 120],
            'width': [20, 30, 40],
            'height': [15, 15, 15]
        },
        {
            'page_num': 9,
            'text': ['2.', '시의', '형식'],
            'top': [100, 100, 100],
            'left': [50, 80, 120],
            'width': [20, 30, 40],
            'height': [15, 15, 15]
        },
        {
            'page_num': 10,
            'text': ['작품으로', '이해하기'],
            'top': [100, 100],
            'left': [50, 150],
            'width': [50, 50],
            'height': [15, 15]
        }
    ]
    
    result = extractor.extract(ocr_data)
    
    print(f"추출 방법: {result.method}")
    print(f"신뢰도: {result.confidence:.2f}")
    print(f"섹션 수: {len(result.sections)}")
    print()
    
    if result.sections:
        print("추출된 섹션:")
        for i, section in enumerate(result.sections, 1):
            print(f"  {i}. {section.get('title')} ({section.get('type')})")
            print(f"     페이지: {section.get('page')}")
    else:
        print("[ERROR] 섹션이 추출되지 않았습니다.")
    
    print()
    print(f"메타데이터: {result.metadata}")


def test_merge_sections():
    """섹션 병합 테스트"""
    print("=" * 60)
    print("섹션 병합 테스트")
    print("=" * 60)
    
    config = {'start_content_page': 8}
    extractor = ImprovedSectionExtractor(config=config)
    
    sections1 = [
        {'title': '1. 시적 표현', 'type': 'concept', 'page': 8, 'bbox': [0, 0, 100, 20]}
    ]
    
    sections2 = [
        {'title': '2. 시의 형식', 'type': 'concept', 'page': 8, 'bbox': [0, 30, 100, 50]},
        {'title': '1. 시적 표현', 'type': 'concept', 'page': 8, 'bbox': [0, 0, 100, 20]}  # 중복
    ]
    
    merged = extractor._merge_sections(sections1, sections2)
    
    print(f"섹션 1: {len(sections1)}개")
    print(f"섹션 2: {len(sections2)}개")
    print(f"병합 결과: {len(merged)}개 (중복 제거됨)")
    print()
    
    for section in merged:
        print(f"  - {section.get('title')}")


if __name__ == "__main__":
    try:
        test_text_preprocessor()
        print()
        test_section_extractor()
        print()
        test_merge_sections()
        print()
        print("=" * 60)
        print("[OK] 모든 테스트 완료!")
        print("=" * 60)
    except Exception as e:
        print(f"[ERROR] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
