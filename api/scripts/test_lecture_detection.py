"""
강의 감지 패턴 테스트 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.textbook_pipeline import TextbookPipeline

def test_lecture_detection():
    """특정 페이지들에서 강의 감지 테스트"""

    # 테스트할 페이지 범위 (4-9강이 있는 페이지들 + 2부 작품들)
    test_pages = [
        (8, 15),    # 1-3강
        (19, 25),   # 4-5강
        (29, 37),   # 6-7강
        (41, 45),   # 9강 + 2부 시작
        (50, 55),   # 2부 작품들
        (70, 80),   # 2부 작품들
    ]

    print("\n" + "="*80)
    print("문학 교재 강의 감지 테스트")
    print("="*80)

    for start_page, end_page in test_pages:
        print(f"\n📄 페이지 {start_page}~{end_page} 테스트 중...")

        try:
            # 파이프라인 생성
            pipeline = TextbookPipeline(
                subject='literature',
                dpi=150,
                use_parallel=False,
                use_ai_postprocess=False,
                use_cache=True,
                use_pdfplumber=True,
                max_pages=end_page,  # end_page까지만 처리
            )

            # 페이지 이미지 경로
            pages_dir = project_root / "data" / "literature" / "pages"

            if not pages_dir.exists():
                print(f"❌ 페이지 디렉토리를 찾을 수 없음: {pages_dir}")
                continue

            # OCR 데이터 로드 (캐시 사용)
            all_ocr_data = []
            for page_num in range(start_page, end_page + 1):
                page_img = pages_dir / f"page_{page_num:03d}.png"
                if page_img.exists():
                    try:
                        # pdfplumber로 페이지 추출 (캐시된 데이터 사용)
                        ocr_data = pipeline._extract_page_pdfplumber(
                            None,  # PDF 객체는 필요 없음 (이미지만 사용)
                            page_num
                        )
                        if ocr_data:
                            all_ocr_data.append(ocr_data)
                    except Exception as e:
                        print(f"  ⚠️  페이지 {page_num} 추출 실패: {e}")

            if not all_ocr_data:
                print(f"  ❌ OCR 데이터 없음")
                continue

            # 강의 감지
            config = pipeline._get_default_config()
            from app.parsing.strategies.literature_strategy import LiteratureParsingStrategy
            strategy = LiteratureParsingStrategy()
            lectures = strategy.extract_lectures(all_ocr_data, config)

            print(f"  ✅ 감지된 강의 수: {len(lectures)}")
            for lec in lectures:
                print(f"     • 강의 {lec['lecture_id']}: {lec['title'][:60]} (페이지 {lec['page']})")

        except Exception as e:
            print(f"  ❌ 오류: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("테스트 완료")
    print("="*80)

if __name__ == "__main__":
    test_lecture_detection()
