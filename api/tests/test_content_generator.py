"""
자동 제작 시스템 테스트 스크립트
"""
from pathlib import Path
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services.content_auto_generator import ContentAutoGenerator

# 한글 파일 경로 (프로젝트 루트 기준)
hwp_file = Path("../data/lecture_scripts/수능특강_문학_2026/01강_[교과서_개념]_1_2_(고3_기본).hwp")

# 파일 존재 확인
if not hwp_file.exists():
    print(f"❌ 한글 파일을 찾을 수 없습니다: {hwp_file}")
    print(f"   현재 작업 디렉토리: {Path.cwd()}")
    print(f"   절대 경로: {hwp_file.resolve()}")
    
    # 대체 파일 찾기
    hwp_dir = Path("../data/lecture_scripts")
    if hwp_dir.exists():
        subject_dirs = [d for d in hwp_dir.iterdir() if d.is_dir()]
        if subject_dirs:
            subject_dir = subject_dirs[0]
            hwp_files = list(subject_dir.glob("*.hwp"))
            if hwp_files:
                hwp_file = hwp_files[0]
                print(f"   대체 파일 사용: {hwp_file}")
            else:
                print(f"   {subject_dir} 폴더에 한글 파일이 없습니다.")
                sys.exit(1)
        else:
            print(f"   {hwp_dir} 폴더에 과목 폴더가 없습니다.")
            sys.exit(1)
    else:
        print(f"   {hwp_dir} 폴더가 존재하지 않습니다.")
        sys.exit(1)

print(f"📄 한글 파일: {hwp_file.name}")
print(f"🔄 자동 제작 시스템 실행 중...\n")

try:
    generator = ContentAutoGenerator()
    result = generator.generate_structured_content(hwp_file)
    
    if result:
        print("✅ 자동 제작 성공!\n")
        
        # 결과 요약
        sections = result.get('sections', [])
        print(f"📊 생성 결과:")
        print(f"   - 생성된 섹션 수: {len(sections)}")
        
        # 검증 결과
        validation = result.get('validation', {})
        if validation:
            print(f"   - 검증 결과:")
            print(f"     * 통과: {validation.get('passed', 0)}")
            print(f"     * 실패: {validation.get('failed', 0)}")
            
            if validation.get('errors'):
                print(f"     * 에러 목록:")
                for error in validation['errors'][:5]:  # 최대 5개만 표시
                    print(f"       - {error}")
        
        # 섹션 샘플 출력
        if sections:
            print(f"\n📋 섹션 샘플 (첫 번째 섹션):")
            first_section = sections[0]
            print(f"   - 제목: {first_section.get('title', 'N/A')}")
            print(f"   - 타입: {first_section.get('type', 'N/A')}")
            content_preview = first_section.get('content', '')[:100]
            print(f"   - 내용 미리보기: {content_preview}...")
    else:
        print("❌ 자동 제작 실패: 결과가 없습니다.")
        
except Exception as e:
    print(f"❌ 에러 발생: {e}")
    import traceback
    traceback.print_exc()
