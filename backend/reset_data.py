"""
데이터베이스 및 파일 시스템 완전 초기화 스크립트
주의: 모든 교재, 레슨, 학습 단위 데이터가 삭제됩니다!
"""
import sys
import shutil
from pathlib import Path
from sqlalchemy import text

# API 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal, engine, Base

def reset_database():
    """데이터베이스 초기화"""
    print("\n=== 데이터베이스 초기화 ===")

    # 모든 테이블 삭제 후 재생성
    Base.metadata.drop_all(bind=engine)
    print("✓ 모든 테이블 삭제 완료")

    Base.metadata.create_all(bind=engine)
    print("✓ 테이블 재생성 완료")

def reset_file_system():
    """파일 시스템 초기화"""
    print("\n=== 파일 시스템 초기화 ===")

    data_dir = Path(__file__).parent / "data"

    if not data_dir.exists():
        print("✓ data 디렉토리가 없습니다. 건너뜁니다.")
        return

    # 각 과목 디렉토리 처리
    for subject_dir in data_dir.iterdir():
        if subject_dir.is_dir():
            print(f"\n과목: {subject_dir.name}")

            # 하위 디렉토리 삭제
            for sub_dir in subject_dir.iterdir():
                if sub_dir.is_dir():
                    try:
                        shutil.rmtree(sub_dir)
                        print(f"  ✓ 삭제: {sub_dir.name}/")
                    except Exception as e:
                        print(f"  ✗ 실패: {sub_dir.name}/ - {e}")
                elif sub_dir.is_file() and sub_dir.name != 'config.json':
                    try:
                        sub_dir.unlink()
                        print(f"  ✓ 삭제: {sub_dir.name}")
                    except Exception as e:
                        print(f"  ✗ 실패: {sub_dir.name} - {e}")

def main():
    print("=" * 60)
    print("⚠️  데이터 완전 삭제 스크립트")
    print("=" * 60)
    print("\n이 작업은 다음을 삭제합니다:")
    print("  1. 데이터베이스의 모든 테이블 및 데이터")
    print("  2. api/data/ 디렉토리의 모든 파일 (config.json 제외)")
    print("\n⚠️  이 작업은 되돌릴 수 없습니다!")

    confirm = input("\n계속하시겠습니까? (yes/no): ")

    if confirm.lower() != 'yes':
        print("\n작업이 취소되었습니다.")
        return

    try:
        # 1. 데이터베이스 초기화
        reset_database()

        # 2. 파일 시스템 초기화
        reset_file_system()

        print("\n" + "=" * 60)
        print("✅ 데이터 초기화가 완료되었습니다!")
        print("=" * 60)
        print("\n이제 새로운 PDF를 업로드할 수 있습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
