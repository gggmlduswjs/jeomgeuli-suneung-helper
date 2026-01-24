"""
수능특강 문학 실제 데이터 생성 스크립트

파이프라인 결과를 DB에 저장하여 Lesson과 Unit 생성
"""
import sys
from pathlib import Path

# Windows 콘솔 UTF-8 인코딩 설정
try:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except:
    pass

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from app.db.session import SessionLocal
from app.db.models import Book, Subject, ParseStatus
from app.routers.books import _create_curriculum_from_pipeline
from app.utils.id_generator import generate_book_id
from sqlalchemy import func
import json

def main():
    print("=" * 80)
    print("수능특강 문학 실제 데이터 생성")
    print("=" * 80)
    print()
    
    # DB 세션 생성
    db = SessionLocal()
    
    try:
        # 1. 과목 및 연도 설정
        book_title = "2026 수능특강 문학"
        book_year = 2026
        subject = Subject.KOREAN

        print(f"[과목] {subject.value}")
        print(f"[연도] {book_year}")
        print()

        # 같은 과목 + 연도의 모든 기존 교재 찾기 (제목 무관)
        existing_books = db.query(Book).filter(
            Book.subject == subject,
            Book.year == book_year
        ).all()

        if existing_books:
            print(f"[기존 교재 발견] {len(existing_books)}개")
            for existing_book in existing_books:
                print(f"  - {existing_book.book_id}: {existing_book.title} ({existing_book.parse_status.value})")
            print()

            # 모든 기존 교재 삭제
            from app.db.models import Lesson, Unit, Curriculum, LearningUnit

            print("[기존 데이터 삭제] 시작...")
            total_lessons = 0
            total_units = 0
            total_curricula = 0

            for existing_book in existing_books:
                book_id = existing_book.book_id
                print(f"\n  교재: {existing_book.title} ({book_id})")

                # 해당 Book에 연결된 모든 Lesson 찾기
                existing_lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
                if existing_lessons:
                    lesson_count = len(existing_lessons)
                    unit_count = 0
                    for lesson in existing_lessons:
                        # Lesson에 연결된 Unit 삭제 (cascade로 자동 삭제되지만 명시적으로 처리)
                        unit_count += len(lesson.units)
                    print(f"    - Lesson: {lesson_count}개, Unit: {unit_count}개 삭제")
                    total_lessons += lesson_count
                    total_units += unit_count

                # 해당 Book에 연결된 모든 Curriculum 찾기
                existing_curricula = db.query(Curriculum).filter(Curriculum.book_id == book_id).all()
                if existing_curricula:
                    curriculum_count = len(existing_curricula)
                    print(f"    - Curriculum: {curriculum_count}개 삭제")
                    total_curricula += curriculum_count

                # Book 삭제 (cascade로 Lesson, Unit, Curriculum 모두 자동 삭제)
                db.delete(existing_book)

            db.commit()
            print(f"\n[기존 데이터 삭제] 완료")
            print(f"  - Book: {len(existing_books)}개")
            print(f"  - Lesson: {total_lessons}개")
            print(f"  - Unit: {total_units}개")
            print(f"  - Curriculum: {total_curricula}개")
            print()

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
        print(f"[새 교재 생성] {book_id} - {book_title}")
        print()

        # 2. 파이프라인 결과 확인
        from app.core.config import settings
        data_dir = settings.API_DIR / "data" / "literature"
        lectures_dir = data_dir / "lectures"
        lectures_json = lectures_dir / "lectures.json"
        
        if not lectures_json.exists():
            print(f"[ERROR] 파이프라인 결과를 찾을 수 없습니다: {lectures_json}")
            print(f"   먼저 파이프라인을 실행하세요:")
            print(f"   python api/scripts/test_suneung_literature.py")
            return
        
        # lectures.json 읽기
        with open(lectures_json, "r", encoding="utf-8") as f:
            lectures_data = json.load(f)
        
        if isinstance(lectures_data, dict):
            lectures_list = lectures_data.get("lectures", [])
        else:
            lectures_list = lectures_data
        
        print(f"[파이프라인 결과] 강의 수: {len(lectures_list)}개")
        print()
        
        if not lectures_list:
            print("[ERROR] 강의 데이터가 없습니다. 파이프라인을 먼저 실행하세요.")
            return
        
        # 3. 커리큘럼 생성 및 Lesson/Unit 저장
        print(f"[DB 저장] 시작...")
        print()
        
        curriculum_id = _create_curriculum_from_pipeline(
            book_id=book_id,
            subject_enum=subject,
            pipeline_subject="literature",
            title=book_title,
            db=db
        )
        
        print()
        print("=" * 80)
        print("[완료] 데이터 생성 완료")
        print("=" * 80)
        print()
        print(f"교재 ID: {book_id}")
        print(f"커리큘럼 ID: {curriculum_id}")
        print()
        
        # 4. 생성된 Lesson 확인
        from app.db.models import Lesson, Unit
        lessons = db.query(Lesson).filter(Lesson.book_id == book_id).order_by(Lesson.index).all()
        print(f"[생성된 Lesson] {len(lessons)}개")
        
        if lessons:
            print()
            print("Lesson 목록 (최대 10개):")
            for lesson in lessons[:10]:
                unit_count = len(lesson.units) if lesson.units else 0
                print(f"   {lesson.index:2d}. {lesson.title[:50]} ({unit_count}개 Unit)")
            
            if len(lessons) > 10:
                print(f"   ... 외 {len(lessons) - 10}개")
        
        print()
        
        # 5. 생성된 Unit 확인
        total_units = db.query(Unit).join(Lesson).filter(Lesson.book_id == book_id).count()
        print(f"[생성된 Unit] {total_units}개")
        
        # Unit 타입별 통계
        from app.db.models import UnitType
        unit_types = db.query(Unit.type, func.count(Unit.unit_id)).join(Lesson).filter(
            Lesson.book_id == book_id
        ).group_by(Unit.type).all()
        
        if unit_types:
            print()
            print("Unit 타입별 통계:")
            for unit_type, count in unit_types:
                print(f"   {unit_type.value if hasattr(unit_type, 'value') else unit_type}: {count}개")
        
        print()
        print("=" * 80)
        print("[완료] 모든 작업 완료")
        print("=" * 80)
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 80)
        print("[ERROR] 오류 발생")
        print("=" * 80)
        print(f"에러: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
