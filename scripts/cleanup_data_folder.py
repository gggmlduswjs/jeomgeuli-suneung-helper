"""
Data 폴더 정리 스크립트

1. curricula/ 폴더를 과목별로 정리
2. uploads/ 폴더의 오래된 임시 파일 삭제
3. pdfs/ 폴더의 중복 확장자 파일명 정리
"""
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def cleanup_curricula():
    """curricula 폴더를 과목별로 정리"""
    print("=" * 60)
    print("1. curricula 폴더 정리")
    print("=" * 60)
    
    curricula_dir = DATA_DIR / "curricula"
    if not curricula_dir.exists():
        print("curricula 폴더가 없습니다.")
        return
    
    # 과목별 폴더 매핑
    subject_map = {
        'korean': 'korean',
        'literature': 'korean',
        'math': 'math1',
        'math1': 'math1',
        'english': 'english',
    }
    
    # 루트의 JSON 파일 찾기
    json_files = list(curricula_dir.glob("cur_*.json"))
    
    if not json_files:
        print("정리할 JSON 파일이 없습니다.")
        return
    
    moved_count = 0
    for json_file in json_files:
        try:
            # JSON 파일 읽어서 과목 확인
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            subject = data.get('subject', '').lower()
            folder_name = subject_map.get(subject, 'general')
            
            # 과목별 폴더 생성
            target_dir = curricula_dir / folder_name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일 이동
            target_path = target_dir / json_file.name
            if target_path.exists():
                print(f"  [스킵] 이미 존재: {target_path}")
            else:
                shutil.move(str(json_file), str(target_path))
                print(f"  [이동] {json_file.name} → {folder_name}/")
                moved_count += 1
                
        except Exception as e:
            print(f"  [오류] {json_file.name}: {e}")
    
    print(f"\n총 {moved_count}개 파일 이동 완료")

def cleanup_uploads(days_old=7):
    """uploads 폴더의 오래된 임시 파일 삭제"""
    print("\n" + "=" * 60)
    print("2. uploads 폴더 임시 파일 정리")
    print("=" * 60)
    
    uploads_dir = DATA_DIR / "uploads"
    if not uploads_dir.exists():
        print("uploads 폴더가 없습니다.")
        return
    
    # 커리큘럼 생성 시 생성된 임시 파일 찾기 (cur_xxx_*.hwp, cur_xxx_*.pdf)
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    temp_files = []
    for pattern in ["cur_*_*.hwp", "cur_*_*.pdf"]:
        temp_files.extend(uploads_dir.glob(pattern))
    
    if not temp_files:
        print("정리할 임시 파일이 없습니다.")
        return
    
    deleted_count = 0
    total_size = 0
    
    for file_path in temp_files:
        try:
            # 파일 수정 시간 확인
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if mtime < cutoff_date:
                file_size = file_path.stat().st_size
                file_path.unlink()
                print(f"  [삭제] {file_path.name} ({file_size / 1024:.1f} KB, {mtime.strftime('%Y-%m-%d')})")
                deleted_count += 1
                total_size += file_size
        except Exception as e:
            print(f"  [오류] {file_path.name}: {e}")
    
    print(f"\n총 {deleted_count}개 파일 삭제 ({total_size / 1024 / 1024:.2f} MB)")

def cleanup_pdf_filenames():
    """pdfs 폴더의 중복 확장자 파일명 정리"""
    print("\n" + "=" * 60)
    print("3. pdfs 폴더 파일명 정리")
    print("=" * 60)
    
    pdfs_dir = DATA_DIR / "pdfs"
    if not pdfs_dir.exists():
        print("pdfs 폴더가 없습니다.")
        return
    
    # .pdf.pdf 확장자 파일 찾기
    duplicate_ext_files = list(pdfs_dir.glob("*.pdf.pdf"))
    
    if not duplicate_ext_files:
        print("정리할 파일이 없습니다.")
        return
    
    renamed_count = 0
    for file_path in duplicate_ext_files:
        try:
            # .pdf.pdf → .pdf
            new_name = file_path.name.replace('.pdf.pdf', '.pdf')
            new_path = file_path.parent / new_name
            
            if new_path.exists():
                print(f"  [스킵] 이미 존재: {new_name}")
            else:
                file_path.rename(new_path)
                print(f"  [이름변경] {file_path.name} → {new_name}")
                renamed_count += 1
        except Exception as e:
            print(f"  [오류] {file_path.name}: {e}")
    
    print(f"\n총 {renamed_count}개 파일 이름 변경 완료")

def main():
    """메인 함수"""
    print("Data 폴더 정리 시작")
    print(f"작업 디렉토리: {DATA_DIR}")
    print()
    
    # 1. curricula 폴더 정리
    cleanup_curricula()
    
    # 2. uploads 폴더 정리 (7일 이상 된 임시 파일 삭제)
    cleanup_uploads(days_old=7)
    
    # 3. pdfs 폴더 파일명 정리
    cleanup_pdf_filenames()
    
    print("\n" + "=" * 60)
    print("정리 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
