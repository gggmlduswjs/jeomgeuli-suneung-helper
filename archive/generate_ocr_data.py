# -*- coding: utf-8 -*-
"""
교재의 OCR 데이터와 원본 PDF 생성 스크립트
기존 파싱 데이터는 유지하면서 OCR 데이터만 추가 생성
"""
import sys
import json
import shutil
from pathlib import Path

# UTF-8 출력을 위한 설정
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.infrastructure.pdf.extractors import PdfplumberExtractor


def generate_ocr_data(
    pdf_path: Path,
    subject: str,
    book_id: str
):
    """
    PDF에서 OCR 데이터를 추출하고 페이지별 JSON 파일로 저장

    Args:
        pdf_path: PDF 파일 경로
        subject: 과목명 (예: 'literature')
        book_id: 교재 ID
    """
    print(f"\n{'='*60}")
    print(f"OCR 데이터 생성 시작")
    print(f"PDF: {pdf_path}")
    print(f"과목: {subject}")
    print(f"교재 ID: {book_id}")
    print(f"{'='*60}\n")

    # 1. 교재 디렉토리 확인
    book_dir = settings.DATA_DIR / subject / book_id
    if not book_dir.exists():
        raise FileNotFoundError(f"교재 디렉토리를 찾을 수 없습니다: {book_dir}")

    # 2. OCR 데이터 디렉토리 생성
    ocr_data_dir = book_dir / "ocr_data"
    ocr_data_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] OCR 데이터 디렉토리: {ocr_data_dir}")

    # 3. 텍스트 추출기 생성 (pdfplumber 사용)
    print("\n[1/3] 텍스트 추출기 초기화 중...")
    extractor = PdfplumberExtractor()
    print("[OK] pdfplumber 추출기 생성 완료")

    # 4. OCR 데이터 추출
    print(f"\n[2/3] PDF에서 텍스트 추출 중: {pdf_path}")
    ocr_data = extractor.extract(pdf_path)
    print(f"[OK] 추출 완료: {len(ocr_data)}개 페이지")

    # 5. 페이지별 JSON 파일로 저장
    print(f"\n[3/3] OCR 데이터를 JSON 파일로 저장 중...")
    saved_count = 0
    for page_data in ocr_data:
        page_num = page_data.get('page_num', 0)
        if page_num <= 0:
            print(f"  [WARN] 유효하지 않은 페이지 번호: {page_num}, 건너뜁니다.")
            continue

        # 파일명: page_001.json, page_002.json, ...
        ocr_file = ocr_data_dir / f"page_{page_num:03d}.json"

        with open(ocr_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, ensure_ascii=False, indent=2)

        saved_count += 1
        if saved_count % 10 == 0:
            print(f"  진행 중: {saved_count}/{len(ocr_data)} 페이지")

    print(f"[OK] OCR 데이터 저장 완료: {saved_count}개 페이지")

    # 6. 원본 PDF 복사
    print(f"\n원본 PDF 복사 중...")
    dest_pdf = book_dir / "original.pdf"
    shutil.copy2(pdf_path, dest_pdf)
    print(f"[OK] PDF 복사 완료: {dest_pdf}")

    print(f"\n{'='*60}")
    print(f"[SUCCESS] 모든 작업 완료!")
    print(f"{'='*60}")
    print(f"OCR 데이터: {ocr_data_dir}")
    print(f"원본 PDF: {dest_pdf}")


if __name__ == "__main__":
    # 명령줄 인자로 book_id를 받을 수 있도록 수정
    if len(sys.argv) > 1:
        book_id = sys.argv[1]
    else:
        # 기본값: 새 교재
        book_id = "book_korean_2026_수능특강_문학_e4d0c8"

    # PDF 경로와 과목 설정
    pdf_path = Path("data/pdfs/2026 수능특강_ 문학.pdf")
    subject = "literature"

    if not pdf_path.exists():
        print(f"[ERROR] PDF 파일을 찾을 수 없습니다: {pdf_path}")
        print("PDF 경로를 확인하고 다시 시도하세요.")
        sys.exit(1)

    try:
        generate_ocr_data(pdf_path, subject, book_id)
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
