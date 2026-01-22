"""
문학 교재를 제외한 모든 교재 삭제 스크립트
"""
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from app.db.session import SessionLocal
from app.db.models import Book, Lesson, Unit, Curriculum, LearningUnit, Subject
from sqlalchemy import or_

def delete_books(books_to_delete, db):
    """교재 삭제 헬퍼 함수"""
    deleted_count = 0
    for book in books_to_delete:
        book_id = book.book_id
        book_title = book.title
        
        print(f"[삭제 중] {book_title}...")
        
        # 1. Lesson과 Unit 삭제
        lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        for lesson in lessons:
            # Unit 삭제
            units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            for unit in units:
                db.delete(unit)
            # Lesson 삭제
            db.delete(lesson)
        
        # 2. Curriculum과 LearningUnit 삭제
        curricula = db.query(Curriculum).filter(Curriculum.book_id == book_id).all()
        for curriculum in curricula:
            # LearningUnit 삭제
            learning_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == curriculum.curriculum_id
            ).all()
            for lu in learning_units:
                db.delete(lu)
            # Curriculum 삭제
            db.delete(curriculum)
        
        # 3. Book 삭제
        db.delete(book)
        
        deleted_count += 1
        print(f"  [완료] 삭제 완료: {book_title}")
    
    db.commit()
    return deleted_count

def main():
    parser = argparse.ArgumentParser(description="문학 교재를 제외한 모든 교재 삭제")
    parser.add_argument("--yes", "-y", action="store_true", help="확인 없이 자동 실행")
    args = parser.parse_args()
    
    print("=" * 80)
    print("문학 교재를 제외한 모든 교재 삭제")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        # 문학 교재 찾기 (KOREAN subject 또는 제목에 "문학"이 포함된 것)
        literature_books = db.query(Book).filter(
            or_(
                Book.subject == Subject.KOREAN,
                Book.title.like('%문학%')
            )
        ).all()
        
        print(f"[문학 교재] {len(literature_books)}개 발견:")
        for book in literature_books:
            lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
            print(f"  - {book.title} (Book ID: {book.book_id}, Lesson: {lesson_count}개)")
        print()
        
        # 문학이 아닌 교재 찾기
        non_literature_books = db.query(Book).filter(
            ~or_(
                Book.subject == Subject.KOREAN,
                Book.title.like('%문학%')
            )
        ).all()
        
        # 문학이 아닌 교재 삭제
        deleted_count = 0
        if non_literature_books:
            print(f"[삭제 대상] 문학이 아닌 교재 {len(non_literature_books)}개:")
            for book in non_literature_books:
                lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
                print(f"  - {book.title} (Book ID: {book.book_id}, Subject: {book.subject.value}, Lesson: {lesson_count}개)")
            print()
            
            # 확인 (비대화형 환경에서는 자동 실행)
            import sys
            if sys.stdin.isatty():
                response = input(f"정말 {len(non_literature_books)}개 교재를 삭제하시겠습니까? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print("[취소] 삭제가 취소되었습니다.")
                else:
                    deleted_count = delete_books(non_literature_books, db)
            else:
                print(f"[자동 실행] {len(non_literature_books)}개 교재를 삭제합니다...")
                deleted_count = delete_books(non_literature_books, db)
            
            if deleted_count > 0:
                print()
                print("=" * 80)
                print(f"[완료] {deleted_count}개 교재 삭제 완료")
                print("=" * 80)
        else:
            print("[완료] 삭제할 문학이 아닌 교재가 없습니다.")
        
        # 실패한 문학 교재도 삭제 (Lesson이 0개이거나 4개 이하인 문학 교재)
        print()
        print("[실패한 문학 교재 삭제]")
        failed_literature_books = []
        for book in literature_books:
            lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
            # Lesson이 0개이거나 4개 이하인 문학 교재는 실패한 것으로 간주
            if lesson_count <= 4:
                failed_literature_books.append(book)
        
        if failed_literature_books:
            print(f"[삭제 대상] 실패한 문학 교재 {len(failed_literature_books)}개:")
            for book in failed_literature_books:
                lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
                print(f"  - {book.title} (Book ID: {book.book_id}, Lesson: {lesson_count}개)")
            print()
            
            # 확인
            failed_deleted_count = 0
            if not args.yes:
                if sys.stdin.isatty():
                    response = input(f"정말 {len(failed_literature_books)}개 실패한 문학 교재를 삭제하시겠습니까? (yes/no): ")
                    if response.lower() not in ['yes', 'y']:
                        print("[취소] 삭제가 취소되었습니다.")
                    else:
                        failed_deleted_count = delete_books(failed_literature_books, db)
                        deleted_count += failed_deleted_count
                else:
                    print(f"[자동 실행] {len(failed_literature_books)}개 실패한 문학 교재를 삭제합니다...")
                    failed_deleted_count = delete_books(failed_literature_books, db)
                    deleted_count += failed_deleted_count
            else:
                print(f"[자동 실행] {len(failed_literature_books)}개 실패한 문학 교재를 삭제합니다...")
                failed_deleted_count = delete_books(failed_literature_books, db)
                deleted_count += failed_deleted_count
            
            if failed_deleted_count > 0:
                print()
                print("=" * 80)
                print(f"[완료] {failed_deleted_count}개 실패한 문학 교재 삭제 완료")
                print("=" * 80)
        else:
            print("[완료] 삭제할 실패한 문학 교재가 없습니다.")
        
        # 남은 교재 확인
        remaining_books = db.query(Book).all()
        print()
        print(f"[남은 교재] {len(remaining_books)}개:")
        for book in remaining_books:
            lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
            print(f"  - {book.title} (Subject: {book.subject.value}, Lesson: {lesson_count}개)")
        
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
