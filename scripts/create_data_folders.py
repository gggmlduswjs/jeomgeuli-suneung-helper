"""
데이터 폴더 구조 생성 스크립트
"""
from pathlib import Path
import sys

# 프로젝트 루트 경로
project_root = Path(__file__).resolve().parent.parent

# 생성할 폴더 구조
folders = [
    "data/lecture_scripts/수능특강_문학_2026",
    "data/lecture_scripts/수능특강_수1_2026",
    "data/lecture_scripts/수능특강_영어_2026",
    "data/lecture_scripts/수능특강_독서_2026",
    "data/lecture_scripts/수능특강_화법과작문_2026",
    "data/pdfs",
    "data/datasets",
]

def create_folders():
    """폴더 생성"""
    created = []
    failed = []
    
    for folder_path in folders:
        full_path = project_root / folder_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(folder_path)
            print(f"[OK] {folder_path}")
        except Exception as e:
            failed.append((folder_path, str(e)))
            print(f"[FAIL] {folder_path} - {e}")
    
    print(f"\n총 {len(created)}개 폴더 생성 완료")
    if failed:
        print(f"\n{len(failed)}개 폴더 생성 실패:")
        for folder, error in failed:
            print(f"  - {folder}: {error}")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = create_folders()
    sys.exit(0 if success else 1)
