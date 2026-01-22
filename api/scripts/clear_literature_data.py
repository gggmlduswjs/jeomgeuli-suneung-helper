"""
수능특강 문학 데이터 삭제 스크립트
기존 파이프라인 결과를 모두 삭제하여 재생성 준비
"""
import sys
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from app.core.config import settings

def main():
    data_dir = settings.API_DIR / "data" / "literature"
    lectures_dir = data_dir / "lectures"
    
    print("=" * 80)
    print("수능특강 문학 데이터 삭제")
    print("=" * 80)
    print()
    
    if not lectures_dir.exists():
        print("[INFO] lectures 디렉토리가 없습니다. 삭제할 데이터가 없습니다.")
        return
    
    # 삭제할 파일 목록
    files_to_delete = []
    
    # lectures.json
    lectures_json = lectures_dir / "lectures.json"
    if lectures_json.exists():
        files_to_delete.append(lectures_json)
    
    # lecture_XX.json 파일들
    for lecture_file in lectures_dir.glob("lecture_*.json"):
        files_to_delete.append(lecture_file)
    
    if not files_to_delete:
        print("[INFO] 삭제할 파일이 없습니다.")
        return
    
    print(f"[삭제 예정] {len(files_to_delete)}개 파일")
    print()
    
    # 확인 (명령줄 인자로 --yes가 있으면 자동 삭제)
    import sys
    auto_yes = '--yes' in sys.argv or '-y' in sys.argv
    
    if not auto_yes:
        try:
            response = input("정말 삭제하시겠습니까? (yes/no): ")
            if response.lower() != 'yes':
                print("[취소] 삭제를 취소했습니다.")
                return
        except (EOFError, KeyboardInterrupt):
            print("[취소] 삭제를 취소했습니다.")
            return
    else:
        print("[자동] --yes 플래그로 자동 삭제를 진행합니다.")
    
    # 삭제 실행
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            file_path.unlink()
            deleted_count += 1
            print(f"  [삭제] {file_path.name}")
        except Exception as e:
            print(f"  [오류] {file_path.name}: {e}")
    
    print()
    print("=" * 80)
    print(f"[완료] {deleted_count}개 파일 삭제 완료")
    print("=" * 80)
    print()
    print("이제 파이프라인을 재실행하면 모든 데이터를 새로 생성합니다.")
    print("  python api/scripts/test_suneung_literature.py")

if __name__ == "__main__":
    main()
