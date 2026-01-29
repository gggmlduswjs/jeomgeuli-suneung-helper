"""
데이터 확인 스크립트
현재 생성된 데이터 구조 확인
"""
import sys
from pathlib import Path
import json

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings


def check_legacy_data():
    """레거시 데이터 확인"""
    legacy_dir = settings.API_DIR / "data" / "literature" / "lectures"
    
    if not legacy_dir.exists():
        print("[INFO] 레거시 데이터 없음")
        return
    
    print("=" * 60)
    print("레거시 데이터 (과목별)")
    print("=" * 60)
    print(f"경로: {legacy_dir}")
    print()
    
    # lectures.json 확인
    lectures_json = legacy_dir / "lectures.json"
    if lectures_json.exists():
        with open(lectures_json, 'r', encoding='utf-8') as f:
            lectures = json.load(f)
        print(f"강의 수: {len(lectures)}개")
        
        # 첫 번째 강의 확인
        if lectures:
            first_lecture_id = lectures[0].get('lecture_id', 1)
            lecture_file = legacy_dir / f"lecture_{first_lecture_id:02d}.json"
            if lecture_file.exists():
                with open(lecture_file, 'r', encoding='utf-8') as f:
                    lecture = json.load(f)
                print(f"첫 번째 강의: {lecture.get('title')}")
                print(f"  - 섹션 수: {len(lecture.get('sections', []))}")
                print(f"  - 문제 수: {len(lecture.get('problems', []))}")
                
                if lecture.get('sections'):
                    print("  - 섹션 목록:")
                    for section in lecture['sections']:
                        print(f"    • {section.get('title')} ({section.get('type')})")
                else:
                    print("  ⚠️  섹션이 비어있습니다!")
    else:
        print("lectures.json 없음")
    
    print()


def check_book_data(book_id: str):
    """교재별 데이터 확인"""
    book_dir = settings.API_DIR / "data" / "literature" / book_id
    
    if not book_dir.exists():
        print(f"[INFO] 교재 데이터 없음: {book_id}")
        return
    
    print("=" * 60)
    print(f"교재 데이터: {book_id}")
    print("=" * 60)
    print(f"경로: {book_dir}")
    print()
    
    # 디렉토리 구조 확인
    lectures_dir = book_dir / "lectures"
    concepts_dir = book_dir / "concepts_images"
    content_dir = book_dir / "content_images"
    problems_dir = book_dir / "problems_images"
    
    print("디렉토리 구조:")
    print(f"  - lectures: {'[OK]' if lectures_dir.exists() else '[MISSING]'}")
    print(f"  - concepts_images: {'[OK]' if concepts_dir.exists() else '[MISSING]'}")
    print(f"  - content_images: {'[OK]' if content_dir.exists() else '[MISSING]'}")
    print(f"  - problems_images: {'[OK]' if problems_dir.exists() else '[MISSING]'}")
    print()
    
    # 강의 데이터 확인
    if lectures_dir.exists():
        lectures_json = lectures_dir / "lectures.json"
        if lectures_json.exists():
            with open(lectures_json, 'r', encoding='utf-8') as f:
                lectures = json.load(f)
            print(f"강의 수: {len(lectures)}개")
            
            # 첫 번째 강의 확인
            if lectures:
                first_lecture_id = lectures[0].get('lecture_id', 1)
                lecture_file = lectures_dir / f"lecture_{first_lecture_id:02d}.json"
                if lecture_file.exists():
                    with open(lecture_file, 'r', encoding='utf-8') as f:
                        lecture = json.load(f)
                    print(f"첫 번째 강의: {lecture.get('title')}")
                    print(f"  - 섹션 수: {len(lecture.get('sections', []))}")
                    print(f"  - 문제 수: {len(lecture.get('problems', []))}")
                    
                    if lecture.get('sections'):
                        print("  - 섹션 목록:")
                        for section in lecture['sections']:
                            print(f"    • {section.get('title')} ({section.get('type')})")
                    else:
                        print("  ⚠️  섹션이 비어있습니다!")
    
    # 이미지 확인
    if concepts_dir.exists():
        images = list(concepts_dir.glob("*.png"))
        print(f"  - 개념 이미지: {len(images)}개")
    if content_dir.exists():
        images = list(content_dir.glob("*.png"))
        print(f"  - 본문 이미지: {len(images)}개")
    if problems_dir.exists():
        images = list(problems_dir.glob("*.png"))
        print(f"  - 문제 이미지: {len(images)}개")
    
    print()


def list_all_books():
    """모든 교재 디렉토리 목록"""
    literature_dir = settings.API_DIR / "data" / "literature"
    
    if not literature_dir.exists():
        return []
    
    books = []
    for item in literature_dir.iterdir():
        if item.is_dir() and item.name != "pdf" and item.name != "lectures":
            books.append(item.name)
    
    return books


def main():
    """메인 함수"""
    print("=" * 60)
    print("데이터 구조 확인")
    print("=" * 60)
    print()
    
    # 1. 레거시 데이터 확인
    check_legacy_data()
    
    # 2. 교재별 데이터 확인
    books = list_all_books()
    if books:
        print(f"발견된 교재: {len(books)}개")
        print()
        for book_id in books:
            check_book_data(book_id)
    else:
        print("교재 데이터 없음")
    
    print()
    print("=" * 60)
    print("확인 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
