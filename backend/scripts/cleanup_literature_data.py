"""
literature 디렉토리 정리 스크립트
템플릿 파일(config.json)을 제외한 모든 데이터 삭제
"""
import sys
from pathlib import Path
import shutil
import json

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings


def find_template_files(literature_dir: Path) -> list[Path]:
    """템플릿 파일 찾기 (config.json)"""
    templates = []
    
    # 루트의 config.json
    root_config = literature_dir / "config.json"
    if root_config.exists():
        templates.append(root_config)
    
    # 하위 디렉토리의 config.json도 찾기
    for config_file in literature_dir.rglob("config.json"):
        if config_file not in templates:
            templates.append(config_file)
    
    return templates


def cleanup_literature_data():
    """literature 디렉토리 정리 (템플릿 제외)"""
    literature_dir = settings.API_DIR / "data" / "literature"
    
    if not literature_dir.exists():
        print(f"[INFO] literature 디렉토리가 없습니다: {literature_dir}")
        return
    
    print("=" * 60)
    print("literature 디렉토리 정리")
    print("=" * 60)
    print(f"경로: {literature_dir}")
    print()
    
    # 템플릿 파일 찾기
    template_files = find_template_files(literature_dir)
    print(f"템플릿 파일 ({len(template_files)}개):")
    for template in template_files:
        print(f"  - {template.relative_to(literature_dir)}")
    print()
    
    # 삭제할 항목 확인
    items_to_delete = []
    
    for item in literature_dir.iterdir():
        if item.is_file():
            # 템플릿 파일이 아니면 삭제 대상
            if item not in template_files:
                items_to_delete.append(item)
        elif item.is_dir():
            # pdf 디렉토리는 유지할 수도 있지만, 사용자가 완전히 정리하길 원하므로 삭제
            # lectures 디렉토리도 삭제
            items_to_delete.append(item)
    
    if not items_to_delete:
        print("[INFO] 삭제할 항목이 없습니다.")
        return
    
    print(f"삭제할 항목 ({len(items_to_delete)}개):")
    for item in items_to_delete:
        print(f"  - {item.name}")
    print()
    
    # 확인 (명령줄 인자로 --force가 있으면 자동 실행)
    import sys
    force = '--force' in sys.argv or '-f' in sys.argv
    
    if not force:
        try:
            response = input("위 항목들을 삭제하시겠습니까? (y/n): ")
            if response.lower() != 'y':
                print("취소되었습니다.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n취소되었습니다.")
            return
    else:
        print("--force 플래그: 자동으로 삭제를 진행합니다...")
    
    # 삭제 실행
    deleted_count = 0
    for item in items_to_delete:
        try:
            if item.is_file():
                item.unlink()
                print(f"[OK] 파일 삭제: {item.name}")
            elif item.is_dir():
                shutil.rmtree(item)
                print(f"[OK] 디렉토리 삭제: {item.name}")
            deleted_count += 1
        except Exception as e:
            print(f"[ERROR] 삭제 실패: {item.name} - {e}")
    
    print()
    print("=" * 60)
    print(f"정리 완료: {deleted_count}개 항목 삭제")
    print("=" * 60)
    print()
    print("남은 파일:")
    remaining = list(literature_dir.iterdir())
    if remaining:
        for item in remaining:
            print(f"  - {item.name}")
    else:
        print("  (없음)")
    print()
    print("다음 단계:")
    print("1. 관리자 페이지에서 새로 교재 업로드")
    print("2. 또는 재파싱 실행")


if __name__ == "__main__":
    cleanup_literature_data()
