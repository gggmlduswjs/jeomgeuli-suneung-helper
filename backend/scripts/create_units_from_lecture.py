"""
lecture JSON 파일을 기반으로 Unit을 생성하는 스크립트
"""
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal
from app.db.models import Unit, Lesson, UnitType
from app.utils.id_generator import generate_unit_id


def load_lecture_json(lecture_file: Path) -> Dict:
    """lecture JSON 파일 로드"""
    with open(lecture_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_problem_file(problems_dir: Path, page: int, problem_id: str) -> Optional[Path]:
    """문제 파일 찾기"""
    pattern = f"problem_p{page:02d}_{problem_id}.json"
    matches = list(problems_dir.glob(pattern))
    if matches:
        return matches[0]
    return None


def load_problem_json(problem_file: Path) -> Dict:
    """문제 JSON 파일 로드"""
    with open(problem_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_content_file(content_dir: Path, page: int, content_id: str = "01") -> Optional[Path]:
    """Content JSON 파일 찾기"""
    pattern = f"content_p{page:02d}_{content_id}.json"
    matches = list(content_dir.glob(pattern))
    if matches:
        return matches[0]
    return None


def load_content_json(content_file: Path) -> Dict:
    """Content JSON 파일 로드"""
    with open(content_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_units_from_lecture(lecture_id: int, db: SessionLocal):
    """lecture JSON을 기반으로 Unit 생성"""
    # 경로 설정
    data_dir = project_root / "data" / "literature"
    lectures_dir = data_dir / "lectures"
    problems_dir = data_dir / "problems"
    content_dir = data_dir / "content"
    concepts_images_dir = data_dir / "concepts_images"
    content_images_dir = data_dir / "content_images"
    problems_images_dir = data_dir / "problems_images"
    
    # lecture JSON 파일 로드
    lecture_file = lectures_dir / f"lecture_{lecture_id:02d}.json"
    if not lecture_file.exists():
        print(f"[ERROR] Lecture 파일을 찾을 수 없습니다: {lecture_file}")
        return
    
    lecture_data = load_lecture_json(lecture_file)
    print(f"[Lecture {lecture_id}] 로드: {lecture_data.get('title', 'N/A')}")
    
    # Lesson 찾기 (lesson_literature_01 형식)
    lesson_id = f"lesson_literature_{lecture_id:02d}"
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    
    if not lesson:
        print(f"[ERROR] Lesson을 찾을 수 없습니다: {lesson_id}")
        print("   먼저 Lesson을 생성해주세요.")
        return
    
    print(f"[OK] Lesson 찾음: {lesson.title}")
    
    # 기존 Unit 삭제
    existing_units = db.query(Unit).filter(Unit.lesson_id == lesson_id).all()
    if existing_units:
        print(f"[WARN] 기존 Unit {len(existing_units)}개 발견. 삭제합니다...")
        for unit in existing_units:
            db.delete(unit)
        db.commit()
        print(f"[OK] 기존 Unit {len(existing_units)}개 삭제 완료")
    
    units_created = []
    order = 0
    
    # 1. Sections를 Unit으로 변환
    sections = lecture_data.get('sections', [])
    print(f"\n[Sections] 처리 중... ({len(sections)}개)")
    
    for section_idx, section in enumerate(sections):
        section_title = section.get('title', f'섹션 {section_idx + 1}')
        section_content = section.get('content', [])
        page = section.get('page', 0)
        
        # content JSON 파일에서 실제 내용 가져오기
        content_text = '\n'.join(section_content) if section_content else ''
        
        # content JSON 파일이 있으면 우선 사용
        image_path = None
        if page > 0:
            content_file = find_content_file(content_dir, page, "01")
            if content_file:
                try:
                    content_data = load_content_json(content_file)
                    content_text_list = content_data.get('text', [])
                    if content_text_list:
                        content_text = '\n'.join(content_text_list)
                        print(f"  [INFO] Content JSON 사용: {content_file.name}")
                    
                    # 이미지 경로 가져오기
                    image_path_from_json = content_data.get('image_path')
                    if image_path_from_json:
                        image_path = image_path_from_json
                    else:
                        # content_images에서 찾기
                        image_pattern = f"content_p{page:02d}_01.png"
                        image_matches = list(content_images_dir.glob(image_pattern))
                        if image_matches:
                            image_path = f"/api/data/literature/content_images/{image_matches[0].name}"
                except Exception as e:
                    print(f"  [WARN] Content JSON 로드 실패: {e}")
            
            # content JSON이 없으면 concepts_images에서 찾기
            if not image_path and page > 0:
                concept_pattern = f"concept_p{page:02d}_*.png"
                concept_matches = list(concepts_images_dir.glob(concept_pattern))
                if concept_matches:
                    # 첫 번째 매칭 이미지 사용
                    image_path = f"/api/data/literature/concepts_images/{concept_matches[0].name}"
        
        if not content_text.strip():
            print(f"  [SKIP] 빈 섹션: {section_title}")
            continue
        
        # Unit 생성
        unit_id = generate_unit_id(lesson_id, order)
        unit = Unit(
            unit_id=unit_id,
            lesson_id=lesson_id,
            type=UnitType.CONCEPT_CONTENT,
            title=section_title,
            order=order,
            content_text=content_text,
            braille_text=None,  # 나중에 생성
            image_path=image_path,
        )
        
        db.add(unit)
        units_created.append(unit)
        order += 1
        
        print(f"  [OK] Unit 생성: {section_title[:50]}... (order: {order})")
    
    # 2. Problems를 Unit으로 변환
    problems = lecture_data.get('problems', [])
    print(f"\n[Problems] 처리 중... ({len(problems)}개)")
    
    for problem_idx, problem_id in enumerate(problems):
        # 문제 파일 찾기 (페이지 정보 필요)
        # lecture의 sections에서 페이지 범위 추정
        problem_page = 0
        problem_file = None
        
        if sections:
            # 모든 섹션의 페이지 수집
            pages = [s.get('page', 0) for s in sections if s.get('page', 0) > 0]
            if pages:
                # 문제는 보통 섹션 다음 페이지에 위치
                # 섹션 페이지 범위 내에서 찾기
                min_page = min(pages)
                max_page = max(pages)
                
                # 먼저 예상 페이지에서 찾기
                problem_page = max_page
                problem_file = find_problem_file(problems_dir, problem_page, problem_id)
                
                # 찾지 못하면 주변 페이지에서 검색 (max_page ± 3 범위)
                if not problem_file:
                    for search_page in range(max(min_page, max_page - 3), max_page + 4):
                        problem_file = find_problem_file(problems_dir, search_page, problem_id)
                        if problem_file:
                            problem_page = search_page
                            print(f"  [INFO] 문제 {problem_id}를 페이지 {search_page}에서 찾음")
                            break
                
                # 여전히 못 찾으면 모든 페이지에서 검색
                if not problem_file:
                    all_problem_files = list(problems_dir.glob(f"problem_p*_{problem_id}.json"))
                    if all_problem_files:
                        # 파일명에서 페이지 추출
                        for pf in all_problem_files:
                            match = re.search(r'problem_p(\d+)_', pf.name)
                            if match:
                                problem_page = int(match.group(1))
                                problem_file = pf
                                print(f"  [INFO] 문제 {problem_id}를 페이지 {problem_page}에서 찾음 (전체 검색)")
                                break
            else:
                problem_page = sections[-1].get('page', 0) if sections else 0
                problem_file = find_problem_file(problems_dir, problem_page, problem_id)
        
        # 문제 데이터 로드
        question_stem = f"문제 {problem_id} (페이지 {problem_page})"
        question_choices = []
        question_answer = None
        problem_content_text = None
        
        if problem_file:
            try:
                problem_data = load_problem_json(problem_file)
                
                # 문제 지문 추출
                question_text = problem_data.get('question_text', '')
                full_text = problem_data.get('full_text', '')
                content_list = problem_data.get('content', [])
                
                if question_text:
                    question_stem = question_text
                elif full_text:
                    # full_text에서 선택지 제거하여 지문만 추출
                    # 선택지 패턴 제거
                    stem_text = re.sub(r'[①②③④⑤]\s*[^\n]*', '', full_text).strip()
                    if stem_text:
                        question_stem = stem_text
                elif content_list:
                    # content 리스트를 합쳐서 지문으로 사용
                    question_stem = '\n'.join(str(c) for c in content_list if c)
                
                # 선택지 추출
                choices_dict = problem_data.get('choices', {})
                if choices_dict:
                    # 딕셔너리를 리스트로 변환 (순서 보장)
                    sorted_keys = sorted(choices_dict.keys(), key=lambda x: int(x) if x.isdigit() else 999)
                    question_choices = [choices_dict[key] for key in sorted_keys if choices_dict[key]]
                
                # 정답 추출
                question_answer = problem_data.get('answer')
                
                # 본문 텍스트 (지문용)
                if content_list:
                    problem_content_text = '\n'.join(str(c) for c in content_list if c)
                elif full_text:
                    problem_content_text = full_text
                
                print(f"  [INFO] 문제 데이터 로드: {problem_file.name}")
            except Exception as e:
                print(f"  [WARN] 문제 JSON 로드 실패: {e}")
        
        # 문제 이미지 찾기
        problem_image_path = None
        if problem_page > 0:
            problem_image_pattern = f"problem_p{problem_page:02d}_{problem_id}.png"
            problem_image_matches = list(problems_images_dir.glob(problem_image_pattern))
            if problem_image_matches:
                problem_image_path = f"/api/data/literature/problems_images/{problem_image_matches[0].name}"
        
        # Unit 생성
        unit_id = generate_unit_id(lesson_id, order)
        unit = Unit(
            unit_id=unit_id,
            lesson_id=lesson_id,
            type=UnitType.QUESTION,
            title=f"문제 {problem_id}",
            order=order,
            content_text=problem_content_text,  # 지문 텍스트
            braille_text=None,
            image_path=problem_image_path,
            question_stem=question_stem,
            question_choices=json.dumps(question_choices, ensure_ascii=False) if question_choices else json.dumps([], ensure_ascii=False),
            question_answer=question_answer,
        )
        
        db.add(unit)
        units_created.append(unit)
        order += 1
        
        if problem_file:
            print(f"  [OK] Unit 생성: 문제 {problem_id} (페이지 {problem_page}, 파일: {problem_file.name})")
        else:
            print(f"  [WARN] Unit 생성: 문제 {problem_id} (페이지 {problem_page}, 파일 없음)")
    
    # 커밋
    try:
        db.commit()
        print(f"\n[SUCCESS] 총 {len(units_created)}개의 Unit이 생성되었습니다.")
        print(f"   - Sections: {len(sections)}개")
        print(f"   - Problems: {len(problems)}개")
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Unit 생성 실패: {e}")
        raise


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python create_units_from_lecture.py <lecture_id>")
        print("예: python create_units_from_lecture.py 1")
        sys.exit(1)
    
    try:
        lecture_id = int(sys.argv[1])
    except ValueError:
        print("[ERROR] lecture_id는 숫자여야 합니다.")
        sys.exit(1)
    
    # DB 세션 생성
    db = SessionLocal()
    
    try:
        create_units_from_lecture(lecture_id, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
