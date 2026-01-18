"""
HWP 파일 추출 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.services.hwp_extract import extract_text_from_hwp

# 테스트: 첫 번째 HWP 파일 찾기
script_path = Path(__file__).resolve()
api_dir = script_path.parent
project_root = api_dir.parent
scripts_dir = project_root / "data" / "lecture_scripts" / "수능특강_문학_2026"

print(f"[디버그] 프로젝트 루트: {project_root}")
print(f"[디버그] 스크립트 디렉토리: {scripts_dir}")
print(f"[디버그] 존재 여부: {scripts_dir.exists()}")

if not scripts_dir.exists():
    print(f"[오류] 디렉토리를 찾을 수 없습니다: {scripts_dir}")
    sys.exit(1)

# 첫 번째 HWP 파일 찾기
hwp_files = list(scripts_dir.glob("*.hwp"))
if not hwp_files:
    print(f"[오류] HWP 파일을 찾을 수 없습니다: {scripts_dir}")
    sys.exit(1)

test_file = hwp_files[0]
print(f"[테스트] 파일: {test_file.name}")
print(f"[테스트] 경로: {test_file}")
print("-" * 70)

# HWP 파일에서 텍스트 추출
try:
    text = extract_text_from_hwp(test_file)
    
    if text:
        print(f"[성공] 텍스트 추출 성공!")
        print(f"[성공] 텍스트 길이: {len(text)} 문자")
        print(f"[성공] 텍스트 미리보기 (처음 500자):")
        print("-" * 70)
        print(text[:500])
        print("-" * 70)
        print(f"[성공] 텍스트 미리보기 (마지막 200자):")
        print("-" * 70)
        # 인코딩 문제 방지를 위해 파일로 저장
        preview_file = Path(__file__).parent / "hwp_extract_preview.txt"
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write("=== 처음 500자 ===\n")
            f.write(text[:500])
            f.write("\n\n=== 마지막 200자 ===\n")
            f.write(text[-200:])
        print(f"[저장] 미리보기 파일: {preview_file}")
    else:
        print("[실패] 텍스트를 추출할 수 없습니다.")
        
except Exception as e:
    print(f"[오류] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
