"""
커리큘럼 삭제 스크립트
"""
import sys
from pathlib import Path

# api 디렉토리를 Python 경로에 추가
api_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_dir))

from app.db.session import SessionLocal
from app.db.models import Curriculum, LearningUnit

def delete_curriculum(curriculum_id: str = None, book_id: str = None):
    """커리큘럼 삭제"""
    db = SessionLocal()
    try:
        if curriculum_id:
            curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
        elif book_id:
            # book_id로 커리큘럼 찾기
            curriculum = db.query(Curriculum).filter(Curriculum.book_id == book_id).first()
        else:
            print("[오류] curriculum_id 또는 book_id가 필요합니다.")
            return False
        
        if not curriculum:
            print(f"[오류] 커리큘럼을 찾을 수 없습니다.")
            return False
        
        print(f"[확인] 커리큘럼 정보:")
        print(f"  ID: {curriculum.curriculum_id}")
        print(f"  제목: {curriculum.title}")
        print(f"  과목: {curriculum.subject}")
        print(f"  교재 ID: {curriculum.book_id}")
        print(f"  레슨 수: {curriculum.lesson_count}")
        
        # 관련 학습 단위 삭제
        learning_units = db.query(LearningUnit).filter(LearningUnit.curriculum_id == curriculum.curriculum_id).all()
        unit_count = len(learning_units)
        for unit in learning_units:
            db.delete(unit)
        if unit_count > 0:
            print(f"[삭제] 학습 단위 {unit_count}개 삭제")
        
        # 커리큘럼 삭제
        deleted_curriculum_id = curriculum.curriculum_id
        db.delete(curriculum)
        db.commit()
        
        print(f"[완료] 커리큘럼 삭제 완료: {deleted_curriculum_id}")
        return True
        
    except Exception as e:
        print(f"[오류] 삭제 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="커리큘럼 삭제")
    parser.add_argument("--curriculum-id", help="삭제할 커리큘럼 ID")
    parser.add_argument("--book-id", help="삭제할 교재 ID (해당 교재의 커리큘럼 삭제)")
    parser.add_argument("--yes", action="store_true", help="확인 없이 실행")
    
    args = parser.parse_args()
    
    if not args.curriculum_id and not args.book_id:
        print("[오류] --curriculum-id 또는 --book-id가 필요합니다.")
        sys.exit(1)
    
    target = args.curriculum_id or args.book_id
    if not args.yes:
        print(f"[경고] 다음 커리큘럼을 삭제합니다: {target}")
        confirm = input("계속하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            print("취소되었습니다.")
            sys.exit(0)
    
    success = delete_curriculum(curriculum_id=args.curriculum_id, book_id=args.book_id)
    sys.exit(0 if success else 1)
