"""
DB에 저장된 데이터 확인 스크립트
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from app.db.session import SessionLocal
from app.db.models import Lesson, Unit, Book
from sqlalchemy import func

def main():
    db = SessionLocal()
    
    try:
        # Book 찾기
        book = db.query(Book).filter(Book.title.like('%수능특강%')).first()
        
        if not book:
            print("[ERROR] 수능특강 교재를 찾을 수 없습니다.")
            return
        
        print("=" * 80)
        print("DB 데이터 확인")
        print("=" * 80)
        print()
        print(f"교재: {book.title}")
        print(f"Book ID: {book.book_id}")
        print()
        
        # Lesson 수
        lessons = db.query(Lesson).filter(Lesson.book_id == book.book_id).order_by(Lesson.index).all()
        print(f"[Lesson] 총 {len(lessons)}개")
        print()
        
        if lessons:
            print("Lesson 목록 (최대 20개):")
            for lesson in lessons[:20]:
                unit_count = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).count()
                # 인코딩 문제 방지
                title_safe = lesson.title[:60].encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                print(f"   {lesson.index:2d}. {title_safe} ({unit_count}개 Unit)")
            
            if len(lessons) > 20:
                print(f"   ... 외 {len(lessons) - 20}개")
        
        print()
        
        # Unit 수
        total_units = db.query(Unit).join(Lesson).filter(Lesson.book_id == book.book_id).count()
        print(f"[Unit] 총 {total_units}개")
        
        # Unit 타입별 통계
        from app.db.models import UnitType
        unit_types = db.query(Unit.type, func.count(Unit.unit_id)).join(Lesson).filter(
            Lesson.book_id == book.book_id
        ).group_by(Unit.type).all()
        
        if unit_types:
            print()
            print("Unit 타입별 통계:")
            for unit_type, count in unit_types:
                type_name = unit_type.value if hasattr(unit_type, 'value') else str(unit_type)
                print(f"   {type_name}: {count}개")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
