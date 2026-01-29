"""
문학 교재 재파싱 스크립트 (개선된 강의 감지 패턴 적용)
"""
import sys
from pathlib import Path

# Windows 콘솔 UTF-8 인코딩 설정
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.pdf.pipeline import UnifiedPipeline
from app.core.config import settings

def reparse_literature(max_pages=None):
    """
    문학 교재 재파싱

    Args:
        max_pages: 최대 페이지 수 (None이면 전체)
    """
    print("\n" + "="*80)
    print("문학 교재 재파싱 시작")
    if max_pages:
        print(f"페이지 범위: 1~{max_pages}")
    else:
        print("페이지 범위: 전체")
    print("="*80)

    # 파이프라인 생성 (UnifiedPipeline 직접 사용)
    config_path = settings.API_DIR / "data" / "literature" / "config.json"
    
    pipeline = UnifiedPipeline(
        subject='literature',
        use_ocr=True,  # OCR 사용 (pdfplumber/PyMuPDF의 CID 문제 해결)
        use_ml_postprocess=False,  # ML 후처리 비활성화
        config_path=config_path,
        save_results=True,  # JSON 저장 활성화
        dpi=150,
        lang='kor+eng',
        tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        use_parallel=False,  # 순차 처리 (병렬 처리 오류 방지)
        max_pages=max_pages,
    )

    # PDF 경로 확인
    # 실제 PDF 파일 경로를 확인해야 함
    # data/literature/pdf 또는 다른 위치에 있을 수 있음

    # 여러 가능한 경로 확인
    possible_paths = [
        project_root.parent / "data" / "pdfs",  # 실제 PDF 위치
        project_root.parent / "data" / "literature" / "pdf",
        project_root / "data" / "literature" / "pdf",
        Path(r"C:\Users\user\Desktop\jeomgeuli-suneung-helper\data\pdfs"),
        Path(r"C:\Users\user\Desktop\jeomgeuli-suneung-helper\data\literature\pdf"),
    ]

    pdf_path = None
    for path_dir in possible_paths:
        if path_dir.exists():
            # "문학" 또는 "literature"가 포함된 PDF 찾기
            pdf_files = [f for f in path_dir.glob("*.pdf") if "문학" in f.name or "literature" in f.name.lower()]
            if pdf_files:
                pdf_path = pdf_files[0]
                break

    if not pdf_path or not pdf_path.exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다.")
        print("가능한 위치:")
        for path in possible_paths:
            print(f"  - {path}")
        return

    print(f"\n📄 PDF 파일: {pdf_path.name}")
    print(f"📁 출력 디렉토리: {project_root / 'data' / 'literature'}")

    # 출력 디렉토리
    output_dir = project_root / "data" / "literature"
    lectures_dir = output_dir / "lectures"
    problems_dir = output_dir / "problems"
    test_output_dir = output_dir / "test_output"

    # 파싱 실행
    print("\n🔄 파싱 실행 중...")
    try:
        result = pipeline.process(pdf_path)

        print(f"\n✅ 파싱 완료!")
        lectures = result.get('lectures', [])
        problems = result.get('problems', [])
        lecture_contents = result.get('lecture_contents', [])
        print(f"  • 생성된 강의: {len(lectures)}개")
        print(f"  • 생성된 문제: {len(problems)}개")
        print(f"  • 강의 콘텐츠: {len(lecture_contents)}개")

        # 강의 목록 출력
        if lectures:
            print(f"\n📚 감지된 강의 수: {len(lectures)}")
            for lec in lectures[:20]:  # 처음 20개만 표시
                print(f"  • 강의 {lec.get('lecture_id')}: {lec.get('title', 'No title')[:60]} "
                      f"(페이지 {lec.get('page', '?')})")

            if len(lectures) > 20:
                print(f"  ... 그 외 {len(lectures) - 20}개 강의")

        # 강의 JSON 파일 확인
        if lectures_dir.exists():
            lecture_files = sorted(lectures_dir.glob("lecture_*.json"))
            print(f"\n📂 생성된 강의 파일 수: {len(lecture_files)}")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*80)
    print("재파싱 완료")
    print("="*80)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='문학 교재 재파싱')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='최대 페이지 수 (테스트용, 기본값: 전체)')
    args = parser.parse_args()

    reparse_literature(max_pages=args.max_pages)
