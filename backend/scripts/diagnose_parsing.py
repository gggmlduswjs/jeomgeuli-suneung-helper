"""
파싱 진단 스크립트
파싱이 잘 되고 있는지, 실패 원인은 무엇인지 확인
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models import Book, ParseStatus, Lesson, Unit
from app.core.config import settings


def diagnose_book(book_id: str = None):
    """교재 파싱 상태 진단"""
    db = SessionLocal()
    
    try:
        if book_id:
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if not book:
                print(f"[ERROR] 교재를 찾을 수 없습니다: {book_id}")
                return
            books = [book]
        else:
            # 최근 교재 5개
            books = db.query(Book).order_by(Book.created_at.desc()).limit(5).all()
        
        print("=" * 80)
        print("파싱 진단 리포트")
        print("=" * 80)
        print(f"진단 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        for book in books:
            print("-" * 80)
            print(f"교재: {book.title}")
            print(f"ID: {book.book_id}")
            print(f"과목: {book.subject}")
            print(f"상태: {book.parse_status.value if hasattr(book.parse_status, 'value') else book.parse_status}")
            print(f"진행률: {book.parse_progress or 0}%")
            if book.total_pages:
                print(f"페이지: {book.current_page or 0}/{book.total_pages}")
            print()
            
            # 1. 파싱 상태 확인
            if book.parse_status == ParseStatus.PROCESSING:
                print("[진단] 파싱이 진행 중입니다.")
                print(f"  - 진행률: {book.parse_progress}%")
                if book.current_page and book.total_pages:
                    remaining = book.total_pages - book.current_page
                    print(f"  - 남은 페이지: {remaining}개")
                print()
            
            elif book.parse_status == ParseStatus.FAILED:
                print("[진단] 파싱이 실패했습니다.")
                print()
                print("[원인 분석]")
                
                # 원인 1: 강의가 없음
                lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
                if lesson_count == 0:
                    print("  ❌ 강의가 0개입니다.")
                    print("     가능한 원인:")
                    print("     1. PDF에서 강의 제목을 찾지 못함")
                    print("     2. 강의 제목 패턴이 맞지 않음")
                    print("     3. OCR 품질이 낮아 텍스트 추출 실패")
                    print()
                    print("     해결 방법:")
                    print("     1. 캐시 삭제 후 재파싱")
                    print("     2. config.json의 강의 제목 패턴 확인")
                    print("     3. Tesseract 한국어 언어팩 설치 확인")
                    print()
                
                # 원인 2: JSON 파일 확인
                from app.routers.books import _subject_to_pipeline_subject
                pipeline_subject = _subject_to_pipeline_subject(book.subject)
                data_dir = settings.API_DIR / "data" / pipeline_subject / book.book_id
                lectures_dir = data_dir / "lectures"
                
                if lectures_dir.exists():
                    lecture_files = list(lectures_dir.glob("lecture_*.json"))
                    lecture_files = [f for f in lecture_files if f.name != "lectures.json"]
                    if lecture_files:
                        print(f"  ✅ JSON 파일 {len(lecture_files)}개 발견")
                        print("     → JSON 파일은 있지만 DB 동기화가 실패했을 수 있습니다.")
                        print("     → 'JSON 동기화' 버튼을 클릭하세요.")
                        print()
                    else:
                        print("  ❌ JSON 파일이 없습니다.")
                        print(f"     경로: {lectures_dir}")
                        print("     → 파이프라인이 강의를 찾지 못했습니다.")
                        print()
                else:
                    print("  ❌ 데이터 디렉토리가 없습니다.")
                    print(f"     경로: {data_dir}")
                    print("     → 파이프라인이 실행되지 않았거나 실패했습니다.")
                    print()
                
                # 원인 3: PDF 파일 확인
                if book.file_path:
                    pdf_path = Path(book.file_path)
                    if pdf_path.exists():
                        print(f"  ✅ PDF 파일 존재: {pdf_path}")
                        print(f"     크기: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB")
                    else:
                        print(f"  ❌ PDF 파일이 없습니다: {pdf_path}")
                print()
            
            elif book.parse_status == ParseStatus.DONE:
                print("[진단] 파싱이 완료되었습니다.")
                print()
                
                # 결과 확인
                lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
                unit_count = db.query(Unit).join(Lesson).filter(Lesson.book_id == book.book_id).count()
                
                print("[결과 확인]")
                print(f"  - Lesson: {lesson_count}개")
                print(f"  - Unit: {unit_count}개")
                print()
                
                if lesson_count == 0:
                    print("  ⚠️ 경고: Lesson이 0개입니다!")
                    print("     → JSON 파일은 있지만 DB 동기화가 실패했을 수 있습니다.")
                    print("     → 'JSON 동기화' 버튼을 클릭하세요.")
                    print()
                elif unit_count == 0:
                    print("  ⚠️ 경고: Unit이 0개입니다!")
                    print("     → LearningUnit → Unit 변환이 실패했을 수 있습니다.")
                    print()
                else:
                    print("  ✅ 파싱이 정상적으로 완료되었습니다!")
                    print()
                
                # JSON 파일 확인
                from app.routers.books import _subject_to_pipeline_subject
                pipeline_subject = _subject_to_pipeline_subject(book.subject)
                data_dir = settings.API_DIR / "data" / pipeline_subject / book.book_id
                lectures_dir = data_dir / "lectures"
                
                if lectures_dir.exists():
                    lecture_files = list(lectures_dir.glob("lecture_*.json"))
                    lecture_files = [f for f in lecture_files if f.name != "lectures.json"]
                    print(f"[JSON 파일]")
                    print(f"  - 발견된 파일: {len(lecture_files)}개")
                    if lecture_files:
                        print(f"  - 경로: {lectures_dir}")
                        print(f"  - 예시: {lecture_files[0].name}")
                    print()
            
            # 2. 최근 활동 확인
            print("[최근 활동]")
            print(f"  - 생성 시간: {book.created_at}")
            if book.parse_status == ParseStatus.PROCESSING:
                # 파싱이 너무 오래 진행 중이면 경고
                if book.created_at:
                    try:
                        now = datetime.now()
                        if book.created_at.tzinfo is None:
                            # naive datetime
                            elapsed = (now - book.created_at).total_seconds()
                        else:
                            # aware datetime
                            elapsed = (datetime.now(timezone.utc) - book.created_at).total_seconds()
                        
                        if elapsed > 600:  # 10분 이상
                            print(f"  [WARNING] 파싱이 {elapsed/60:.1f}분 동안 진행 중입니다.")
                            print("     → 파싱이 멈춘 것일 수 있습니다.")
                            print("     → 재파싱을 시도하세요.")
                    except Exception as e:
                        pass  # 시간 계산 실패 시 무시
            print()
        
        print("=" * 80)
        
    finally:
        db.close()


def main():
    """메인 함수"""
    book_id = sys.argv[1] if len(sys.argv) > 1 else None
    diagnose_book(book_id)


if __name__ == "__main__":
    main()
