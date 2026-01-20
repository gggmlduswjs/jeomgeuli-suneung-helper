"""
교재 관련 라우터
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from pathlib import Path

from app.db.session import get_db
from app.db.models import Book, ParseStatus, Subject
from app.schemas.book import BookCreate, BookResponse, BookParseStatusResponse
from app.core.config import settings
# HWP 관련 함수들 (삭제된 모듈 대체용)
try:
    from app.services.hwp_extract import (
        extract_text_from_hwp,
        extract_lesson_info_from_filename,
        extract_structure_from_hwp
    )
except ImportError:
    # hwp_extract 모듈이 없는 경우 stub 함수 제공
    def extract_text_from_hwp(file_path: Path) -> str:
        raise HTTPException(status_code=501, detail="HWP 파일 처리가 지원되지 않습니다.")
    
    def extract_lesson_info_from_filename(filename: str) -> dict:
        return {}
    
    def extract_structure_from_hwp(file_path: Path) -> dict:
        return {}
from app.utils.id_generator import generate_lesson_id, generate_book_id
from app.db.models import Lesson, Curriculum, LearningUnit, CurriculumStatus
import json

# ML 기반 섹션 분류기 (선택적)
try:
    from app.services.ml_section_classifier import get_section_classifier
    ML_CLASSIFIER_AVAILABLE = True
except ImportError as e:
    ML_CLASSIFIER_AVAILABLE = False
    print(f"[books] ML 섹션 분류기 로드 실패: {e}")


def _subject_to_pipeline_subject(subject: Subject) -> str:
    """Subject enum을 textbook_pipeline의 subject 형식으로 변환"""
    mapping = {
        Subject.KOREAN: "literature",
        Subject.MATH: "math1",
        Subject.ENGLISH: "english",
    }
    return mapping.get(subject, "literature")


def _create_curriculum_from_pipeline(
    book_id: Optional[str],
    subject_enum: Subject,
    pipeline_subject: str,
    title: str,
    db: Session
) -> str:
    """파이프라인 결과를 커리큘럼으로 변환"""
    from app.core.config import settings
    
    # 커리큘럼 ID 생성
    curriculum_id = f"cur_{uuid.uuid4().hex[:12]}"
    
    # 파이프라인 데이터 경로
    data_dir = settings.API_DIR / "data" / pipeline_subject
    lectures_dir = data_dir / "lectures"
    lectures_json = lectures_dir / "lectures.json"
    
    if not lectures_json.exists():
        print(f"[books] 경고: lectures.json을 찾을 수 없음: {lectures_json}")
        return curriculum_id
    
    # lectures.json 읽기
    with open(lectures_json, "r", encoding="utf-8") as f:
        lectures = json.load(f)
    
    if not isinstance(lectures, list):
        lectures = lectures.get("lectures", [])
    
    if not lectures:
        print(f"[books] 경고: 강의 데이터가 없음")
        return curriculum_id
    
    # 커리큘럼 생성 (book_id가 None일 수 있음)
    curriculum = Curriculum(
        curriculum_id=curriculum_id,
        book_id=book_id,  # None일 수 있음
        subject=subject_enum,
        title=title,
        status=CurriculumStatus.DONE,
        lesson_count=len(lectures),
    )
    db.add(curriculum)
    db.commit()
    db.refresh(curriculum)
    
    # 각 강의(lecture)를 레슨(lesson)으로 변환
    # lecture_data의 title을 레슨 제목으로 사용하고, sections를 학습 단위로 변환
    for lecture in lectures:
        lecture_id = lecture.get("lecture_id", 0)
        lecture_number = lecture.get("lecture_number", lecture_id)
        
        # 강의 상세 파일 읽기
        lecture_file = lectures_dir / f"lecture_{lecture_id:02d}.json"
        if not lecture_file.exists():
            print(f"[books] 경고: 강의 파일을 찾을 수 없음: {lecture_file}")
            continue
        
        with open(lecture_file, "r", encoding="utf-8") as f:
            lecture_data = json.load(f)
        
        # lecture_data.title을 레슨 제목으로 사용 (예: "1강 | 시의 표현과 형식 >>> 고전 시가")
        lecture_title = lecture_data.get("title", f"{lecture_number}강")
        
        # 강의 제목 검증: 반드시 "N강" 형식이어야 함 (문제 번호/지문 제외)
        import re
        lecture_title_match = re.search(r'^(\d+)강', lecture_title)
        if not lecture_title_match:
            # "N강" 형식이 아니면 문제 번호나 지문일 가능성이 높음
            print(f"[books] 경고: 강의 {lecture_id}의 제목이 'N강' 형식이 아님: '{lecture_title[:50]}' - 건너뜀")
            continue
        
        # 문제/해설 페이지에서 추출된 잘못된 강의 제목 필터링
        # 예: "03 주제 슬픔의 승화를...", "01 간을 옮긴 이유도..." 등
        if re.match(r'^\d{2,}\s+[가-힣]{5,}', lecture_title) and not re.search(r'^\d+강', lecture_title):
            # 2자리 이상 숫자로 시작하고 한글이 5자 이상이고 "N강" 형식이 아니면 문제 지문일 가능성
            print(f"[books] 경고: 강의 {lecture_id}의 제목이 문제 지문으로 보임: '{lecture_title[:50]}' - 건너뜀")
            continue
        
        # 문제 번호 형식 제외 (예: "04 웅적 활약", "04 정보를 제공해 주기도 한다...")
        if re.match(r'^\d{2,}\s+[가-힣]{1,4}', lecture_title) and not re.search(r'^\d+강', lecture_title):
            # 2자리 이상 숫자로 시작하고 한글이 4자 이하이고 "N강" 형식이 아니면 문제 번호일 가능성
            print(f"[books] 경고: 강의 {lecture_id}의 제목이 문제 번호로 보임: '{lecture_title[:50]}' - 건너뜀")
            continue
        
        sections = lecture_data.get("sections", [])
        problems = lecture_data.get("problems", [])  # 문제 목록 추가
        
        if not sections and not problems:
            print(f"[books] 경고: 강의 {lecture_id}에 섹션이나 문제가 없음")
            continue
        
        # 섹션 인덱스 추적 (본문/문제 추가 시에도 순서 유지)
        # 실제 DB에 저장되는 순서를 추적
        actual_unit_index = 0
        
        # 각 섹션을 이미지 단위로 학습 단위 변환
        print(f"[books] 강의 {lecture_id} ({lecture_number}강): 섹션 {len(sections)}개, 문제 {len(problems)}개 발견")
        
        # 이미지 디렉토리 경로
        from app.core.config import settings
        data_dir = settings.API_DIR / "data" / pipeline_subject
        concepts_dir = data_dir / "concepts_images"
        content_dir = data_dir / "content_images"
        problems_dir = data_dir / "problems_images"
        
        for idx, section in enumerate(sections):
            unit_id = f"lu_{uuid.uuid4().hex[:12]}"
            print(f"[books]   섹션 {idx}: type={section.get('type', 'general')}, title={section.get('title', 'N/A')[:50]}")
            
            # section_type 추출 (ML 기반 분류 우선, Fallback: 정규식)
            section_type = section.get("type", "general")
            if section_type == "general":
                # ML 기반 섹션 타입 분류 시도
                if ML_CLASSIFIER_AVAILABLE:
                    try:
                        classifier = get_section_classifier()
                        section_title = section.get("title", "")
                        section_content_text = content_text if isinstance(content_text, str) else "\n".join(str(line) for line in content_text) if isinstance(content_text, list) else ""
                        
                        classification_result = classifier.classify_section_type(
                            title=section_title,
                            content=section_content_text[:1000],  # 처음 1000자만 사용 (성능 최적화)
                            threshold=0.5
                        )
                        
                        if classification_result["confidence"] >= 0.5:
                            section_type = classification_result["section_type"]
                            print(f"[books]   ML 분류: '{section_title[:30]}' -> {section_type} (신뢰도: {classification_result['confidence']:.2f})")
                        else:
                            # 신뢰도가 낮으면 정규식 기반 분류로 Fallback
                            section_type = classification_result["section_type"]
                    except Exception as e:
                        print(f"[books]   ML 섹션 분류 실패, 정규식 사용: {e}")
                        section_type = "general"
                
                # ML 분류 실패 시 정규식 기반 분류 (Fallback)
                if section_type == "general" and section.get("title"):
                    title_lower = section.get("title", "").lower()
                    if "개념" in title_lower or "concept" in title_lower:
                        section_type = "concept"
                    elif "예시" in title_lower or "example" in title_lower:
                        section_type = "example"
                    elif "문제" in title_lower or "problem" in title_lower:
                        section_type = "problem"
                    elif "전략" in title_lower or "strategy" in title_lower:
                        section_type = "strategy"
                    elif "오리엔테이션" in title_lower or "ot" in title_lower:
                        section_type = "ot"
            
            # content에서 작품(시/산문)이 포함되어 있는지 확인
            # 작품은 보통 "- 작가명, 「작품명」" 형식으로 끝나거나, 시적 표현이 포함됨
            content_text = section.get("content", "")
            if isinstance(content_text, list):
                content_text = "\n".join(str(line) for line in content_text)
            
            # 작품 감지: ML 기반 감지 우선, Fallback: 정규식
            is_work = False
            work_start_idx_ml = None
            
            if isinstance(content_text, str):
                # ML 기반 작품 감지 시도
                if ML_CLASSIFIER_AVAILABLE:
                    try:
                        classifier = get_section_classifier()
                        work_detection = classifier.detect_work_content(
                            content=content_text[:2000],  # 처음 2000자만 사용
                            threshold=0.6
                        )
                        
                        if work_detection["is_work"]:
                            is_work = True
                            work_start_idx_ml = work_detection.get("work_start_index")
                            print(f"[books]   작품 감지 (ML): {section.get('title', 'N/A')[:50]} (신뢰도: {work_detection['confidence']:.2f})")
                    except Exception as e:
                        print(f"[books]   ML 작품 감지 실패, 정규식 사용: {e}")
                
                # ML 감지 실패 시 정규식 기반 감지 (Fallback)
                if not is_work:
                    import re
                    # 작가명 패턴: "- 박두진, 「해」" 같은 형식
                    work_pattern = r'-\s*[가-힣\s]+,?\s*「[가-힣\s]+」'
                    if re.search(work_pattern, content_text):
                        is_work = True
                        print(f"[books]   작품 감지 (작가명 패턴): {section.get('title', 'N/A')[:50]}")
                    # 또는 content가 시적 표현(반복, 운율 등)을 포함하는 경우
                    elif any(keyword in content_text for keyword in ["해야", "솟아라", "고운", "청산"]):
                        # 시적 반복 패턴 확인
                        if content_text.count("해야") > 2 or content_text.count("솟아라") > 2:
                            is_work = True
                            print(f"[books]   작품 감지 (시적 표현): {section.get('title', 'N/A')[:50]} (해야: {content_text.count('해야')}, 솟아라: {content_text.count('솟아라')})")
            
            # content_raw 먼저 가져오기 (작품 분리 전에)
            content_raw = section.get("content", "")
            content = None  # content 초기화
            work_added = False  # 작품 섹션이 추가되었는지 추적
            
            # 작품이 포함된 경우 별도의 "content" 섹션으로 분리
            if is_work and section_type != "content":
                # 원본 섹션은 개념 설명 부분만 남기고, 작품은 별도 섹션으로 분리
                # 작품 시작 부분 찾기 (ML 결과 우선, Fallback: 정규식)
                content_lines = section.get("content", [])
                if isinstance(content_lines, list):
                    work_start_idx = work_start_idx_ml  # ML에서 감지한 인덱스 사용
                    
                    # ML에서 감지하지 못한 경우 정규식 기반 탐색
                    if work_start_idx is None:
                        for i, line in enumerate(content_lines):
                            if isinstance(line, str) and ("해야 솟아라" in line or "해야," in line or "-" in line and "「" in line):
                                work_start_idx = i
                                break
                    
                    if work_start_idx is not None and work_start_idx > 0:
                        # 개념 부분과 작품 부분 분리
                        concept_content = content_lines[:work_start_idx]
                        work_content = content_lines[work_start_idx:]
                        
                        print(f"[books]   작품 분리: work_start_idx={work_start_idx}, 개념 줄 수={len(concept_content)}, 작품 줄 수={len(work_content)}")
                        
                        # 원본 섹션은 개념 부분만 저장
                        content = "\n".join(str(line) for line in concept_content) if concept_content else ""
                        
                        # 작품 섹션 추가 (원본 섹션 저장 전에)
                        work_unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                        work_content_str = "\n".join(str(line) for line in work_content)
                        
                        # 작품 제목 추출 (마지막 줄에서)
                        work_title = section.get("title", f"{lecture_number}강 본문")
                        if work_content:
                            last_line = str(work_content[-1])
                            if "-" in last_line and "「" in last_line:
                                # "- 박두진, 「해」" 형식에서 작품명 추출
                                import re
                                match = re.search(r'「([^」]+)」', last_line)
                                if match:
                                    work_title = f"본문: {match.group(1)}"
                        
                        # 본문 섹션도 이미지 단위로 생성
                        # 작품은 보통 다음 페이지에 있음 (원본 섹션 페이지 + 1)
                        work_page = section.get("page", 0)
                        # content 이미지는 보통 다음 페이지에 있으므로 page + 1 시도
                        # 먼저 원본 페이지로 찾고, 없으면 다음 페이지로 찾기
                        work_images = []
                        if work_page > 0:
                            # content_dir가 정의되어 있는지 확인
                            if not content_dir.exists():
                                print(f"[books]   경고: 본문 이미지 디렉토리가 존재하지 않음: {content_dir}")
                            else:
                                # 먼저 원본 페이지로 찾기
                                pattern = f"content_p{work_page:02d}_*.png"
                                work_images = sorted(list(content_dir.glob(pattern)))
                                print(f"[books]   본문 이미지 검색 (page {work_page}): {len(work_images)}개 발견")
                                # 없으면 다음 페이지로 찾기
                                if not work_images and work_page > 0:
                                    next_page = work_page + 1
                                    pattern_next = f"content_p{next_page:02d}_*.png"
                                    next_images = sorted(list(content_dir.glob(pattern_next)))
                                    if next_images:
                                        work_images = next_images
                                        work_page = next_page  # 페이지 번호 업데이트
                                        print(f"[books]   본문 이미지를 다음 페이지({work_page})에서 발견: {[img.name for img in work_images]}")
                                    else:
                                        print(f"[books]   경고: 본문 이미지를 찾을 수 없음 (page {work_page} 및 {next_page})")
                        
                        if work_images:
                            print(f"[books]   본문 섹션에 이미지 {len(work_images)}개 발견")
                            for img_idx, img_path in enumerate(work_images):
                                work_unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                                # 이미지가 1개면 원본 제목 그대로, 여러 개면 번호 추가
                                work_unit_title = work_title if len(work_images) == 1 else f"{work_title} - 이미지 {img_idx + 1}"
                                
                                work_order = lecture_number * 10000 + actual_unit_index
                                work_pdf_ref = {
                                    "page": work_page,
                                    "lecture_id": lecture_id,
                                    "lecture_number": lecture_number,
                                    "lecture_title": lecture_title,
                                    "section_index": actual_unit_index,
                                    "is_work": True,
                                    "image_index": img_idx,
                                    "image_filename": img_path.name
                                }
                                
                                work_unit = LearningUnit(
                                    unit_id=work_unit_id,
                                    curriculum_id=curriculum_id,
                                    lesson_id=None,
                                    section_type="content",  # 본문 타입
                                    title=work_unit_title,
                                    content=work_content_str,
                                    order=work_order,
                                    break_points=None,
                                    pdf_references=json.dumps([work_pdf_ref], ensure_ascii=False),
                                )
                                db.add(work_unit)
                                actual_unit_index += 1
                                work_added = True  # 이미지가 있어도 work_added 설정
                                print(f"[books]   본문 이미지 단위 추가: {work_unit_title[:50]} (이미지: {img_path.name}, order: {work_order})")
                        else:
                            # 이미지가 없으면 기존처럼 1개만 생성
                            work_order = lecture_number * 10000 + actual_unit_index
                            work_pdf_ref = {
                                "page": work_page,
                                "lecture_id": lecture_id,
                                "lecture_number": lecture_number,
                                "lecture_title": lecture_title,
                                "section_index": actual_unit_index,
                                "is_work": True
                            }
                            
                            work_unit = LearningUnit(
                                unit_id=work_unit_id,
                                curriculum_id=curriculum_id,
                                lesson_id=None,
                                section_type="content",  # 본문 타입
                                title=work_title,
                                content=work_content_str,
                                order=work_order,
                                break_points=None,
                                pdf_references=json.dumps([work_pdf_ref], ensure_ascii=False),
                            )
                            db.add(work_unit)
                            actual_unit_index += 1
                            work_added = True
                            print(f"[books]   작품 섹션 추가 (이미지 없음): {work_title[:50]} (order: {work_order})")
                    elif work_start_idx == 0:
                        print(f"[books]   경고: 작품이 첫 줄부터 시작 (work_start_idx=0), 분리하지 않음")
                    else:
                        print(f"[books]   경고: 작품 시작 위치를 찾을 수 없음 (work_start_idx=None)")
            
            # 작품이 분리된 경우 원본 섹션은 저장하지 않음 (본문 다음에 바로 문제가 나와야 함)
            if work_added:
                print(f"[books]   원본 섹션 '{section.get('title', 'N/A')[:50]}'은(는) 작품이 분리되어 저장하지 않음")
                continue  # 다음 섹션으로 넘어감
            
            # content가 아직 설정되지 않은 경우 (작품 분리되지 않은 경우)
            if content is None:
                if isinstance(content_raw, list):
                    content = "\n".join(str(line) for line in content_raw)
                else:
                    content = str(content_raw)
            
            # content가 비어있거나 공백만 있는 경우 학습 단위 생성하지 않음
            if not content or not content.strip():
                print(f"[books]   섹션 '{section.get('title', 'N/A')[:50]}'은(는) 내용이 없어 저장하지 않음")
                continue  # 다음 섹션으로 넘어감
            
            # section.title을 그대로 사용 (예: "(1) 시적 표현의 개념")
            section_title = section.get("title") or f"{lecture_number}강 {section_type}"
            page = section.get("page", 0)
            
            # 해당 페이지의 이미지 찾기 (이미지 단위로 학습 단위 생성)
            images = []
            if page > 0:
                if section_type == "concept" and concepts_dir.exists():
                    pattern = f"concept_p{page:02d}_*.png"
                    images = sorted(list(concepts_dir.glob(pattern)))
                elif section_type == "content" and content_dir.exists():
                    pattern = f"content_p{page:02d}_*.png"
                    images = sorted(list(content_dir.glob(pattern)))
                elif section_type == "problem" and problems_dir.exists():
                    pattern = f"problem_p{page:02d}_*.png"
                    images = sorted(list(problems_dir.glob(pattern)))
            
            # 이미지가 있으면 각 이미지마다 학습 단위 생성, 없으면 1개만 생성
            if images:
                print(f"[books]   섹션 '{section_title[:50]}'에 이미지 {len(images)}개 발견")
                for img_idx, img_path in enumerate(images):
                    unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                    # 이미지가 1개면 원본 제목 그대로, 여러 개면 번호 추가
                    unit_title = section_title if len(images) == 1 else f"{section_title} - 이미지 {img_idx + 1}"
                    
                    # order = lecture_number * 10000 + actual_unit_index
                    order = lecture_number * 10000 + actual_unit_index
                    
                    # PDF 참조 정보에 이미지 정보 추가
                    pdf_ref = {
                        "page": page,
                        "lecture_id": lecture_id,
                        "lecture_number": lecture_number,
                        "lecture_title": lecture_title,
                        "section_index": idx,
                        "image_index": img_idx,
                        "image_filename": img_path.name
                    }
                    
                    learning_unit = LearningUnit(
                        unit_id=unit_id,
                        curriculum_id=curriculum_id,
                        lesson_id=None,
                        section_type=section_type,
                        title=unit_title,
                        content=content,  # 같은 내용을 모든 이미지 단위에 포함
                        order=order,
                        break_points=None,
                        pdf_references=json.dumps([pdf_ref], ensure_ascii=False),
                    )
                    db.add(learning_unit)
                    actual_unit_index += 1
                    print(f"[books]   이미지 단위 저장: {unit_title[:50]} (이미지: {img_path.name}, order: {order})")
            else:
                # 이미지가 없으면 기존처럼 1개만 생성
                order = lecture_number * 10000 + actual_unit_index
                pdf_ref = {
                    "page": page,
                    "lecture_id": lecture_id,
                    "lecture_number": lecture_number,
                    "lecture_title": lecture_title,
                    "section_index": idx
                }
                
                learning_unit = LearningUnit(
                    unit_id=unit_id,
                    curriculum_id=curriculum_id,
                    lesson_id=None,
                    section_type=section_type,
                    title=section_title,
                    content=content,
                    order=order,
                    break_points=None,
                    pdf_references=json.dumps([pdf_ref], ensure_ascii=False) if page > 0 else json.dumps([pdf_ref], ensure_ascii=False),
                )
                db.add(learning_unit)
                actual_unit_index += 1
                print(f"[books]   섹션 저장 (이미지 없음): {section_title[:50]} (order: {order}, type: {section_type})")
        
        # 문제들을 학습 단위로 변환
        problems = lecture_data.get("problems", [])
        problems_dir = data_dir / "problems"
        
        print(f"[books] 문제 처리 시작: {len(problems)}개 문제, 디렉토리: {problems_dir}")
        print(f"[books] 문제 디렉토리 존재: {problems_dir.exists()}")
        if problems_dir.exists():
            all_problem_files = list(problems_dir.glob('*.json'))
            print(f"[books] 문제 파일 목록 ({len(all_problem_files)}개): {[f.name for f in all_problem_files[:10]]}")
        else:
            print(f"[books] 경고: 문제 디렉토리가 존재하지 않음: {problems_dir}")
        
        for prob_idx, problem_num in enumerate(problems):
            # problem_num이 "01", "02" 등 문자열 형태
            # 문제 파일 찾기 (problem_num이 "01" 형태일 수 있음)
            # 예: problem_p09_01.json, problem_p10_02.json 등
            # 파일 이름 패턴: problem_p{page}_{num}.json
            
            # 패턴1: problem_*_{num}.json (예: problem_*_01.json)
            problem_num_padded = problem_num.zfill(2)  # "01", "02" 등
            problem_files = list(problems_dir.glob(f"problem_*_{problem_num_padded}.json"))
            print(f"[books]   문제 {prob_idx + 1} ({problem_num}): 패턴1 (problem_*_{problem_num_padded}.json) 매칭 {len(problem_files)}개")
            if problem_files:
                print(f"[books]     매칭된 파일: {[f.name for f in problem_files]}")
            
            if not problem_files:
                # 패턴2: problem_num만으로 검색 (예: *01*.json)
                problem_files = list(problems_dir.glob(f"*{problem_num}*.json"))
                print(f"[books]   문제 {prob_idx + 1} ({problem_num}): 패턴2 (*{problem_num}*.json) 매칭 {len(problem_files)}개")
                if problem_files:
                    print(f"[books]     매칭된 파일: {[f.name for f in problem_files]}")
            
            if not problem_files:
                # 패턴3: problem_num을 숫자로 변환하여 검색 (예: problem_*_1.json)
                try:
                    problem_num_int = int(problem_num)
                    problem_files = list(problems_dir.glob(f"problem_*_{problem_num_int}.json"))
                    print(f"[books]   문제 {prob_idx + 1} ({problem_num}): 패턴3 (problem_*_{problem_num_int}.json) 매칭 {len(problem_files)}개")
                    if problem_files:
                        print(f"[books]     매칭된 파일: {[f.name for f in problem_files]}")
                except ValueError:
                    pass
            
            if problem_files:
                problem_file = problem_files[0]  # 첫 번째 매칭 파일 사용
                try:
                    with open(problem_file, "r", encoding="utf-8") as f:
                        problem_data = json.load(f)
                    
                    # 문제 내용 추출
                    problem_content = problem_data.get("content", "")
                    if isinstance(problem_content, list):
                        problem_content = "\n".join(str(line) for line in problem_content)
                    
                    # 문제 지문 추출 (question_text 우선, 없으면 content 사용)
                    problem_question = problem_data.get("question_text", "")
                    if not problem_question:
                        problem_question = problem_content if isinstance(problem_content, str) else "\n".join(str(line) for line in problem_content)
                    
                    # 선택지 추출
                    problem_choices = problem_data.get("choices", {})
                    # choices가 딕셔너리인 경우 리스트로 변환
                    choices_list = []
                    if isinstance(problem_choices, dict):
                        # "1", "2", "3" 순서대로 정렬
                        for key in sorted(problem_choices.keys(), key=lambda x: int(x) if x.isdigit() else 999):
                            choices_list.append(problem_choices[key])
                    elif isinstance(problem_choices, list):
                        choices_list = problem_choices
                    
                    # 정답 추출 (임시로 없음, 나중에 추가 필요)
                    problem_answer = problem_data.get("answer", None)
                    
                    # 문제 메타데이터 생성
                    problem_metadata = {
                        "problem_id": problem_data.get("problem_id", problem_num),
                        "choices": choices_list,
                        "answer": problem_answer,
                        "question_text": problem_question,
                    }
                    
                    problem_title = problem_data.get("title", f"문제 {problem_num}")
                    problem_page = problem_data.get("page", 0)
                    
                    # content에는 문제 지문과 선택지를 포함한 전체 텍스트 저장
                    # full_text가 있으면 사용, 없으면 question_text + choices 조합
                    problem_full_text = problem_data.get("full_text", "")
                    if not problem_full_text:
                        # 선택지를 ①~⑤ 형식으로 변환하여 추가
                        choice_text = "\n".join([f"{['①', '②', '③', '④', '⑤'][i]} {choice}" for i, choice in enumerate(choices_list)])
                        problem_full_text = f"{problem_question}\n{choice_text}" if choices_list else problem_question
                    
                    # 문제 이미지 찾기 (이미지 단위로 학습 단위 생성)
                    problem_images = []
                    if problem_page > 0 and problems_dir.exists():
                        # problem_number를 사용하여 정확한 이미지 찾기
                        try:
                            prob_num_int = int(problem_num)
                            pattern = f"problem_p{problem_page:02d}_{prob_num_int:02d}.png"
                            prob_img = problems_dir / pattern
                            if prob_img.exists():
                                problem_images = [prob_img]
                        except ValueError:
                            pass
                        
                        # 정확한 매칭이 없으면 패턴으로 찾기
                        if not problem_images:
                            pattern = f"problem_p{problem_page:02d}_*.png"
                            all_images = sorted(list(problems_dir.glob(pattern)))
                            if all_images and prob_idx < len(all_images):
                                problem_images = [all_images[prob_idx]]
                    
                    # 이미지가 있으면 각 이미지마다 학습 단위 생성, 없으면 1개만 생성
                    if problem_images:
                        print(f"[books]   문제 {prob_idx + 1} ({problem_num}): 이미지 {len(problem_images)}개 발견")
                        for img_idx, img_path in enumerate(problem_images):
                            unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                            # 이미지가 1개면 원본 제목 그대로, 여러 개면 번호 추가
                            unit_title = problem_title if len(problem_images) == 1 else f"{problem_title} - 이미지 {img_idx + 1}"
                            
                            order = lecture_number * 10000 + actual_unit_index
                            actual_unit_index += 1
                            
                            pdf_ref = {
                                "page": problem_page,
                                "lecture_id": lecture_id,
                                "lecture_number": lecture_number,
                                "lecture_title": lecture_title,
                                "problem_number": problem_num,
                                "problem_index": prob_idx,
                                "image_index": img_idx,
                                "image_filename": img_path.name
                            }
                            
                            learning_unit = LearningUnit(
                                unit_id=unit_id,
                                curriculum_id=curriculum_id,
                                lesson_id=None,
                                section_type="problem",
                                title=unit_title,
                                content=problem_full_text,  # 전체 문제 텍스트 (지문 + 선택지)
                                order=order,
                                break_points=None,
                                pdf_references=json.dumps([pdf_ref], ensure_ascii=False),
                                subject_metadata=json.dumps(problem_metadata, ensure_ascii=False),  # 선택지와 정답 정보
                            )
                            db.add(learning_unit)
                            print(f"[books]   문제 이미지 단위 저장: {unit_title[:50]} (이미지: {img_path.name}, order: {order})")
                    else:
                        # 이미지가 없으면 기존처럼 1개만 생성
                        unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                        order = lecture_number * 10000 + actual_unit_index
                        actual_unit_index += 1
                        print(f"[books]   문제 {prob_idx + 1} ({problem_num}): {problem_file.name} (이미지 없음, order: {order})")
                        
                        pdf_ref = {
                            "page": problem_page,
                            "lecture_id": lecture_id,
                            "lecture_number": lecture_number,
                            "lecture_title": lecture_title,
                            "problem_number": problem_num,
                            "problem_index": prob_idx
                        }
                        
                        learning_unit = LearningUnit(
                            unit_id=unit_id,
                            curriculum_id=curriculum_id,
                            lesson_id=None,
                            section_type="problem",
                            title=problem_title,
                            content=problem_full_text,  # 전체 문제 텍스트 (지문 + 선택지)
                            order=order,
                            break_points=None,
                            pdf_references=json.dumps([pdf_ref], ensure_ascii=False),
                            subject_metadata=json.dumps(problem_metadata, ensure_ascii=False),  # 선택지와 정답 정보
                        )
                        db.add(learning_unit)
                except Exception as e:
                    print(f"[books]   경고: 문제 파일 읽기 실패 {problem_file}: {e}")
            else:
                print(f"[books]   경고: 문제 파일을 찾을 수 없음 (번호: {problem_num})")
                print(f"[books]   시도한 패턴: problem_*_{problem_num.zfill(2)}.json, *{problem_num}*.json")
    
    db.commit()
    total_units = db.query(LearningUnit).filter(LearningUnit.curriculum_id == curriculum_id).count()
    print(f"[books] 커리큘럼 생성 완료: {curriculum_id}")
    print(f"[books]   강의 수: {len(lectures)}개")
    print(f"[books]   학습 단위 총 개수: {total_units}개")
    
    # 각 강의별 학습 단위 개수 확인
    for lecture in lectures:
        lecture_id = lecture.get("lecture_id", 0)
        lecture_num = lecture.get("lecture_number", lecture_id)
        units_for_lecture = db.query(LearningUnit).filter(
            LearningUnit.curriculum_id == curriculum_id,
            LearningUnit.order >= lecture_num * 10000,
            LearningUnit.order < (lecture_num + 1) * 10000
        ).count()
        print(f"[books]   {lecture_num}강: {units_for_lecture}개 학습 단위")
    
    return curriculum_id


def _process_pdf_background(book_id: str, pdf_path: Path, subject: str, ai_options: dict = None):
    """백그라운드에서 PDF 파이프라인 실행"""
    from app.services.textbook_pipeline import TextbookPipeline
    from app.db.models import Book, ParseStatus
    from app.db.session import SessionLocal

    if ai_options is None:
        ai_options = {}

    db = SessionLocal()
    try:
        # Subject enum 변환
        subject_enum = Subject(subject)
        pipeline_subject = _subject_to_pipeline_subject(subject_enum)

        print(f"[books] PDF 파이프라인 시작: {pdf_path} (과목: {pipeline_subject})")
        print(f"[books] AI 옵션: ML dedup={ai_options.get('enable_ml_deduplication', True)}, "
              f"ML class={ai_options.get('enable_ml_classification', True)}, "
              f"DL layout={ai_options.get('enable_layout_analysis', False)}, "
              f"DL math={ai_options.get('enable_math_recognition', False)}, "
              f"LLM meta={ai_options.get('enable_llm_metadata', False)}, "
              f"LLM expl={ai_options.get('enable_llm_explanations', False)}, "
              f"LLM rec={ai_options.get('enable_llm_recommendations', False)}")

        # AI 후처리 활성화 여부 결정
        enable_ai = (ai_options.get('enable_ml_deduplication', True) or
                    ai_options.get('enable_ml_classification', True) or
                    ai_options.get('enable_layout_analysis', False) or
                    ai_options.get('enable_math_recognition', False) or
                    ai_options.get('enable_llm_metadata', False) or
                    ai_options.get('enable_llm_explanations', False) or
                    ai_options.get('enable_llm_recommendations', False))

        # TextbookPipeline 실행 (AI 옵션 반영)
        pipeline = TextbookPipeline(
            subject=pipeline_subject,
            dpi=150,  # DPI 낮춤 (속도 최적화)
            use_parallel=True,  # 병렬 처리 활성화
            use_ai_postprocess=enable_ai,  # AI 옵션에 따라 활성화
            use_cache=True,
            use_pdfplumber=True,  # pdfplumber 우선 사용
            max_pages=None,  # 전체 페이지 처리
            ai_options=ai_options,  # AI 옵션 전달
        )
        
        print(f"[books] 파이프라인 설정: DPI={pipeline.dpi}, 병렬={pipeline.use_parallel}, pdfplumber={pipeline.use_pdfplumber}")
        
        result = pipeline.process_pdf(pdf_path)
        
        # 파이프라인 완료 후 커리큘럼 자동 생성
        curriculum_id = None
        if result.get('lectures'):
            try:
                curriculum_id = _create_curriculum_from_pipeline(
                    book_id=book_id,
                    subject_enum=subject_enum,
                    pipeline_subject=pipeline_subject,
                    title=book.title if book else f"{subject} 교재",
                    db=db
                )
                print(f"[books] 커리큘럼 자동 생성 완료: {curriculum_id}")
            except Exception as e:
                print(f"[books] 커리큘럼 생성 실패 (파이프라인은 성공): {e}")
                import traceback
                traceback.print_exc()
        
        # 파싱 완료 상태 업데이트
        book = db.query(Book).filter(Book.book_id == book_id).first()
        if book:
            book.parse_status = ParseStatus.DONE
            db.commit()
            print(f"[books] PDF 파이프라인 완료: {book_id} (강의 {len(result.get('lectures', []))}개 생성, 커리큘럼: {curriculum_id})")
        else:
            print(f"[books] 경고: 교재를 찾을 수 없음: {book_id}")
            
    except Exception as e:
        print(f"[books] PDF 파이프라인 실패: {e}")
        import traceback
        traceback.print_exc()
        
        # 파싱 실패 상태 업데이트
        try:
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                book.parse_status = ParseStatus.FAILED
                db.commit()
        except Exception as db_error:
            print(f"[books] DB 업데이트 실패: {db_error}")
    finally:
        db.close()

# LectureScriptParser (삭제된 모듈 대체용)
try:
    from app.services.lecture_script_parser import LectureScriptParser
except ImportError:
    # lecture_script_parser 모듈이 없는 경우 stub 클래스 제공
    class LectureScriptParser:
        def __init__(self, subject: str = "literature"):
            self.subject = subject
        
        def parse(self, text: str) -> dict:
            raise HTTPException(status_code=501, detail="강의 스크립트 파싱이 지원되지 않습니다.")

router = APIRouter()


@router.post("/books/upload", response_model=BookResponse, status_code=201)
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(...),
    year: int = Form(None),
    # AI Processing Options (Level 1/2/3)
    enable_ml_deduplication: bool = Form(True),
    enable_ml_classification: bool = Form(True),
    enable_layout_analysis: bool = Form(False),
    enable_math_recognition: bool = Form(False),
    enable_llm_metadata: bool = Form(False),
    enable_llm_explanations: bool = Form(False),
    enable_llm_recommendations: bool = Form(False),
    openai_api_key: str = Form(None),
    education_level: str = Form("high"),
    db: Session = Depends(get_db),
):
    """
    PDF 업로드 + 교재 생성 + 파싱 시작
    
    PDF 업로드 시 자동으로 textbook_pipeline을 실행하여 학습 데이터를 생성합니다.
    """
    # 파일 검증
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"파일 크기는 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB를 초과할 수 없습니다.")
    
    # 교재 ID 생성 (의미있는 ID)
    book_id = generate_book_id(subject, title, year)
    
    # 파일 저장
    file_path = settings.UPLOADS_DIR / f"{book_id}.pdf"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # DB에 교재 생성
    book = Book(
        book_id=book_id,
        title=title,
        subject=Subject(subject),
        year=year,
        parse_status=ParseStatus.PROCESSING,
        file_path=str(file_path),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # 백그라운드에서 PDF 파이프라인 실행 (AI 옵션 전달)
    ai_options = {
        "enable_ml_deduplication": enable_ml_deduplication,
        "enable_ml_classification": enable_ml_classification,
        "enable_layout_analysis": enable_layout_analysis,
        "enable_math_recognition": enable_math_recognition,
        "enable_llm_metadata": enable_llm_metadata,
        "enable_llm_explanations": enable_llm_explanations,
        "enable_llm_recommendations": enable_llm_recommendations,
        "openai_api_key": openai_api_key,
        "education_level": education_level,
    }
    background_tasks.add_task(
        _process_pdf_background,
        book_id,
        file_path,
        subject,
        ai_options
    )
    
    return BookResponse(
        book_id=book.book_id,
        title=book.title,
        subject=book.subject,
        year=book.year,
        parse_status=book.parse_status,
        lesson_count=0,
    )


@router.get("/books", response_model=List[BookResponse])
async def list_books(
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    교재 목록 조회
    
    MENU_FLOW: 과목 선택 → 교재 목록에서 사용
    """
    query = db.query(Book)
    
    # 과목 필터링
    if subject:
        try:
            subject_enum = Subject(subject.upper())
            query = query.filter(Book.subject == subject_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 과목: {subject}")
    
    books = query.order_by(Book.created_at.desc()).all()
    
    # 중복 제거: 같은 제목과 연도의 교재는 가장 최근 것만 유지
    book_map = {}
    for book in books:
        key = (book.title, book.year)  # 제목과 연도로 중복 판단
        if key not in book_map or book.created_at > book_map[key].created_at:
            book_map[key] = book
    
    result = []
    for book in book_map.values():
        lesson_count = len(book.lessons) if book.lessons else 0
        result.append(BookResponse(
            book_id=book.book_id,
            title=book.title,
            subject=book.subject,
            year=book.year,
            parse_status=book.parse_status,
            lesson_count=lesson_count,
        ))
    
    # 최신순으로 정렬
    result.sort(key=lambda x: x.book_id, reverse=True)
    return result


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, db: Session = Depends(get_db)):
    """교재 상세"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    lesson_count = len(book.lessons) if book.lessons else 0
    return BookResponse(
        book_id=book.book_id,
        title=book.title,
        subject=book.subject,
        year=book.year,
        parse_status=book.parse_status,
        lesson_count=lesson_count,
    )


@router.get("/books/{book_id}/parse-status", response_model=BookParseStatusResponse)
async def get_parse_status(book_id: str, db: Session = Depends(get_db)):
    """파싱 진행 상태 (프론트 폴링용)"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    # TODO: 실제 파싱 진행률 계산 (현재는 상태만 반환)
    progress = 100 if book.parse_status == ParseStatus.DONE else 0
    
    return BookParseStatusResponse(
        book_id=book.book_id,
        status=book.parse_status,
        progress=progress,
    )


@router.post("/books/{book_id}/reparse")
async def reparse_book(book_id: str, db: Session = Depends(get_db)):
    """교재 재파싱"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    # 파일 경로 확인
    file_path = Path(book.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"파일을 찾을 수 없습니다: {file_path}"
        )
    
    # PDF 파일인 경우 재파싱
    if file_path.suffix.lower() == '.pdf':
        try:
            # 기존 강의 삭제 (선택적)
            # for lesson in book.lessons:
            #     db.delete(lesson)
            # db.commit()
            
            # 재파싱 시작
            # TODO: PDF 파싱 파이프라인 구현 후 활성화
            # success = parse_lessons_and_units(book_id, db)
            success = False  # 임시로 False
            
            # 최신 상태 가져오기
            db.refresh(book)
            
            if success:
                return {
                    "ok": True,
                    "message": "재파싱이 완료되었습니다.",
                    "status": book.parse_status.value if hasattr(book.parse_status, 'value') else str(book.parse_status)
                }
            else:
                return {
                    "ok": False,
                    "message": "재파싱에 실패했습니다.",
                    "status": book.parse_status.value if hasattr(book.parse_status, 'value') else str(book.parse_status)
                }
        except Exception as e:
            print(f"[books] 재파싱 실패: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"재파싱 중 오류가 발생했습니다: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="PDF 파일만 재파싱할 수 있습니다."
        )


@router.post("/books/upload-hwp", response_model=BookResponse, status_code=201)
async def upload_hwp_book(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(...),
    year: int = Form(None),
    db: Session = Depends(get_db),
):
    """
    한글 파일 업로드 및 파싱
    
    - 파일명에서 강의 정보 추출
    - 텍스트 추출 및 구조화
    - 데이터베이스에 저장
    """
    # 파일 검증
    if not file.filename or not (file.filename.endswith('.hwp') or file.filename.endswith('.HWP')):
        raise HTTPException(status_code=400, detail="한글 파일(.hwp)만 업로드 가능합니다.")
    
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"파일 크기는 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB를 초과할 수 없습니다.")
    
    # 교재 ID 생성 (의미있는 ID)
    book_id = generate_book_id(subject, title, year)
    
    # 파일 저장
    file_path = settings.UPLOADS_DIR / f"{book_id}.hwp"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 파일명에서 강의 정보 추출
    lesson_info = extract_lesson_info_from_filename(file.filename)
    
    # 텍스트 추출 및 구조 파싱
    text = extract_text_from_hwp(file_path)
    structure = extract_structure_from_hwp(file_path) if text else {}
    
    # DB에 교재 생성
    book = Book(
        book_id=book_id,
        title=title,
        subject=Subject(subject),
        year=year,
        parse_status=ParseStatus.PROCESSING,
        file_path=str(file_path),
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # 강의 대본 파서로 구조화된 데이터 추출
    lesson_count = 0
    if text:
        try:
            # 과목에 맞는 파서 생성
            subject_str = subject.lower()
            if subject_str == 'korean':
                subject_str = 'literature'
            elif subject_str == 'math':
                subject_str = 'math1'
            
            parser = LectureScriptParser(subject=subject_str)
            parsed = parser.parse(text)
            
            # Lesson 생성
            lesson_number = parsed.get('lesson_number', 0)
            if lesson_number == 0 and lesson_info.get('lesson_number'):
                lesson_number = lesson_info['lesson_number']
            
            # 의미있는 레슨 ID 생성
            lesson_id = generate_lesson_id(subject_str, lesson_number)
            
            lesson_title = lesson_info.get('title') or f"{lesson_number}강"
            if not lesson_title or lesson_title == '0강':
                # 파싱 결과에서 제목 추출 시도
                sections = parsed.get('sections', [])
                if sections:
                    first_section = sections[0]
                    if first_section.get('type') == 'ot':
                        content = first_section.get('content', '')
                        # "수능특강 문학" 같은 패턴 찾기
                        import re
                        title_match = re.search(r'수능특강\s*([가-힣]+)', content)
                        if title_match:
                            lesson_title = f"{lesson_number}강 {title_match.group(1)}"
                        else:
                            lesson_title = f"{lesson_number}강"
            
            lesson = Lesson(
                lesson_id=lesson_id,
                book_id=book_id,
                index=lesson_number,
                title=lesson_title,
            )
            db.add(lesson)
            db.commit()
            lesson_count = 1
            
            # 파싱 성공
            book.parse_status = ParseStatus.DONE
        except Exception as e:
            print(f"[books] Error parsing HWP: {e}")
            import traceback
            traceback.print_exc()
            book.parse_status = ParseStatus.FAILED
    else:
        book.parse_status = ParseStatus.FAILED
    
    db.commit()
    db.refresh(book)
    
    return BookResponse(
        book_id=book.book_id,
        title=book.title,
        subject=book.subject,
        year=book.year,
        parse_status=book.parse_status,
        lesson_count=lesson_count,
    )


@router.get("/books/{book_id}/lessons-from-hwp")
async def get_lessons_from_hwp(book_id: str, db: Session = Depends(get_db)):
    """한글 파일에서 추출한 강의 목록 조회"""
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    pdf_path = Path(book.file_path)
    if not pdf_path.exists() or not pdf_path.suffix.lower() == '.hwp':
        raise HTTPException(status_code=404, detail="한글 파일을 찾을 수 없습니다.")
    
    # 구조 추출
    structure = extract_structure_from_hwp(pdf_path)
    lesson_info = extract_lesson_info_from_filename(pdf_path.name)
    
    return {
        "book_id": book_id,
        "lesson_info": lesson_info,
        "structure": structure
    }


@router.post("/books/{book_id}/create-curriculum-from-data")
async def create_curriculum_from_existing_data(
    book_id: str,
    db: Session = Depends(get_db),
):
    """
    기존 파이프라인 데이터로부터 커리큘럼 생성
    
    이미 api/data/{subject}/lectures/ 폴더에 데이터가 있는 경우,
    이를 기반으로 커리큘럼을 생성합니다.
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    # 이미 커리큘럼이 있는지 확인하고 삭제
    try:
        existing_curriculum = db.query(Curriculum).filter(Curriculum.book_id == book_id).first()
        if existing_curriculum:
            # 기존 커리큘럼의 학습 단위 삭제
            existing_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == existing_curriculum.curriculum_id
            ).all()
            for unit in existing_units:
                db.delete(unit)
            # 기존 커리큘럼 삭제
            db.delete(existing_curriculum)
            db.commit()
            print(f"[books] 기존 커리큘럼 삭제: {existing_curriculum.curriculum_id} (학습 단위 {len(existing_units)}개)")
    except Exception as e:
        print(f"[books] 경고: 기존 커리큘럼 삭제 중 오류: {e}")
        db.rollback()
    
    # Subject enum 변환
    subject_enum = book.subject
    pipeline_subject = _subject_to_pipeline_subject(subject_enum)
    
    try:
        # 파이프라인 데이터로부터 커리큘럼 생성
        curriculum_id = _create_curriculum_from_pipeline(
            book_id=book_id,
            subject_enum=subject_enum,
            pipeline_subject=pipeline_subject,
            title=book.title,
            db=db
        )
        
        if curriculum_id:
            return {
                "ok": True,
                "message": "커리큘럼이 성공적으로 생성되었습니다.",
                "curriculum_id": curriculum_id
            }
        else:
            return {
                "ok": False,
                "message": "커리큘럼 생성에 실패했습니다. 파이프라인 데이터를 확인하세요."
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"커리큘럼 생성 중 오류가 발생했습니다: {str(e)}"
        )
