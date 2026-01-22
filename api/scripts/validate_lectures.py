"""
lectures 데이터 검증 스크립트
"""
import json
import os
from pathlib import Path

def main():
    lectures_dir = Path("api/data/literature/lectures")
    
    # lectures.json 읽기
    lectures_json = lectures_dir / "lectures.json"
    with open(lectures_json, "r", encoding="utf-8") as f:
        lectures_list = json.load(f)
    
    print("=" * 80)
    print("Lectures 데이터 검증")
    print("=" * 80)
    print()
    print(f"lectures.json 항목 수: {len(lectures_list)}")
    print()
    
    # lecture_id 중복 확인
    lecture_ids = {}
    duplicates = []
    for lecture in lectures_list:
        lid = lecture.get("lecture_id")
        if lid in lecture_ids:
            duplicates.append(lid)
        lecture_ids[lid] = lecture_ids.get(lid, 0) + 1
    
    if duplicates:
        print(f"[경고] 중복된 lecture_id: {len(set(duplicates))}개")
        print(f"  중복 ID: {sorted(set(duplicates))[:10]}")
    else:
        print("[OK] lecture_id 중복 없음")
    print()
    
    # 개별 lecture 파일 확인
    lecture_files = sorted([f for f in os.listdir(lectures_dir) 
                           if f.startswith("lecture_") and f.endswith(".json") 
                           and f != "lectures.json"])
    
    print(f"개별 lecture 파일 수: {len(lecture_files)}")
    print()
    
    # 통계
    total_sections = 0
    empty_sections = 0
    sections_with_content = 0
    total_problems = 0
    lectures_with_empty_sections = []
    lectures_without_sections = []
    
    for lecture_file in lecture_files:
        file_path = lectures_dir / lecture_file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        sections = data.get("sections", [])
        problems = data.get("problems", [])
        
        total_sections += len(sections)
        total_problems += len(problems)
        
        if not sections:
            lectures_without_sections.append(lecture_file)
        
        for section in sections:
            content = section.get("content", [])
            if not content or (isinstance(content, list) and len(content) == 0):
                empty_sections += 1
            else:
                sections_with_content += 1
        
        if sections and all(not s.get("content") or 
                           (isinstance(s.get("content"), list) and len(s.get("content", [])) == 0) 
                           for s in sections):
            lectures_with_empty_sections.append((lecture_file, data.get("title", "N/A")))
    
    print("=" * 80)
    print("통계")
    print("=" * 80)
    print(f"총 섹션 수: {total_sections}")
    print(f"  - 내용 있는 섹션: {sections_with_content}")
    print(f"  - 내용 없는 섹션: {empty_sections}")
    print(f"총 문제 수: {total_problems}")
    print()
    
    if lectures_without_sections:
        print(f"[경고] 섹션이 없는 강의: {len(lectures_without_sections)}개")
        for f in lectures_without_sections[:5]:
            print(f"  - {f}")
        print()
    
    if lectures_with_empty_sections:
        print(f"[경고] 모든 섹션이 비어있는 강의: {len(lectures_with_empty_sections)}개")
        for f, title in lectures_with_empty_sections[:10]:
            print(f"  - {f}: {title[:50]}")
        if len(lectures_with_empty_sections) > 10:
            print(f"  ... 외 {len(lectures_with_empty_sections) - 10}개")
        print()
    
    # 샘플 확인
    print("=" * 80)
    print("샘플 확인")
    print("=" * 80)
    
    # 잘 된 예시
    good_examples = []
    for lecture_file in lecture_files[:20]:
        file_path = lectures_dir / lecture_file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        sections = data.get("sections", [])
        has_content = any(s.get("content") and 
                          (not isinstance(s.get("content"), list) or len(s.get("content", [])) > 0)
                          for s in sections)
        
        if has_content and sections:
            good_examples.append((lecture_file, data.get("title", "N/A"), len(sections)))
            if len(good_examples) >= 3:
                break
    
    if good_examples:
        print("\n[OK] 내용이 잘 추출된 강의 예시:")
        for f, title, sec_count in good_examples:
            print(f"  - {f}: {title[:50]} ({sec_count}개 섹션)")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
