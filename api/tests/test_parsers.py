"""
과목별 파서 테스트 스크립트 (통합)

수학Ⅰ, 문학, 영어 파서를 하나의 파일에서 테스트
"""
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Windows 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from tests.test_helpers import find_pdf_file, format_file_size
from app.services.subject_strategies.math1 import Math1Parser
from app.services.subject_strategies.literature import LiteratureParser
from app.services.subject_strategies.english import EnglishParser
from app.services.pdf_extract import PDFPlumberExtractor, LiteraturePDFExtractor


def test_math1_parser(pdf_path: Optional[Path] = None):
    """수학Ⅰ 파서 테스트"""
    print("=" * 60)
    print("🔢 수학Ⅰ 파서 테스트")
    print("=" * 60)
    
    if not pdf_path:
        pdf_path = find_pdf_file("*수학*.pdf") or find_pdf_file()
    
    if not pdf_path or not pdf_path.exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다")
        return False
    
    print(f"\n📖 PDF 파일: {pdf_path.name}")
    print(f"📊 파일 크기: {format_file_size(pdf_path.stat().st_size)}")
    
    try:
        # Step 1: 추출
        print("\n[1단계] PDF에서 블록 추출 중...")
        extractor = PDFPlumberExtractor()
        blocks = extractor.extract_blocks(pdf_path)
        print(f"✅ 추출 완료: {len(blocks)}개 블록")
        
        # Step 2: 파싱
        print("\n[2단계] 수학Ⅰ 파싱 중...")
        parser = Math1Parser()
        result = parser.parse(blocks, metadata={"book_id": "test_math1"})
        
        print(f"✅ 파싱 완료!")
        print(f"\n📊 파싱 결과:")
        print(f"   - 과목: {result.get('subject', 'unknown')}")
        print(f"   - 단위 수: {len(result.get('units', []))}")
        
        # 통계 정보
        stats = result.get('statistics', {})
        if stats:
            print(f"   - 통계:")
            for key, value in stats.items():
                print(f"     • {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_literature_parser(pdf_path: Optional[Path] = None):
    """문학 파서 테스트"""
    print("\n" + "=" * 60)
    print("📚 문학 파서 테스트")
    print("=" * 60)
    
    if not pdf_path:
        pdf_path = find_pdf_file("*문학*.pdf") or find_pdf_file()
    
    if not pdf_path or not pdf_path.exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다")
        return False
    
    print(f"\n📖 PDF 파일: {pdf_path.name}")
    print(f"📊 파일 크기: {format_file_size(pdf_path.stat().st_size)}")
    
    try:
        # Step 1: 추출 (줄 단위)
        print("\n[1단계] PDF에서 줄 단위로 추출 중...")
        extractor = LiteraturePDFExtractor()
        lines = extractor.extract_blocks(pdf_path)
        print(f"✅ 추출 완료: {len(lines)}줄")
        
        # Step 2: 파싱
        print("\n[2단계] 문학 파싱 중...")
        parser = LiteratureParser()
        result = parser.parse(lines, metadata={"book_id": "test_literature"})
        
        print(f"✅ 파싱 완료!")
        print(f"\n📊 파싱 결과:")
        print(f"   - 과목: {result.get('subject', 'unknown')}")
        print(f"   - 지문 수: {len(result.get('passages', []))}")
        print(f"   - 문제 수: {len(result.get('questions', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_english_parser(pdf_path: Optional[Path] = None):
    """영어 파서 테스트"""
    print("\n" + "=" * 60)
    print("🌐 영어 파서 테스트")
    print("=" * 60)
    
    if not pdf_path:
        pdf_path = find_pdf_file("*영어*.pdf") or find_pdf_file()
    
    if not pdf_path or not pdf_path.exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다")
        return False
    
    print(f"\n📖 PDF 파일: {pdf_path.name}")
    print(f"📊 파일 크기: {format_file_size(pdf_path.stat().st_size)}")
    
    try:
        # Step 1: 추출 (줄 단위)
        print("\n[1단계] PDF에서 줄 단위로 추출 중...")
        extractor = LiteraturePDFExtractor()
        lines = extractor.extract_blocks(pdf_path)
        print(f"✅ 추출 완료: {len(lines)}줄")
        
        # Step 2: 파싱
        print("\n[2단계] 영어 파싱 중...")
        print("  (디버그: 처음 50개 블록 분류 결과)")
        parser = EnglishParser()
        result = parser.parse(lines, metadata={"book_id": "test_english", "debug": True})
        
        print(f"✅ 파싱 완료!")
        print(f"\n📊 파싱 결과:")
        print(f"   - 과목: {result.get('subject', 'unknown')}")
        
        # units에서 지문과 문제 개수 계산
        units = result.get('units', [])
        passages = [u for u in units if u.get('type') == 'passage']
        questions = [u for u in units if u.get('type') == 'question']
        
        stats = result.get('statistics', {})
        print(f"   - 지문 수: {len(passages)} (statistics: {stats.get('passages', 0)})")
        print(f"   - 문제 수: {len(questions)} (statistics: {stats.get('questions', 0)})")
        print(f"   - 총 단위 수: {stats.get('total_units', len(units))}")
        
        # 문제 유형별 통계
        questions = result.get('questions', [])
        if questions:
            question_types = {}
            for q in questions:
                q_type = q.get('type', 'unknown')
                question_types[q_type] = question_types.get(q_type, 0) + 1
            
            print(f"   - 문제 유형별 통계:")
            for q_type, count in question_types.items():
                print(f"     • {q_type}: {count}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="과목별 파서 테스트")
    parser.add_argument(
        "--subject",
        choices=["math1", "literature", "english", "all"],
        default="all",
        help="테스트할 과목 선택 (기본값: all)"
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        help="테스트할 PDF 파일 경로"
    )
    
    args = parser.parse_args()
    
    print("🚀 파서 테스트 시작\n")
    
    results = {}
    
    if args.subject in ["math1", "all"]:
        results['math1'] = test_math1_parser(args.pdf)
    
    if args.subject in ["literature", "all"]:
        results['literature'] = test_literature_parser(args.pdf)
    
    if args.subject in ["english", "all"]:
        results['english'] = test_english_parser(args.pdf)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    for subject, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"   {subject:15s}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 일부 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
