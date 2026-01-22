"""
파이프라인 진행 상황 확인 스크립트
"""
import json
import os
from pathlib import Path

def main():
    lectures_dir = Path("api/data/literature/lectures")
    
    print("=" * 80)
    print("파이프라인 진행 상황")
    print("=" * 80)
    print()
    
    # lectures.json 확인
    lectures_json = lectures_dir / "lectures.json"
    if lectures_json.exists():
        with open(lectures_json, "r", encoding="utf-8") as f:
            lectures_list = json.load(f)
        print(f"[lectures.json] {len(lectures_list)}개 강의")
    else:
        print("[lectures.json] 아직 생성되지 않음")
        lectures_list = []
    
    # 개별 lecture 파일 확인
    lecture_files = sorted([f for f in os.listdir(lectures_dir) 
                           if f.startswith("lecture_") and f.endswith(".json") 
                           and f != "lectures.json"])
    
    print(f"[lecture_XX.json] {len(lecture_files)}개 파일")
    print()
    
    if lecture_files:
        # 샘플 확인
        print("샘플 파일 확인:")
        for f in lecture_files[:5]:
            file_path = lectures_dir / f
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            sections = data.get("sections", [])
            sections_with_content = sum(1 for s in sections if s.get("content") and len(s.get("content", [])) > 0)
            total_content_items = sum(len(s.get("content", [])) for s in sections)
            
            print(f"  {f}:")
            print(f"    - 제목: {data.get('title', 'N/A')[:50]}")
            print(f"    - 섹션: {len(sections)}개 (내용 있는 섹션: {sections_with_content}개)")
            print(f"    - 총 content 항목: {total_content_items}개")
        
        if len(lecture_files) > 5:
            print(f"  ... 외 {len(lecture_files) - 5}개 파일")
    
    print()
    print("=" * 80)
    
    # 통계
    if lecture_files:
        total_sections = 0
        sections_with_content = 0
        total_content_items = 0
        
        for f in lecture_files:
            file_path = lectures_dir / f
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            sections = data.get("sections", [])
            total_sections += len(sections)
            
            for s in sections:
                content = s.get("content", [])
                if content and len(content) > 0:
                    sections_with_content += 1
                    total_content_items += len(content)
        
        print("전체 통계:")
        print(f"  - 총 섹션: {total_sections}개")
        print(f"  - 내용 있는 섹션: {sections_with_content}개 ({sections_with_content/total_sections*100:.1f}%)")
        print(f"  - 총 content 항목: {total_content_items}개")
        print()
    
    print("=" * 80)

if __name__ == "__main__":
    main()
