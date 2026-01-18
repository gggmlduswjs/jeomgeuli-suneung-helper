"""
한글 파일 추출 빠른 테스트 스크립트
"""
from pathlib import Path
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services.hwp_extract import (
    extract_text_from_hwp,
    extract_structure_from_hwp,
    extract_lesson_info_from_filename
)
from app.services.content_auto_generator import ContentAutoGenerator
from app.services.braille_convert import text_to_braille

def test_hwp_extract(hwp_path: Path):
    """한글 파일 텍스트 추출 테스트"""
    print("=== 한글 파일 텍스트 추출 테스트 ===")
    print(f"파일: {hwp_path.name}\n")
    
    if not hwp_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {hwp_path}")
        return False
    
    # 텍스트 추출
    text = extract_text_from_hwp(hwp_path)
    
    if text:
        print(f"✅ 텍스트 추출 성공!")
        print(f"  - 텍스트 길이: {len(text)} 문자")
        print(f"  - 첫 200자:\n    {text[:200]}...\n")
        
        # 점자 변환 테스트
        braille = text_to_braille(text[:100])
        print(f"  - 점자 변환 샘플 (100자): {braille[:50]}...\n")
        
        return True
    else:
        print("❌ 텍스트 추출 실패")
        return False

def test_hwp_structure(hwp_path: Path):
    """한글 파일 구조 추출 테스트"""
    print("=== 한글 파일 구조 추출 테스트 ===")
    
    structure = extract_structure_from_hwp(hwp_path)
    
    if structure:
        print(f"✅ 구조 추출 성공!")
        print(f"  - 섹션 수: {len(structure.get('sections', []))}")
        print(f"  - 메타데이터: {structure.get('metadata', {})}\n")
        return True
    else:
        print("❌ 구조 추출 실패\n")
        return False

def test_lesson_info(filename: str):
    """파일명에서 레슨 정보 추출 테스트"""
    print("=== 레슨 정보 추출 테스트 ===")
    print(f"파일명: {filename}\n")
    
    info = extract_lesson_info_from_filename(filename)
    
    if info:
        print(f"✅ 정보 추출 성공!")
        print(f"  - 레슨 번호: {info.get('lesson_number')}")
        print(f"  - 카테고리: {info.get('category')}")
        print(f"  - 난이도: {info.get('difficulty')}\n")
        return True
    else:
        print("❌ 정보 추출 실패\n")
        return False

def test_content_generator(hwp_path: Path):
    """자동 제작 시스템 테스트"""
    print("=== 자동 제작 시스템 테스트 ===")
    
    generator = ContentAutoGenerator()
    result = generator.generate_structured_content(hwp_path)
    
    if result:
        print(f"✅ 자동 제작 성공!")
        print(f"  - 생성된 섹션 수: {len(result.get('sections', []))}")
        
        validation = result.get('validation', {})
        print(f"  - 검증 결과:")
        print(f"    * 통과: {validation.get('passed', 0)}")
        print(f"    * 실패: {validation.get('failed', 0)}")
        
        if validation.get('errors'):
            print(f"    * 에러:")
            for error in validation['errors'][:3]:
                print(f"      - {error}")
        
        print()
        return True
    else:
        print("❌ 자동 제작 실패\n")
        return False

if __name__ == "__main__":
    # 한글 파일 경로
    hwp_dir = Path(__file__).parent.parent / "data" / "lecture_scripts"
    
    # 과목별 폴더 찾기
    subject_dirs = [d for d in hwp_dir.iterdir() if d.is_dir()]
    
    if not subject_dirs:
        print(f"❌ 한글 파일을 찾을 수 없습니다: {hwp_dir}")
        print("   data/lecture_scripts/[과목명]/ 폴더에 한글 파일을 배치하세요.")
        sys.exit(1)
    
    # 문학 폴더 우선 선택, 없으면 첫 번째 폴더
    subject_dir = None
    for dir in subject_dirs:
        if "문학" in dir.name:
            subject_dir = dir
            break
    
    if not subject_dir:
        subject_dir = subject_dirs[0]
    hwp_files = list(subject_dir.glob("*.hwp"))
    
    if not hwp_files:
        print(f"❌ {subject_dir.name} 폴더에 한글 파일이 없습니다.")
        sys.exit(1)
    
    test_file = hwp_files[0]
    print(f"테스트 파일: {test_file.name}")
    print(f"과목: {subject_dir.name}\n")
    
    # 테스트 실행
    success = True
    success &= test_hwp_extract(test_file)
    success &= test_lesson_info(test_file.name)
    success &= test_hwp_structure(test_file)
    success &= test_content_generator(test_file)
    
    print("="*50)
    if success:
        print("✅ 모든 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
        sys.exit(1)
