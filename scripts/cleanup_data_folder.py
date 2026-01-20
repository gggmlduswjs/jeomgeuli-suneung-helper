"""
Data 폴더 정리 스크립트

1. uploads/ 폴더의 오래된 임시 파일 삭제
2. pdfs/ 폴더의 중복 확장자 파일명 정리

참고: curricula/ 폴더 정리는 더 이상 사용되지 않습니다 (DB에 저장됨).
"""
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def cleanup_uploads(days_old=7):
    """uploads 폴더의 오래된 임시 파일 삭제"""
    print("=" * 60)
    print("1. uploads 폴더 임시 파일 정리")
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
    print("2. pdfs 폴더 파일명 정리")
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
    
    # 1. uploads 폴더 정리 (7일 이상 된 임시 파일 삭제)
    cleanup_uploads(days_old=7)
    
    # 2. pdfs 폴더 파일명 정리
    cleanup_pdf_filenames()
    
    print("\n" + "=" * 60)
    print("정리 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
