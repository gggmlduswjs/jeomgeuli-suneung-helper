"""
잘못된 Unit 데이터 정리 스크립트

1. Lesson이 없는 Unit 삭제 (orphaned units)
2. Book이 없는 Lesson의 Unit 삭제
3. 데이터 일관성 검증 및 정리
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from app.db.session import SessionLocal
from app.db.models import Unit, Lesson, Book

def cleanup_orphaned_units():
    """Lesson이 없는 Unit 삭제"""
    print("=" * 60)
    print("1. Lesson이 없는 Unit (orphaned units) 정리")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 모든 Unit 조회
        all_units = db.query(Unit).all()
        print(f"전체 Unit 개수: {len(all_units)}")
        
        orphaned_units = []
        for unit in all_units:
            lesson = db.query(Lesson).filter(Lesson.lesson_id == unit.lesson_id).first()
            if not lesson:
                orphaned_units.append(unit)
        
        if not orphaned_units:
            print("✅ 정리할 orphaned unit이 없습니다.")
        else:
            print(f"⚠️  발견된 orphaned unit: {len(orphaned_units)}개")
            for unit in orphaned_units:
                print(f"  - {unit.unit_id} (lesson_id: {unit.lesson_id})")
                db.delete(unit)
            db.commit()
            print(f"✅ {len(orphaned_units)}개 orphaned unit 삭제 완료")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def cleanup_units_without_book():
    """Book이 없는 Lesson의 Unit 삭제"""
    print("\n" + "=" * 60)
    print("2. Book이 없는 Lesson의 Unit 정리")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 모든 Lesson 조회
        all_lessons = db.query(Lesson).all()
        print(f"전체 Lesson 개수: {len(all_lessons)}")
        
        invalid_lessons = []
        for lesson in all_lessons:
            book = db.query(Book).filter(Book.book_id == lesson.book_id).first()
            if not book:
                invalid_lessons.append(lesson)
        
        if not invalid_lessons:
            print("✅ 정리할 invalid lesson이 없습니다.")
        else:
            print(f"⚠️  발견된 invalid lesson: {len(invalid_lessons)}개")
            deleted_units_count = 0
            for lesson in invalid_lessons:
                units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
                deleted_units_count += len(units)
                print(f"  - Lesson {lesson.lesson_id} (book_id: {lesson.book_id}) - Unit {len(units)}개")
                for unit in units:
                    db.delete(unit)
                db.delete(lesson)
            db.commit()
            print(f"✅ {len(invalid_lessons)}개 invalid lesson과 {deleted_units_count}개 unit 삭제 완료")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def validate_unit_consistency():
    """Unit 데이터 일관성 검증 및 실제 문제 있는 Unit 찾기"""
    print("\n" + "=" * 60)
    print("3. Unit 데이터 일관성 검증")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        all_units = db.query(Unit).all()
        print(f"전체 Unit 개수: {len(all_units)}")
        
        real_issues = []  # 실제 문제가 있는 unit
        warnings = []  # 경고만 (lu_ ID는 정상일 수 있음)
        
        for unit in all_units:
            lesson = db.query(Lesson).filter(Lesson.lesson_id == unit.lesson_id).first()
            if not lesson:
                real_issues.append((unit, f"Lesson {unit.lesson_id} 없음"))
                continue
            
            book = db.query(Book).filter(Book.book_id == lesson.book_id).first()
            if not book:
                real_issues.append((unit, f"Book {lesson.book_id} 없음"))
                continue
            
            # unit_id가 lu_로 시작하는 것은 정상 (LearningUnit ID를 그대로 사용)
            # 실제 문제는 lesson이나 book이 없는 경우만
        
        if not real_issues:
            print("✅ 모든 Unit이 일관성 있게 연결되어 있습니다.")
            print(f"ℹ️  참고: {len(all_units)}개 Unit이 lu_ ID 형식을 사용 중입니다 (정상).")
        else:
            print(f"⚠️  발견된 실제 문제: {len(real_issues)}개")
            for unit, reason in real_issues[:20]:  # 최대 20개만 표시
                print(f"  - Unit {unit.unit_id}: {reason}")
            if len(real_issues) > 20:
                print(f"  ... 외 {len(real_issues) - 20}개")
            
            # 실제 문제가 있는 unit 삭제
            if real_issues:
                print(f"\n🔧 {len(real_issues)}개 문제 Unit 삭제 중...")
                deleted_count = 0
                for unit, reason in real_issues:
                    try:
                        db.delete(unit)
                        deleted_count += 1
                    except Exception as e:
                        print(f"  ❌ Unit {unit.unit_id} 삭제 실패: {e}")
                
                db.commit()
                print(f"✅ {deleted_count}개 문제 Unit 삭제 완료")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """메인 함수"""
    print("잘못된 Unit 데이터 정리 시작")
    print()
    
    # 1. Orphaned units 정리
    cleanup_orphaned_units()
    
    # 2. Book이 없는 Lesson의 Unit 정리
    cleanup_units_without_book()
    
    # 3. 데이터 일관성 검증
    validate_unit_consistency()
    
    print("\n" + "=" * 60)
    print("정리 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
