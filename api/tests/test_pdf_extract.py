"""
PDF 추출 테스트 스크립트

새 아키텍처 기반 PDF 추출 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Windows 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 테스트 헬퍼 함수 import
from tests.test_helpers import (
    find_pdf_file,
    format_block_preview,
    count_block_types,
    format_file_size
)


def test_basic_pdf_extraction():
    """기본 PDF 추출 테스트 (PDFPlumber)"""
    print("=" * 60)
    print("📄 기본 PDF 추출 테스트 (PDFPlumber)")
    print("=" * 60)
    
    from app.services.pdf_extract import PDFPlumberExtractor
    
    # 헬퍼 함수 사용
    pdf_path = find_pdf_file()
    if not pdf_path:
        print(f"❌ PDF 파일을 찾을 수 없습니다")
        print("   data/pdfs/ 폴더에 PDF 파일을 넣어주세요.")
        return False
    
    print(f"\n📖 PDF 파일: {pdf_path.name}")
    print(f"📊 파일 크기: {format_file_size(pdf_path.stat().st_size)}")
    
    try:
        extractor = PDFPlumberExtractor()
        print("\n🔄 PDF 추출 중...")
        blocks = extractor.extract_blocks(pdf_path)
        
        print(f"✅ 추출 완료!")
        print(f"\n📊 추출 결과:")
        print(f"   - 총 블록 수: {len(blocks)}개")
        
        # 헬퍼 함수 사용
        block_types = count_block_types(blocks)
        print(f"   - 블록 타입별 통계:")
        for block_type, count in block_types.items():
            print(f"     • {block_type}: {count}개")
        
        # 헬퍼 함수 사용
        print(f"\n📝 처음 5개 블록 샘플:")
        for i, block in enumerate(blocks[:5], 1):
            block_type = block.get("type", "unknown")
            preview = format_block_preview(block)
            print(f"   {i}. [{block_type}] {preview}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 추출 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_literature_extraction():
    """문학 PDF 추출 테스트"""
    print("\n" + "=" * 60)
    print("📚 문학 PDF 추출 테스트")
    print("=" * 60)
    
    from app.services.pdf_extract import LiteraturePDFExtractor
    
    # 헬퍼 함수 사용 (문학 파일 우선)
    pdf_path = find_pdf_file("*문학*.pdf") or find_pdf_file()
    
    if not pdf_path:
        print(f"❌ PDF 파일을 찾을 수 없습니다")
        return False
    
    print(f"\n📖 PDF 파일: {pdf_path.name}")
    
    try:
        extractor = LiteraturePDFExtractor()
        lines = extractor.extract_blocks(pdf_path)
        
        print(f"✅ 추출 완료!")
        print(f"\n📊 추출 결과:")
        print(f"   - 총 줄 수: {len(lines)}줄")
        
        # 처음 5줄 샘플
        print(f"\n📝 처음 5줄 샘플:")
        for i, line in enumerate(lines[:5], 1):
            text = line.get("text", "")[:50]
            page = line.get("page", 0)
            print(f"   {i}. (p.{page}) {text}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 추출 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_ocr():
    """Enhanced OCR 테스트 (선택적)"""
    print("\n" + "=" * 60)
    print("🔍 Enhanced OCR 테스트 (선택적)")
    print("=" * 60)
    
    try:
        from app.services.pdf_extract.enhanced_ocr import EnhancedOCR
    except ImportError:
        print("⚠️ Enhanced OCR을 사용할 수 없습니다.")
        print("   pip install pytesseract opencv-python")
        return None
    
    # 헬퍼 함수 사용
    pdf_path = find_pdf_file()
    
    if not pdf_path:
        print(f"❌ PDF 파일을 찾을 수 없습니다")
        return None
    
    print(f"\n📖 PDF 파일: {pdf_path.name}")
    print("⚠️ OCR은 느릴 수 있습니다. 첫 페이지만 테스트합니다.")
    
    try:
        ocr = EnhancedOCR(lang='kor+eng')
        
        # PDF → 이미지 변환 (첫 페이지만)
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
        
        if not images:
            print("❌ 이미지 변환 실패")
            return False
        
        # OCR 수행
        print("🔄 OCR 처리 중...")
        result = ocr.extract_from_page_image(images[0], page_num=1)
        
        print(f"✅ OCR 완료!")
        print(f"\n📊 OCR 결과:")
        print(f"   - 추출된 블록 수: {result['total_blocks']}개")
        
        if result['text']:
            preview = result['text'][:200]
            print(f"\n📝 텍스트 샘플:")
            print(f"   {preview}...")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_text_postprocessor():
    """AI 텍스트 후처리 테스트 (선택적)"""
    print("\n" + "=" * 60)
    print("🤖 AI 텍스트 후처리 테스트 (선택적)")
    print("=" * 60)
    
    try:
        from app.services.pdf_extract.ai_text_postprocessor import get_text_postprocessor
        from app.core.config import settings
    except ImportError:
        print("⚠️ AI 텍스트 후처리기를 사용할 수 없습니다.")
        print("   pip install openai langchain")
        return None
    
    # API 키 확인
    if not settings.OPENAI_API_KEY:
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY를 설정하세요.")
        return None
    
    # 테스트 텍스트 (OCR 오류 시뮬레이션)
    test_text = """다 음 문 제를 읽고 답하시오.
1. 다음 중 0 (영)이 아닌 것은?
   ① 첫 번째 보기
   ② 두 번째 보기"""
    
    print(f"\n📝 원본 텍스트 (OCR 오류 포함):")
    print(f"   {test_text}")
    
    try:
        postprocessor = get_text_postprocessor(use_ai=True, model="gpt-4o-mini")
        
        print("\n🔄 AI 후처리 중...")
        cleaned = postprocessor.clean_extracted_text(test_text, subject="korean")
        
        print(f"✅ 후처리 완료!")
        print(f"\n📝 후처리된 텍스트:")
        print(f"   {cleaned}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI 후처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 함수"""
    print("🚀 PDF 추출 테스트 시작\n")
    
    results = {}
    
    # 1. 기본 PDF 추출
    results['basic'] = test_basic_pdf_extraction()
    
    # 2. 문학 PDF 추출
    results['literature'] = test_literature_extraction()
    
    # 3. Enhanced OCR (선택적)
    results['ocr'] = test_enhanced_ocr()
    
    # 4. AI 텍스트 후처리 (선택적)
    results['ai'] = test_ai_text_postprocessor()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is None:
            status = "⏭️  스킵 (선택적)"
        elif result:
            status = "✅ 통과"
        else:
            status = "❌ 실패"
        print(f"   {test_name:15s}: {status}")
    
    # 성공 여부 반환
    required_tests = ['basic', 'literature']
    all_passed = all(results.get(test) for test in required_tests)
    
    if all_passed:
        print("\n✅ 필수 테스트 모두 통과!")
    else:
        print("\n❌ 일부 필수 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
