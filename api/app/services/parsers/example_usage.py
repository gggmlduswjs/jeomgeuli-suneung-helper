"""
파서 사용 예제

3단계 파이프라인:
1. PDF → Intermediate Structure (DocumentParser)
2. Intermediate Structure 검증/시각화 (수동 또는 자동)
3. Intermediate Structure → 강의 JSON (JSONAssembler)
"""
import sys
from pathlib import Path
import logging

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.parsers import DocumentParser, JSONAssembler
from app.services.text_extractors import PdfplumberExtractor, OCRExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_pdfplumber():
    """
    pdfplumber를 사용한 파싱 예제
    (텍스트 레이어가 있는 PDF에 권장)
    """
    print("=" * 60)
    print("예제 1: pdfplumber를 사용한 파싱")
    print("=" * 60)

    # 1. 텍스트 추출기 초기화
    extractor = PdfplumberExtractor()

    # 2. PDF 경로
    pdf_path = Path("data/literature/pdf/수능특강_문학.pdf")

    if not pdf_path.exists():
        print(f"⚠️ PDF 파일이 없습니다: {pdf_path}")
        print(f"   실제 PDF 경로를 지정하세요.")
        return

    # 3. OCR 데이터 추출
    print(f"\n[단계 1] PDF 텍스트 추출 중...")
    all_ocr_data = extractor.extract(pdf_path)
    print(f"   ✓ {len(all_ocr_data)}개 페이지 추출 완료")

    # 4. 문서 파서 초기화
    print(f"\n[단계 2] 문서 파싱 중...")
    doc_parser = DocumentParser(subject="literature")

    # 5. 중간 구조 생성
    intermediate_doc = doc_parser.parse(
        all_ocr_data=all_ocr_data,
        pdf_path=str(pdf_path),
        ocr_method="pdfplumber"
    )

    print(f"   ✓ 파싱 완료:")
    print(f"     - 페이지: {intermediate_doc.metadata.total_pages}개")
    print(f"     - 블록: {intermediate_doc.metadata.total_blocks}개")
    print(f"     - 강의: {len(intermediate_doc.lectures)}개")

    # 6. 중간 구조 저장 (검증용)
    intermediate_path = Path("data/literature/intermediate_doc.json")
    print(f"\n[단계 3] 중간 구조 저장 중...")
    doc_parser.save_intermediate(intermediate_doc, intermediate_path)
    print(f"   ✓ 저장 완료: {intermediate_path}")

    # 7. 최종 JSON 생성
    print(f"\n[단계 4] 최종 JSON 생성 중...")
    assembler = JSONAssembler()

    lectures_dir = Path("data/literature/lectures")
    problems_dir = Path("data/literature/problems")

    assembler.save_all(
        doc=intermediate_doc,
        lectures_dir=lectures_dir,
        problems_dir=problems_dir
    )
    print(f"   ✓ 강의 JSON: {lectures_dir}/")
    print(f"   ✓ 문제 JSON: {problems_dir}/")

    print("\n" + "=" * 60)
    print("✅ 완료!")
    print("=" * 60)

    # 8. 결과 샘플 출력
    if intermediate_doc.pages:
        first_page = intermediate_doc.pages[0]
        print(f"\n[샘플] 첫 페이지 블록:")
        for block in first_page.blocks[:3]:  # 처음 3개만
            print(f"  - [{block.block_type.value}] {block.block_id}")
            print(f"    제목: {block.metadata.title or '(없음)'}")
            print(f"    신뢰도: {block.metadata.confidence:.2f}")
            print(f"    줄 수: {len(block.raw_lines)}")
            print()


def example_ocr():
    """
    Tesseract OCR을 사용한 파싱 예제
    (텍스트 레이어가 없는 스캔 PDF용)
    """
    print("=" * 60)
    print("예제 2: Tesseract OCR을 사용한 파싱")
    print("=" * 60)

    # 1. OCR 추출기 초기화
    try:
        extractor = OCRExtractor(
            dpi=180,
            lang='kor+eng'
        )
    except Exception as e:
        print(f"⚠️ Tesseract가 설치되지 않았습니다: {e}")
        print(f"   pdfplumber 예제를 사용하세요.")
        return

    # 2. PDF 경로
    pdf_path = Path("data/literature/pdf/수능특강_문학.pdf")

    if not pdf_path.exists():
        print(f"⚠️ PDF 파일이 없습니다: {pdf_path}")
        return

    # 3. OCR 실행 (시간이 오래 걸림)
    print(f"\n[단계 1] OCR 수행 중... (시간이 걸릴 수 있습니다)")
    all_ocr_data = extractor.extract(pdf_path)
    print(f"   ✓ {len(all_ocr_data)}개 페이지 OCR 완료")

    # 4. 이후 단계는 pdfplumber와 동일
    doc_parser = DocumentParser(subject="literature")
    intermediate_doc = doc_parser.parse(
        all_ocr_data=all_ocr_data,
        pdf_path=str(pdf_path),
        ocr_method="tesseract"
    )

    # ... (나머지는 example_pdfplumber와 동일)


def example_load_and_assemble():
    """
    저장된 중간 구조를 로드하여 재조립하는 예제
    """
    print("=" * 60)
    print("예제 3: 중간 구조 로드 및 재조립")
    print("=" * 60)

    # 1. 중간 구조 로드
    intermediate_path = Path("data/literature/intermediate_doc.json")

    if not intermediate_path.exists():
        print(f"⚠️ 중간 구조 파일이 없습니다: {intermediate_path}")
        print(f"   먼저 예제 1을 실행하세요.")
        return

    print(f"\n[단계 1] 중간 구조 로드 중...")
    doc_parser = DocumentParser(subject="literature")
    intermediate_doc = doc_parser.load_intermediate(intermediate_path)
    print(f"   ✓ 로드 완료")

    # 2. 특정 강의만 JSON 생성
    print(f"\n[단계 2] 특정 강의 JSON 생성...")
    assembler = JSONAssembler()

    if intermediate_doc.lectures:
        lecture_id = 1
        lecture_json = assembler.assemble_lecture_json(intermediate_doc, lecture_id)

        print(f"   강의 {lecture_id}:")
        print(f"     - 제목: {lecture_json.get('title', '')}")
        print(f"     - 섹션: {len(lecture_json.get('sections', []))}개")
        print(f"     - 문제: {len(lecture_json.get('problems', []))}개")

        # 첫 섹션 샘플
        if lecture_json.get('sections'):
            first_section = lecture_json['sections'][0]
            print(f"\n   첫 섹션 샘플:")
            print(f"     제목: {first_section.get('title', '')}")
            print(f"     페이지: {first_section.get('page', '')}")
            print(f"     내용: {len(first_section.get('content', []))}줄")
            if first_section.get('content'):
                print(f"     첫 줄: {first_section['content'][0][:60]}...")


if __name__ == "__main__":
    print("\n수능특강 문학 파서 사용 예제\n")

    # 예제 1 실행 (pdfplumber)
    try:
        example_pdfplumber()
    except Exception as e:
        logger.error(f"예제 1 실패: {e}", exc_info=True)

    print("\n\n")

    # 예제 3 실행 (재조립)
    try:
        example_load_and_assemble()
    except Exception as e:
        logger.error(f"예제 3 실패: {e}", exc_info=True)
