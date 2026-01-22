"""
수능특강 문학 실제 데이터 생성 스크립트 (인코딩 안전 버전)
"""
import sys
import os
from pathlib import Path

# Windows 인코딩 문제 해결
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from app.db.session import SessionLocal
from app.db.models import Book, Subject, ParseStatus
from app.routers.books import _create_curriculum_from_pipeline
from app.utils.id_generator import generate_book_id
import json

def safe_print(*args, **kwargs):
    """안전한 출력 함수"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 인코딩 오류 시 ASCII로 변환
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
            else:
                safe_args.append(str(arg))
        print(*safe_args, **kwargs)

def main():
    safe_print("=" * 80)
    safe_print("수능특강 문학 실제 데이터 생성")
    safe_print("=" * 80)
    safe_print()
    
    # DB 세션 생성
    db = SessionLocal()
    
    try:
        # 1. Book 생성 또는 찾기
        book_title = "2026 수능특강 문학"
        book_year = 2026
        subject = Subject.KOREAN
        
        # 기존 Book 찾기
        existing_book = db.query(Book).filter(
            Book.title == book_title,
            Book.subject == subject
        ).first()
        
        if existing_book:
            book_id = existing_book.book_id
            safe_print(f"[기존 교재] {book_id} - {book_title}")
        else:
            # 새 Book 생성
            book_id = generate_book_id("literature", book_title, book_year)
            book = Book(
                book_id=book_id,
                title=book_title,
                subject=subject,
                year=book_year,
                parse_status=ParseStatus.DONE
            )
            db.add(book)
            db.commit()
            db.refresh(book)
            safe_print(f"[새 교재] {book_id} - {book_title}")
        
        safe_print()
        
        # 2. 파이프라인 결과 확인
        from app.core.config import settings
        data_dir = settings.API_DIR / "data" / "literature"
        lectures_dir = data_dir / "lectures"
        lectures_json = lectures_dir / "lectures.json"
        
        if not lectures_json.exists():
            safe_print(f"[ERROR] 파이프라인 결과를 찾을 수 없습니다: {lectures_json}")
            safe_print(f"   먼저 파이프라인을 실행하세요:")
            safe_print(f"   python api/scripts/test_suneung_literature.py")
            return
        
        # lectures.json 읽기
        with open(lectures_json, "r", encoding="utf-8") as f:
            lectures_data = json.load(f)
        
        if isinstance(lectures_data, dict):
            lectures_list = lectures_data.get("lectures", [])
        else:
            lectures_list = lectures_data
        
        safe_print(f"[파이프라인 결과] 강의 수: {len(lectures_list)}개")
        safe_print()
        
        if not lectures_list:
            safe_print("[ERROR] 강의 데이터가 없습니다. 파이프라인을 먼저 실행하세요.")
            return
        
        # 3. 커리큘럼 생성 및 Lesson/Unit 저장
        safe_print(f"[DB 저장] 시작...")
        safe_print()
        
        curriculum_id = _create_curriculum_from_pipeline(
            book_id=book_id,
            subject_enum=subject,
            pipeline_subject="literature",
            title=book_title,
            db=db
        )
        
        safe_print()
        safe_print("=" * 80)
        safe_print("[완료] 데이터 생성 완료")
        safe_print("=" * 80)
        safe_print()
        safe_print(f"교재 ID: {book_id}")
        safe_print(f"커리큘럼 ID: {curriculum_id}")
        safe_print()
        
        # 4. 생성된 Lesson 확인
        from app.db.models import Lesson, Unit
        lessons = db.query(Lesson).filter(Lesson.book_id == book_id).order_by(Lesson.index).all()
        safe_print(f"[생성된 Lesson] {len(lessons)}개")
        
        if lessons:
            safe_print()
            safe_print("Lesson 목록 (최대 20개):")
            for lesson in lessons[:20]:
                unit_count = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).count()
                title_safe = lesson.title[:60] if lesson.title else "N/A"
                safe_print(f"   {lesson.index:2d}. {title_safe} ({unit_count}개 Unit)")
            
            if len(lessons) > 20:
                safe_print(f"   ... 외 {len(lessons) - 20}개")
        
        safe_print()
        
        # 5. 생성된 Unit 확인
        total_units = db.query(Unit).join(Lesson).filter(Lesson.book_id == book_id).count()
        safe_print(f"[생성된 Unit] {total_units}개")
        
        # Unit 타입별 통계
        from app.db.models import UnitType
        from sqlalchemy import func
        unit_types = db.query(Unit.type, func.count(Unit.unit_id)).join(Lesson).filter(
            Lesson.book_id == book_id
        ).group_by(Unit.type).all()
        
        if unit_types:
            safe_print()
            safe_print("Unit 타입별 통계:")
            for unit_type, count in unit_types:
                type_name = unit_type.value if hasattr(unit_type, 'value') else str(unit_type)
                safe_print(f"   {type_name}: {count}개")
        
        safe_print()
        safe_print("=" * 80)
        safe_print("[완료] 모든 작업 완료")
        safe_print("=" * 80)
        
    except Exception as e:
        db.rollback()
        safe_print()
        safe_print("=" * 80)
        safe_print("[ERROR] 오류 발생")
        safe_print("=" * 80)
        safe_print(f"에러: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
