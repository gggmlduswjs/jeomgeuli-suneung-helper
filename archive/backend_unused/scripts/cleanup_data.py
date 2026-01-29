"""
데이터 정리 스크립트
기존 파싱 데이터를 정리하고 재생성 준비
"""
import sys
from pathlib import Path
import shutil

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings


def cleanup_legacy_data():
    """레거시 데이터 정리 (과목별 디렉토리)"""
    legacy_dir = settings.API_DIR / "data" / "literature" / "lectures"
    
    if legacy_dir.exists():
        print(f"레거시 데이터 삭제: {legacy_dir}")
        shutil.rmtree(legacy_dir)
        print("✅ 레거시 데이터 삭제 완료")
    else:
        print("레거시 데이터 없음")


def cleanup_book_data(book_id: str):
    """교재별 데이터 정리"""
    book_dir = settings.API_DIR / "data" / "literature" / book_id
    
    if book_dir.exists():
        print(f"교재 데이터 삭제: {book_dir}")
        shutil.rmtree(book_dir)
        print(f"✅ 교재 데이터 삭제 완료: {book_id}")
    else:
        print(f"교재 데이터 없음: {book_id}")


def list_all_books():
    """모든 교재 디렉토리 목록"""
    literature_dir = settings.API_DIR / "data" / "literature"
    
    if not literature_dir.exists():
        print("literature 디렉토리가 없습니다.")
        return []
    
    books = []
    for item in literature_dir.iterdir():
        if item.is_dir() and item.name != "pdf" and item.name != "lectures":
            books.append(item.name)
    
    return books


def main():
    """메인 함수"""
    print("=" * 60)
    print("데이터 정리 스크립트")
    print("=" * 60)
    print()
    
    # 1. 레거시 데이터 확인
    legacy_dir = settings.API_DIR / "data" / "literature" / "lectures"
    if legacy_dir.exists():
        print(f"⚠️  레거시 데이터 발견: {legacy_dir}")
        response = input("삭제하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            cleanup_legacy_data()
        print()
    
    # 2. 교재별 데이터 확인
    books = list_all_books()
    if books:
        print(f"발견된 교재: {len(books)}개")
        for book_id in books:
            print(f"  - {book_id}")
        print()
        
        response = input("모든 교재 데이터를 삭제하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            for book_id in books:
                cleanup_book_data(book_id)
    else:
        print("교재 데이터 없음")
    
    print()
    print("=" * 60)
    print("정리 완료!")
    print("=" * 60)
    print()
    print("다음 단계:")
    print("1. 관리자 페이지에서 교재 재파싱")
    print("2. 또는 새로 교재 업로드")


if __name__ == "__main__":
    main()
