"""
교재 관련 라우터
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import sys
import logging
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
from app.db.models import Lesson, Curriculum, LearningUnit, CurriculumStatus, Unit, UnitType
import json

# ML 기반 섹션 분류기 (선택적)
try:
    from app.services.ml_section_classifier import get_section_classifier
    ML_CLASSIFIER_AVAILABLE = True
except ImportError:
    ML_CLASSIFIER_AVAILABLE = False
    # ML 분류기는 선택적 의존성이므로 경고 없이 무시


def _subject_to_pipeline_subject(subject: Subject) -> str:
    """Subject enum을 textbook_pipeline의 subject 형식으로 변환"""
    mapping = {
        Subject.KOREAN: "literature",
        Subject.MATH: "math1",
        Subject.ENGLISH: "english",
    }
    return mapping.get(subject, "literature")


def _map_section_type_to_unit_type(section_type: str) -> UnitType:
    """
    LearningUnit의 section_type (문자열)을 Unit의 UnitType (enum)으로 매핑

    Args:
        section_type: "concept", "content", "problem", "example", "strategy" 등

    Returns:
        UnitType enum value
    """
    mapping = {
        # 개념 타입
        "concept": UnitType.CONCEPT_CORE,
        "ot": UnitType.CONCEPT_CORE,  # 오리엔테이션도 핵심 개념으로
        "general": UnitType.CONCEPT_CORE,

        # 작품/본문 타입
        "content": UnitType.PASSAGE,
        "work": UnitType.PASSAGE,
        "passage": UnitType.PASSAGE,

        # 문제 타입
        "problem": UnitType.QUESTION,
        "question": UnitType.QUESTION,

        # 예시/전략은 개념으로 분류
        "example": UnitType.CONCEPT_FORM,
        "strategy": UnitType.CONCEPT_CONTENT,
    }

    return mapping.get(section_type.lower(), UnitType.CONCEPT_CORE)


def _convert_learning_units_to_units(
    curriculum_id: str,
    book_id: str,
    db: Session
) -> dict:
    """
    Curriculum의 LearningUnit들을 Lesson과 Unit으로 변환하여 프론트엔드 호환성 확보

    Args:
        curriculum_id: 커리큘럼 ID
        book_id: 교재 ID
        db: 데이터베이스 세션

    Returns:
        변환 통계 딕셔너리 {"lessons_created": int, "units_created": int}
    """
    print(f"[books] LearningUnit → Unit 변환 시작: curriculum_id={curriculum_id}")

    # 1. 커리큘럼의 모든 LearningUnit 조회
    learning_units = db.query(LearningUnit).filter(
        LearningUnit.curriculum_id == curriculum_id
    ).order_by(LearningUnit.order).all()

    if not learning_units:
        print(f"[books] 변환할 LearningUnit이 없습니다.")
        return {"lessons_created": 0, "units_created": 0}

    # 2. 레슨별로 그룹화 (order = lecture_id * 10000 + unit_index)
    lessons_dict = {}
    for lu in learning_units:
        lesson_number = lu.order // 10000  # lecture_id를 추출

        if lesson_number not in lessons_dict:
            lessons_dict[lesson_number] = []

        lessons_dict[lesson_number].append(lu)

    print(f"[books] {len(learning_units)}개 LearningUnit을 {len(lessons_dict)}개 레슨으로 그룹화")

    # 3. 레슨별로 Lesson과 Unit 생성
    lessons_created = 0
    units_created = 0

    for lesson_number in sorted(lessons_dict.keys()):
        lesson_units = lessons_dict[lesson_number]

        # 레슨 제목 추출 (첫 번째 LearningUnit의 pdf_references에서)
        lesson_title = f"{lesson_number}강"
        if lesson_units and lesson_units[0].pdf_references:
            try:
                pdf_refs = json.loads(lesson_units[0].pdf_references)
                if isinstance(pdf_refs, list) and pdf_refs:
                    lesson_title = pdf_refs[0].get('lecture_title', lesson_title)
                elif isinstance(pdf_refs, dict):
                    lesson_title = pdf_refs.get('lecture_title', lesson_title)
            except:
                pass

        # 기존 Lesson 확인 (같은 book_id와 index로)
        existing_lesson = db.query(Lesson).filter(
            Lesson.book_id == book_id,
            Lesson.index == lesson_number
        ).first()
        
        if existing_lesson:
            # 기존 Lesson 업데이트
            existing_lesson.title = lesson_title
            lesson = existing_lesson
            lesson_id = existing_lesson.lesson_id
            print(f"[books]   Lesson 업데이트: {lesson_id} - {lesson_title}")
            
            # 기존 Lesson의 모든 Unit 삭제 (데이터 일관성 보장)
            existing_units = db.query(Unit).filter(Unit.lesson_id == lesson_id).all()
            if existing_units:
                print(f"[books]   기존 Unit {len(existing_units)}개 삭제 중...")
                for unit in existing_units:
                    db.delete(unit)
                print(f"[books]   기존 Unit 삭제 완료")
        else:
            # 새 Lesson 생성
            lesson_id = f"l_{uuid.uuid4().hex[:12]}"
            lesson = Lesson(
                lesson_id=lesson_id,
                book_id=book_id,
                title=lesson_title,
                index=lesson_number  # Lesson 모델은 index 필드 사용
            )
            db.add(lesson)
            lessons_created += 1
            print(f"[books]   Lesson 생성: {lesson_id} - {lesson_title}")

        # 각 LearningUnit을 Unit으로 변환
        for lu in lesson_units:
            # UnitType 매핑
            unit_type = _map_section_type_to_unit_type(lu.section_type)

            # 이미지 경로 및 전체 작품 내용 추출 (pdf_references에서)
            image_path = None
            image_paths = []
            full_work_content = None
            if lu.pdf_references:
                try:
                    pdf_refs = json.loads(lu.pdf_references)
                    if isinstance(pdf_refs, list):
                        # 여러 개의 참조가 있는 경우
                        for ref in pdf_refs:
                            if isinstance(ref, dict):
                                # 이미지 경로 추출
                                if ref.get('image_filename'):
                                    page = ref.get('page', 0)
                                    # 과목별 디렉토리 결정
                                    curriculum = db.query(Curriculum).filter(
                                        Curriculum.curriculum_id == curriculum_id
                                    ).first()
                                    if curriculum:
                                        subject_lower = curriculum.subject.value.lower()
                                        if subject_lower == 'korean':
                                            subject_lower = 'literature'

                                        # section_type에 따라 이미지 디렉토리 결정
                                        if lu.section_type == 'concept':
                                            img_dir = 'concepts_images'
                                        elif lu.section_type == 'problem':
                                            img_dir = 'problems_images'
                                        else:
                                            img_dir = 'content_images'

                                        img_path = f"/api/data/{subject_lower}/{img_dir}/{ref['image_filename']}"
                                        image_paths.append(img_path)

                                # 전체 작품 내용 추출 (작품 타입인 경우)
                                # 우선순위: full_work_content > content (전체 작품인 경우)
                                if ref.get('is_work'):
                                    if ref.get('full_work_content'):
                                        full_work_content = ref['full_work_content']
                                    elif lu.content and len(lu.content) > 100:
                                        # full_work_content가 없지만 content가 충분히 길면 전체 작품으로 간주
                                        full_work_content = lu.content
                    elif isinstance(pdf_refs, dict):
                        # 단일 참조
                        if pdf_refs.get('image_filename'):
                            curriculum = db.query(Curriculum).filter(
                                Curriculum.curriculum_id == curriculum_id
                            ).first()
                            if curriculum:
                                subject_lower = curriculum.subject.value.lower()
                                if subject_lower == 'korean':
                                    subject_lower = 'literature'

                                if lu.section_type == 'concept':
                                    img_dir = 'concepts_images'
                                elif lu.section_type == 'problem':
                                    img_dir = 'problems_images'
                                else:
                                    img_dir = 'content_images'

                                img_path = f"/api/data/{subject_lower}/{img_dir}/{pdf_refs['image_filename']}"
                                image_paths.append(img_path)

                        # 전체 작품 내용 추출
                        # 우선순위: full_work_content > content (전체 작품인 경우)
                        if pdf_refs.get('is_work'):
                            if pdf_refs.get('full_work_content'):
                                full_work_content = pdf_refs['full_work_content']
                            elif lu.content and len(lu.content) > 100:
                                # full_work_content가 없지만 content가 충분히 길면 전체 작품으로 간주
                                full_work_content = lu.content
                except Exception as e:
                    print(f"[books] 이미지 경로/전체 작품 내용 추출 실패: {e}")
                    import traceback
                    traceback.print_exc()

            # 첫 번째 이미지를 image_path로, 나머지는 content_image_paths로
            if image_paths:
                image_path = image_paths[0]
                if len(image_paths) > 1:
                    content_image_paths_json = json.dumps(image_paths, ensure_ascii=False)
                else:
                    content_image_paths_json = None
            else:
                content_image_paths_json = None

            # Unit 레코드 생성
            # PASSAGE 타입의 경우 braille_text 필드에 전체 작품 내용 저장
            braille_text_value = lu.braille_text
            
            # 작품 내용 추출 우선순위:
            # 1. pdf_references의 full_work_content (가장 정확, 전체 작품)
            # 2. lu.content (전체 작품 내용이 저장된 경우, 100자 이상)
            # 3. lu.braille_text (기존 값, 100자 이상)
            # 4. lu.content (짧은 텍스트라도 사용)
            if unit_type == UnitType.PASSAGE:
                if full_work_content:
                    braille_text_value = full_work_content
                    print(f"[books]   작품 Unit에 전체 작품 내용 저장 (pdf_references에서): {len(full_work_content)}자")
                elif lu.content and len(lu.content) > 100:  # content가 충분히 길면 전체 작품으로 간주
                    # content가 전체 작품 내용인 경우 (이미지가 없을 때)
                    braille_text_value = lu.content
                    print(f"[books]   작품 Unit에 전체 작품 내용 저장 (content에서): {len(lu.content)}자")
                elif lu.braille_text and len(lu.braille_text) > 100:
                    # braille_text에 이미 전체 내용이 있는 경우
                    braille_text_value = lu.braille_text
                    print(f"[books]   작품 Unit에 전체 작품 내용 저장 (braille_text에서): {len(lu.braille_text)}자")
                elif lu.content:
                    # 작품 내용이 짧아도 content를 사용
                    braille_text_value = lu.content
                    print(f"[books]   작품 Unit에 내용 저장: {len(lu.content)}자")
                else:
                    # content도 없으면 기존 braille_text 유지
                    print(f"[books]   작품 Unit 내용 없음 (기존 braille_text 유지)")

            unit = Unit(
                unit_id=lu.unit_id,  # 같은 ID 사용
                lesson_id=lesson_id,
                type=unit_type,
                title=lu.title or f"{lu.section_type} 학습 단위",
                order=lu.order,
                content_text=lu.content,
                braille_text=braille_text_value,  # 작품의 경우 전체 내용, 그 외는 기존 값
                image_path=image_path,  # DB에서 직접 관리
                content_image_paths=content_image_paths_json  # 여러 이미지
            )

            # 문제인 경우 추가 필드 설정
            if unit_type == UnitType.QUESTION and lu.subject_metadata:
                try:
                    metadata = json.loads(lu.subject_metadata)
                    unit.question_stem = metadata.get('problem_text', lu.content)

                    # 선택지 처리
                    choices = metadata.get('choices', [])
                    if choices:
                        unit.question_choices = json.dumps(choices, ensure_ascii=False)

                    # 정답 처리
                    unit.question_answer = metadata.get('answer', None)
                except:
                    pass

            db.add(unit)
            units_created += 1

        # LearningUnit에 lesson_id 설정 (양방향 참조)
        for lu in lesson_units:
            lu.lesson_id = lesson_id

    # 4. 커밋
    db.commit()

    print(f"[books] 변환 완료: {lessons_created}개 Lesson, {units_created}개 Unit 생성")

    return {
        "lessons_created": lessons_created,
        "units_created": units_created
    }


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
    
    # 디렉토리 존재 확인
    if not lectures_dir.exists():
        print(f"[books] ❌ 경고: 강의 디렉토리가 존재하지 않음: {lectures_dir}")
        return curriculum_id
    
    # lectures.json 대신 실제 lecture_*.json 파일들을 직접 읽기
    lecture_files = sorted(lectures_dir.glob("lecture_*.json"))
    # lectures.json은 제외
    lecture_files = [f for f in lecture_files if f.name != "lectures.json"]
    
    if not lecture_files:
        print(f"[books] ❌ 경고: 강의 파일을 찾을 수 없음: {lectures_dir}")
        print(f"[books] 디렉토리 내용: {list(lectures_dir.glob('*'))}")
        return curriculum_id
    
    print(f"[books] ✅ JSON 파일 발견: {len(lecture_files)}개")
    
    print(f"[books] 발견된 강의 파일: {len(lecture_files)}개")
    
    # 각 파일에서 lecture_id 추출하여 lectures 리스트 생성
    lectures = []
    for lecture_file in lecture_files:
        try:
            with open(lecture_file, "r", encoding="utf-8") as f:
                lecture_data = json.load(f)
            
            lecture_id = lecture_data.get("lecture_id", 0)
            if lecture_id == 0:
                # 파일명에서 lecture_id 추출 (lecture_01.json -> 1)
                import re
                match = re.search(r'lecture_(\d+)\.json', lecture_file.name)
                if match:
                    lecture_id = int(match.group(1))
            
            # lecture_number는 lecture_id와 동일하게 설정
            lecture_number = lecture_data.get("lecture_number", lecture_id)
            title = lecture_data.get("title", f"{lecture_number}강")
            
            lectures.append({
                "lecture_id": lecture_id,
                "lecture_number": lecture_number,
                "title": title,
                "file": lecture_file
            })
        except Exception as e:
            print(f"[books] 경고: 파일 읽기 실패 {lecture_file}: {e}")
            continue
    
    if not lectures:
        print(f"[books] 경고: 강의 데이터가 없음")
        return curriculum_id
    
    print(f"[books] 로드된 강의: {len(lectures)}개")
    
    # 커리큘럼 생성 (book_id가 None일 수 있음)
    curriculum = Curriculum(
        curriculum_id=curriculum_id,
        book_id=book_id,  # None일 수 있음
        subject=subject_enum,
        title=title,
        status=CurriculumStatus.DONE,
        lesson_count=len(lectures),  # 실제 JSON 파일 개수
    )
    db.add(curriculum)
    db.commit()
    db.refresh(curriculum)
    
    # 각 강의(lecture)를 레슨(lesson)으로 변환
    # 각 JSON 파일을 하나의 Lesson으로 변환 (단순화)
    import re
    
    for lecture in lectures:
        lecture_id = lecture.get("lecture_id", 0)
        lecture_number = lecture.get("lecture_number", lecture_id)
        lecture_file = lecture.get("file")
        
        if not lecture_file or not lecture_file.exists():
            print(f"[books] 경고: 강의 파일을 찾을 수 없음: {lecture_file}")
            continue
        
        # 강의 상세 파일 읽기
        with open(lecture_file, "r", encoding="utf-8") as f:
            lecture_data = json.load(f)
        
        # lecture_data.title을 레슨 제목으로 사용 (예: "1강 | 시의 표현과 형식 >>> 고전 시가")
        lecture_title = lecture_data.get("title", f"{lecture_number}강")
        
        # 제목이 없거나 너무 짧으면 기본 제목 사용
        if not lecture_title or len(lecture_title.strip()) < 2:
            lecture_title = f"{lecture_number}강"
        
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

        # Lesson은 _convert_learning_units_to_units에서 생성하므로 여기서는 생성하지 않음
        # LearningUnit만 생성하고, 나중에 Lesson과 Unit으로 변환

        # 이미지 디렉토리 경로
        from app.core.config import settings
        data_dir = settings.API_DIR / "data" / pipeline_subject
        concepts_dir = data_dir / "concepts_images"
        content_dir = data_dir / "content_images"
        problems_dir = data_dir / "problems_images"

        # 페이지별로 같은 타입의 섹션 인덱스를 추적 (이미지 중복 방지)
        page_section_counters = {}  # {(page, section_type): current_index}

        def get_section_index_in_page(page, section_type):
            """해당 페이지에서 같은 타입의 섹션이 몇 번째인지 반환"""
            key = (page, section_type)
            if key not in page_section_counters:
                page_section_counters[key] = 0
            current_idx = page_section_counters[key]
            page_section_counters[key] += 1
            return current_idx

        # 섹션을 타입별로 분류하여 순서 보장: 개념 -> 본문 -> 문제
        concept_sections = []
        content_sections = []
        other_sections = []

        for idx, section in enumerate(sections):
            section_type = section.get("type", "general")
            if section_type == "general":
                # 제목 기반으로 타입 추정
                title_lower = section.get("title", "").lower()
                if "개념" in title_lower or "concept" in title_lower:
                    section_type = "concept"
                elif "본문" in title_lower or "작품" in title_lower or "content" in title_lower:
                    section_type = "content"
            
            if section_type == "concept":
                concept_sections.append((idx, section))
            elif section_type == "content":
                content_sections.append((idx, section))
            else:
                other_sections.append((idx, section))
        
        # 순서대로 처리: 개념 -> 본문 -> 기타
        sorted_sections = concept_sections + content_sections + other_sections
        print(f"[books]   섹션 순서: 개념 {len(concept_sections)}개, 본문 {len(content_sections)}개, 기타 {len(other_sections)}개")
        
        for idx, section in sorted_sections:
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
                        if not content_dir.exists():
                            print(f"[books]   경고: 본문 이미지 디렉토리가 존재하지 않음: {content_dir}")
                        else:
                            # 패턴1: content_p{page:02d}_*.png (원본 페이지)
                            if work_page > 0:
                                pattern1 = f"content_p{work_page:02d}_*.png"
                                work_images = sorted(list(content_dir.glob(pattern1)))
                                print(f"[books]   본문 이미지 검색 (패턴1: {pattern1}): {len(work_images)}개 발견")
                            
                            # 패턴2: content_p{page+1:02d}_*.png (다음 페이지)
                            if not work_images and work_page > 0:
                                next_page = work_page + 1
                                pattern2 = f"content_p{next_page:02d}_*.png"
                                next_images = sorted(list(content_dir.glob(pattern2)))
                                if next_images:
                                    work_images = next_images
                                    work_page = next_page  # 페이지 번호 업데이트
                                    print(f"[books]   본문 이미지 검색 (패턴2: {pattern2}): {len(work_images)}개 발견")
                            
                            # 패턴3: content_{lecture_id:02d}_*.png (강의 ID 기반)
                            if not work_images:
                                pattern3 = f"content_{lecture_id:02d}_*.png"
                                work_images = sorted(list(content_dir.glob(pattern3)))
                                print(f"[books]   본문 이미지 검색 (패턴3: {pattern3}): {len(work_images)}개 발견")
                            
                            if not work_images:
                                print(f"[books]   경고: 본문 이미지를 찾을 수 없음 (page {work_page})")
                        
                        if work_images:
                            print(f"[books]   본문 섹션에 이미지 {len(work_images)}개 발견")

                            # 본문 텍스트를 이미지 개수로 균등 분할
                            work_content_lines = [line for line in work_content_str.split('\n') if line.strip()]

                            if len(work_images) == 1:
                                work_content_splits = [work_content_str]
                            else:
                                lines_per_work_image = max(1, len(work_content_lines) // len(work_images))
                                work_content_splits = []

                                for img_idx in range(len(work_images)):
                                    start_idx = img_idx * lines_per_work_image
                                    # 마지막 이미지는 남은 텍스트 전체 포함
                                    if img_idx == len(work_images) - 1:
                                        end_idx = len(work_content_lines)
                                    else:
                                        end_idx = start_idx + lines_per_work_image

                                    split_work_content = '\n'.join(work_content_lines[start_idx:end_idx])
                                    work_content_splits.append(split_work_content)
                                    print(f"[books]     본문 이미지 {img_idx + 1}: 라인 {start_idx+1}-{end_idx} ({end_idx - start_idx}줄)")

                            for img_idx, img_path in enumerate(work_images):
                                work_unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                                # 이미지가 1개면 원본 제목 그대로, 여러 개면 번호 추가
                                work_unit_title = work_title if len(work_images) == 1 else f"{work_title} - {img_idx + 1}"

                                # 이 이미지에 해당하는 본문 텍스트 가져오기
                                image_work_content = work_content_splits[img_idx] if img_idx < len(work_content_splits) else ""

                                work_order = lecture_id * 10000 + actual_unit_index
                                work_pdf_ref = {
                                    "page": work_page,
                                    "lecture_id": lecture_id,
                                    "lecture_number": lecture_number,
                                    "lecture_title": lecture_title,
                                    "section_index": actual_unit_index,
                                    "is_work": True,
                                    "image_index": img_idx,
                                    "image_filename": img_path.name,
                                    "full_work_content": work_content_str  # ✅ 전체 작품 텍스트 저장
                                }

                                work_unit = LearningUnit(
                                    unit_id=work_unit_id,
                                    curriculum_id=curriculum_id,
                                    lesson_id=None,
                                    section_type="content",  # 본문 타입
                                    title=work_unit_title,
                                    content=image_work_content,  # ✅ 분할된 본문 텍스트만 포함
                                    order=work_order,
                                    break_points=None,
                                    pdf_references=json.dumps([work_pdf_ref], ensure_ascii=False),
                                )
                                db.add(work_unit)
                                actual_unit_index += 1
                                work_added = True  # 이미지가 있어도 work_added 설정
                                print(f"[books]   본문 이미지 단위 추가: {work_unit_title[:50]} (이미지: {img_path.name}, 텍스트: {len(image_work_content)}자, 전체: {len(work_content_str)}자, order: {work_order})")
                        else:
                            # 이미지가 없으면 기존처럼 1개만 생성
                            work_order = lecture_id * 10000 + actual_unit_index
                            work_pdf_ref = {
                                "page": work_page,
                                "lecture_id": lecture_id,
                                "lecture_number": lecture_number,
                                "lecture_title": lecture_title,
                                "section_index": actual_unit_index,
                                "is_work": True,
                                "full_work_content": work_content_str  # ✅ 이미지가 없어도 전체 작품 내용 저장
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
                            print(f"[books]   작품 섹션 추가 (이미지 없음): {work_title[:50]} (전체 내용: {len(work_content_str)}자, order: {work_order})")
                    elif work_start_idx == 0:
                        print(f"[books]   경고: 작품이 첫 줄부터 시작 (work_start_idx=0), 분리하지 않음")
                    else:
                        print(f"[books]   경고: 작품 시작 위치를 찾을 수 없음 (work_start_idx=None)")
            
            # content가 아직 설정되지 않은 경우 (작품 분리되지 않은 경우)
            if content is None:
                if isinstance(content_raw, list):
                    content = "\n".join(str(line) for line in content_raw)
                else:
                    content = str(content_raw)
            
            # 작품이 분리된 경우에도 개념 부분이 있으면 원본 섹션 저장
            # content가 비어있어도 이미지가 있거나 제목이 있으면 Unit 생성
            # (본문/문제는 이미지만 있어도 학습 가능)
            has_content = content and content.strip()
            has_title = section.get("title") and section.get("title").strip()
            
            if not has_content and not has_title:
                if work_added:
                    print(f"[books]   원본 섹션 '{section.get('title', 'N/A')[:50]}'은(는) 작품이 분리되었고 개념 부분이 없어 저장하지 않음")
                else:
                    print(f"[books]   섹션 '{section.get('title', 'N/A')[:50]}'은(는) 내용과 제목이 모두 없어 저장하지 않음")
                continue  # 다음 섹션으로 넘어감
            
            # content가 비어있으면 제목을 content로 사용 (최소한의 내용 보장)
            if not has_content:
                content = section.get("title", f"{lecture_number}강 {section_type}")
                print(f"[books]   섹션 '{section.get('title', 'N/A')[:50]}'은(는) 내용이 없지만 제목을 사용하여 Unit 생성")
            
            # section.title을 그대로 사용 (예: "(1) 시적 표현의 개념")
            section_title = section.get("title") or f"{lecture_number}강 {section_type}"
            page = section.get("page", 0)
            
            # 해당 페이지의 이미지 찾기 (이미지 단위로 학습 단위 생성)
            # 여러 패턴 시도: 페이지 기반, 강의 ID 기반
            images = []
            if section_type == "concept" and concepts_dir.exists():
                # 패턴1: concept_p{page:02d}_*.png (예: concept_p14_01.png)
                if page > 0:
                    pattern1 = f"concept_p{page:02d}_*.png"
                    all_images = sorted(list(concepts_dir.glob(pattern1)))
                    print(f"[books]   개념 이미지 검색 (패턴1: {pattern1}): {len(all_images)}개 발견")

                    # 같은 페이지의 n번째 섹션이면 n번째 이미지만 선택
                    if all_images:
                        section_idx_in_page = get_section_index_in_page(page, section_type)
                        if section_idx_in_page < len(all_images):
                            images = [all_images[section_idx_in_page]]
                            print(f"[books]   페이지 {page}의 {section_idx_in_page+1}번째 개념 섹션 → 이미지: {images[0].name}")
                        else:
                            print(f"[books]   경고: 페이지 {page}의 {section_idx_in_page+1}번째 섹션이지만 이미지는 {len(all_images)}개만 있음")

                # 패턴2: concept_{lecture_id:02d}_*.png (예: concept_02_*.png)
                if not images:
                    pattern2 = f"concept_{lecture_id:02d}_*.png"
                    images = sorted(list(concepts_dir.glob(pattern2)))
                    print(f"[books]   개념 이미지 검색 (패턴2: {pattern2}): {len(images)}개 발견")

                # 패턴3: concept_*_강의 {lecture_id}.png (예: concept_02_강의 2.png)
                if not images:
                    pattern3 = f"concept_*_강의 {lecture_id}.png"
                    images = sorted(list(concepts_dir.glob(pattern3)))
                    print(f"[books]   개념 이미지 검색 (패턴3: {pattern3}): {len(images)}개 발견")

            elif section_type == "content":
                # 본문 이미지 검색 (디렉토리가 없어도 계속 진행)
                if content_dir.exists():
                    # 패턴1: content_p{page:02d}_*.png (예: content_p14_01.png)
                    if page > 0:
                        pattern1 = f"content_p{page:02d}_*.png"
                        all_images = sorted(list(content_dir.glob(pattern1)))
                        print(f"[books]   본문 이미지 검색 (패턴1: {pattern1}): {len(all_images)}개 발견")

                        # 같은 페이지의 n번째 섹션이면 n번째 이미지만 선택
                        if all_images:
                            section_idx_in_page = get_section_index_in_page(page, section_type)
                            if section_idx_in_page < len(all_images):
                                images = [all_images[section_idx_in_page]]
                                print(f"[books]   페이지 {page}의 {section_idx_in_page+1}번째 본문 섹션 → 이미지: {images[0].name}")
                            else:
                                print(f"[books]   경고: 페이지 {page}의 {section_idx_in_page+1}번째 섹션이지만 이미지는 {len(all_images)}개만 있음")

                    # 패턴2: content_{lecture_id:02d}_*.png (예: content_02_*.png)
                    if not images:
                        pattern2 = f"content_{lecture_id:02d}_*.png"
                        images = sorted(list(content_dir.glob(pattern2)))
                        print(f"[books]   본문 이미지 검색 (패턴2: {pattern2}): {len(images)}개 발견")
                else:
                    print(f"[books]   본문 이미지 디렉토리가 없음: {content_dir} (이미지 없이 Unit 생성)")

            elif section_type == "problem":
                # 문제 이미지 검색 (디렉토리가 없어도 계속 진행)
                if problems_dir.exists():
                    # 패턴1: problem_p{page:02d}_*.png (예: problem_p14_01.png)
                    if page > 0:
                        pattern1 = f"problem_p{page:02d}_*.png"
                        all_images = sorted(list(problems_dir.glob(pattern1)))
                        print(f"[books]   문제 이미지 검색 (패턴1: {pattern1}): {len(all_images)}개 발견")

                        # 같은 페이지의 n번째 섹션이면 n번째 이미지만 선택
                        if all_images:
                            section_idx_in_page = get_section_index_in_page(page, section_type)
                            if section_idx_in_page < len(all_images):
                                images = [all_images[section_idx_in_page]]
                                print(f"[books]   페이지 {page}의 {section_idx_in_page+1}번째 문제 섹션 → 이미지: {images[0].name}")
                            else:
                                print(f"[books]   경고: 페이지 {page}의 {section_idx_in_page+1}번째 섹션이지만 이미지는 {len(all_images)}개만 있음")
                else:
                    print(f"[books]   문제 이미지 디렉토리가 없음: {problems_dir} (이미지 없이 Unit 생성)")
            
            # 이미지가 있으면 각 이미지마다 학습 단위 생성, 없으면 1개만 생성
            if images:
                print(f"[books]   섹션 '{section_title[:50]}'에 이미지 {len(images)}개 발견")

                # 텍스트를 이미지 개수로 균등 분할
                content_lines = []
                if isinstance(content, str):
                    content_lines = [line for line in content.split('\n') if line.strip()]
                elif isinstance(content, list):
                    content_lines = [str(line) for line in content if str(line).strip()]

                # 이미지가 1개면 전체 텍스트, 여러 개면 분할
                if len(images) == 1:
                    content_splits = ['\n'.join(content_lines)]
                else:
                    # 균등 분할: 각 이미지당 할당할 라인 수 계산
                    lines_per_image = max(1, len(content_lines) // len(images))
                    content_splits = []

                    for img_idx in range(len(images)):
                        start_idx = img_idx * lines_per_image
                        # 마지막 이미지는 남은 텍스트 전체 포함
                        if img_idx == len(images) - 1:
                            end_idx = len(content_lines)
                        else:
                            end_idx = start_idx + lines_per_image

                        split_content = '\n'.join(content_lines[start_idx:end_idx])
                        content_splits.append(split_content)
                        print(f"[books]     이미지 {img_idx + 1}: 라인 {start_idx+1}-{end_idx} ({end_idx - start_idx}줄)")

                for img_idx, img_path in enumerate(images):
                    unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                    # 이미지가 1개면 원본 제목 그대로, 여러 개면 번호 추가
                    unit_title = section_title if len(images) == 1 else f"{section_title} - {img_idx + 1}"

                    # 이 이미지에 해당하는 텍스트 가져오기
                    image_content = content_splits[img_idx] if img_idx < len(content_splits) else ""

                    # order = lecture_id * 10000 + actual_unit_index
                    order = lecture_id * 10000 + actual_unit_index

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
                        content=image_content,  # ✅ 분할된 텍스트만 포함
                        order=order,
                        break_points=None,
                        pdf_references=json.dumps([pdf_ref], ensure_ascii=False),
                    )
                    db.add(learning_unit)
                    actual_unit_index += 1
                    print(f"[books]   이미지 단위 저장: {unit_title[:50]} (이미지: {img_path.name}, 텍스트: {len(image_content)}자, order: {order})")
            else:
                # 이미지가 없으면 기존처럼 1개만 생성
                order = lecture_id * 10000 + actual_unit_index
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
        
        # 문제들을 학습 단위로 변환 (개념-본문 순서 이후에 처리)
        problems_raw = lecture_data.get("problems", [])

        # 중복 제거 (순서 유지)
        problems_seen = set()
        problems = []
        for p in problems_raw:
            if p not in problems_seen:
                problems.append(p)
                problems_seen.add(p)

        print(f"[books] 문제 처리 시작: {len(problems)}개 문제 (원본: {len(problems_raw)}개, 중복 제거됨: {len(problems_raw) - len(problems)}개)")

        # 문제 파일 디렉토리 확인 (problems 또는 problems_images)
        problems_dir = data_dir / "problems"  # JSON 파일 디렉토리
        problems_images_dir = data_dir / "problems_images"  # 이미지 디렉토리
        print(f"[books] 문제 JSON 디렉토리: {problems_dir} (존재: {problems_dir.exists()})")
        print(f"[books] 문제 이미지 디렉토리: {problems_images_dir} (존재: {problems_images_dir.exists()})")
        
        # 문제 파일 목록 확인
        problem_files_all = []
        if problems_dir.exists():
            problem_files_all = list(problems_dir.glob('*.json'))
            print(f"[books] 문제 JSON 파일 목록 ({len(problem_files_all)}개): {[f.name for f in problem_files_all[:10]]}")
        elif problems_images_dir.exists():
            # problems_images 디렉토리에서도 JSON 파일 찾기 시도
            problem_files_all = list(problems_images_dir.glob('*.json'))
            print(f"[books] 문제 JSON 파일 목록 (problems_images에서, {len(problem_files_all)}개): {[f.name for f in problem_files_all[:10]]}")
            problems_dir = problems_images_dir  # 대체 경로 사용
        
        # 강의의 시작 페이지 추출 (첫 번째 섹션의 페이지)
        lecture_start_page = None
        if sections:
            for section in sections:
                section_page = section.get('page', 0)
                if section_page > 0:
                    lecture_start_page = section_page
                    break

        print(f"[books] 강의 시작 페이지: {lecture_start_page}")

        for prob_idx, problem_num in enumerate(problems):
            # problem_num이 "01", "02" 등 문자열 형태
            # 문제 파일 찾기 (강의 페이지 범위 기반)

            problem_files = []
            problem_num_padded = problem_num.zfill(2)  # "01", "02" 등

            # 파이프라인에서 저장하는 형식: problem_p{page:02d}_{problem_id}.json
            # 강의 시작 페이지를 기준으로 ±5 페이지 범위 내에서만 검색

            if problems_dir.exists() and lecture_start_page:
                # 페이지 범위: lecture_start_page ~ lecture_start_page + 10
                for page_offset in range(0, 15):  # 최대 15페이지 범위
                    page_num = lecture_start_page + page_offset
                    pattern_file = problems_dir / f"problem_p{page_num:02d}_{problem_num_padded}.json"
                    if pattern_file.exists():
                        problem_files.append(pattern_file)
                        print(f"[books]   문제 {prob_idx + 1} ({problem_num}): 페이지 {page_num} 매칭")
                        break

                # 페이지 기반으로 못 찾으면 전체 검색 (첫 번째만)
                if not problem_files:
                    pattern1_files = list(problems_dir.glob(f"problem_p*_{problem_num_padded}.json"))
                    if pattern1_files:
                        problem_files = [pattern1_files[0]]  # 첫 번째만 사용
                        print(f"[books]   문제 {prob_idx + 1} ({problem_num}): 전체 검색으로 첫 번째 파일 사용 - {pattern1_files[0].name}")
            
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
                    # problems_images_dir에서 이미지 찾기
                    if problem_page > 0 and problems_images_dir.exists():
                        # problem_number를 사용하여 정확한 이미지 찾기
                        try:
                            prob_num_int = int(problem_num)
                            # 패턴1: problem_p{page}_{num}.png
                            pattern1 = f"problem_p{problem_page:02d}_{prob_num_int:02d}.png"
                            prob_img = problems_images_dir / pattern1
                            if prob_img.exists():
                                problem_images = [prob_img]
                                print(f"[books]     이미지 패턴1 매칭: {pattern1}")
                        except ValueError:
                            pass
                        
                        # 패턴2: problem_p{page}_*.png (페이지 기반)
                        if not problem_images:
                            pattern2 = f"problem_p{problem_page:02d}_*.png"
                            all_images = sorted(list(problems_images_dir.glob(pattern2)))
                            if all_images:
                                # problem_num과 매칭되는 이미지 찾기
                                prob_num_padded = problem_num.zfill(2)
                                matched_images = [img for img in all_images if prob_num_padded in img.name]
                                if matched_images:
                                    problem_images = matched_images
                                elif prob_idx < len(all_images):
                                    # 매칭이 없으면 인덱스로 선택
                                    problem_images = [all_images[prob_idx]]
                                print(f"[books]     이미지 패턴2 매칭: {pattern2} -> {len(problem_images)}개")
                        
                        # 패턴3: *{problem_num}*.png (문제 번호 기반)
                        if not problem_images:
                            prob_num_padded = problem_num.zfill(2)
                            pattern3 = f"*{prob_num_padded}*.png"
                            all_images = sorted(list(problems_images_dir.glob(pattern3)))
                            if all_images:
                                problem_images = all_images[:1]  # 첫 번째만 사용
                                print(f"[books]     이미지 패턴3 매칭: {pattern3} -> {len(problem_images)}개")
                    
                    # 이미지가 있으면 각 이미지마다 학습 단위 생성, 없으면 1개만 생성
                    if problem_images:
                        print(f"[books]   문제 {prob_idx + 1} ({problem_num}): 이미지 {len(problem_images)}개 발견")
                        for img_idx, img_path in enumerate(problem_images):
                            unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                            # 이미지가 1개면 원본 제목 그대로, 여러 개면 번호 추가
                            unit_title = problem_title if len(problem_images) == 1 else f"{problem_title} - 이미지 {img_idx + 1}"
                            
                            order = lecture_id * 10000 + actual_unit_index
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
                        order = lecture_id * 10000 + actual_unit_index
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
                # 문제 파일을 찾지 못한 경우
                print(f"[books]   경고: 문제 파일을 찾을 수 없음 (번호: {problem_num}, 페이지: {lecture_start_page})")
                if problems_dir.exists():
                    all_files = list(problems_dir.glob('*.json'))
                    if all_files:
                        print(f"[books]   디렉토리 내 JSON 파일 ({len(all_files)}개): {[f.name for f in all_files[:10]]}")
                    else:
                        print(f"[books]   디렉토리 내 JSON 파일 없음")
                else:
                    print(f"[books]   문제 디렉토리가 존재하지 않음: {problems_dir}")
                print(f"[books]   기본 문제 Unit 생성 (파일 없음)")
                
                unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                order = lecture_id * 10000 + actual_unit_index
                actual_unit_index += 1
                
                problem_title = f"문제 {problem_num}"
                problem_full_text = f"문제 {problem_num} (파일을 찾을 수 없음)"
                
                pdf_ref = {
                    "page": 0,
                    "lecture_id": lecture_id,
                    "lecture_number": lecture_number,
                    "lecture_title": lecture_title,
                    "problem_number": problem_num,
                    "problem_index": prob_idx
                }
                
                problem_metadata = {
                    "problem_id": problem_num,
                    "choices": [],
                    "answer": None,
                    "question_text": problem_full_text,
                }
                
                learning_unit = LearningUnit(
                    unit_id=unit_id,
                    curriculum_id=curriculum_id,
                    lesson_id=None,
                    section_type="problem",
                    title=problem_title,
                    content=problem_full_text,
                    order=order,
                    break_points=None,
                    pdf_references=json.dumps([pdf_ref], ensure_ascii=False),
                    subject_metadata=json.dumps(problem_metadata, ensure_ascii=False),
                )
                db.add(learning_unit)
                print(f"[books]   기본 문제 Unit 저장: {problem_title} (order: {order})")
    
    db.commit()
    total_units = db.query(LearningUnit).filter(LearningUnit.curriculum_id == curriculum_id).count()
    print(f"[books] 커리큘럼 생성 완료: {curriculum_id}")
    print(f"[books]   처리된 강의 수: {len(lectures)}개")
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

    # LearningUnit → Unit 변환 (프론트엔드 호환성)
    print(f"[books] 프론트엔드 호환을 위해 LearningUnit → Lesson + Unit 변환 시작")
    conversion_stats = _convert_learning_units_to_units(
        curriculum_id=curriculum_id,
        book_id=book_id,
        db=db
    )
    print(f"[books] 변환 완료: {conversion_stats['lessons_created']}개 Lesson, {conversion_stats['units_created']}개 Unit")

    return curriculum_id


def _process_pdf_background(book_id: str, pdf_path: Path, subject: str, ai_options: dict = None):
    """백그라운드에서 PDF 파이프라인 실행 (UnifiedPipeline 직접 사용)"""
    import sys
    import logging
    from app.processing.pipeline import UnifiedPipeline
    from app.db.models import Book, ParseStatus
    from app.db.session import SessionLocal
    from app.core.config import settings

    # 즉시 출력을 위한 print 사용 (백그라운드 작업에서는 logger가 제대로 작동하지 않을 수 있음)
    print(f"[books] ========================================")
    print(f"[books] [백그라운드] PDF 파이프라인 시작")
    print(f"[books] ========================================")
    print(f"[books] book_id: {book_id}")
    print(f"[books] PDF 경로: {pdf_path}")
    print(f"[books] PDF 타입: {type(pdf_path)}")
    print(f"[books] PDF 존재 여부: {pdf_path.exists() if pdf_path else 'N/A'}")
    print(f"[books] 과목: {subject}")
    sys.stdout.flush()

    # 로거 설정 (즉시 출력)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 콘솔 핸들러 추가 (이미 있으면 재사용)
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if ai_options is None:
        ai_options = {}

    db = SessionLocal()
    try:
        # Subject enum 변환
        subject_enum = Subject(subject)
        pipeline_subject = _subject_to_pipeline_subject(subject_enum)

        print(f"[books] ========================================")
        print(f"[books] PDF 파이프라인 시작")
        print(f"[books] ========================================")
        print(f"[books] PDF 경로: {pdf_path}")
        print(f"[books] 과목: {pipeline_subject}")
        print(f"[books] UnifiedPipeline 사용 (processing 모듈)")
        sys.stdout.flush()
        logger.info(f"[books] AI 옵션: ML dedup={ai_options.get('enable_ml_deduplication', True)}, "
              f"ML class={ai_options.get('enable_ml_classification', True)}, "
              f"DL layout={ai_options.get('enable_layout_analysis', False)}, "
              f"DL math={ai_options.get('enable_math_recognition', False)}, "
              f"LLM meta={ai_options.get('enable_llm_metadata', False)}, "
              f"LLM expl={ai_options.get('enable_llm_explanations', False)}, "
              f"LLM rec={ai_options.get('enable_llm_recommendations', False)}")
        sys.stdout.flush()

        # AI 후처리 활성화 여부 결정 (현재는 ML 후처리 비활성화)
        # enable_ml = (ai_options.get('enable_ml_deduplication', True) or
        #             ai_options.get('enable_ml_classification', True))
        enable_ml = False  # ML 후처리는 아직 비활성화

        # config.json 경로
        config_path = settings.API_DIR / "data" / pipeline_subject / "config.json"
        logger.info(f"[books] config.json 경로: {config_path}")
        logger.info(f"[books] config.json 존재 여부: {config_path.exists() if config_path else 'N/A'}")
        sys.stdout.flush()

        # UnifiedPipeline 실행
        logger.info(f"[books] UnifiedPipeline 초기화 중...")
        sys.stdout.flush()
        pipeline = UnifiedPipeline(
            subject=pipeline_subject,
            use_ocr=True,  # OCR 사용 (PDF 폰트 문제 해결)
            use_ml_postprocess=enable_ml,  # ML 후처리 (현재 비활성화)
            config_path=config_path,
            save_results=True,  # JSON 저장 활성화
            dpi=300,  # DPI 높임 (OCR 품질 개선)
            lang='kor+eng',
            tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Tesseract 경로
            use_parallel=True,  # 병렬 처리 활성화
            max_workers=None,  # CPU 코어 수 자동
            max_pages=None,  # 전체 페이지 처리
        )

        logger.info(f"[books] 파이프라인 설정: DPI=300, 병렬=True, OCR=True (Tesseract)")
        logger.info(f"[books] PDF 파일 확인: {pdf_path}")
        logger.info(f"[books] PDF 파일 존재 여부: {pdf_path.exists() if pdf_path else 'N/A'}")
        if pdf_path and pdf_path.exists():
            logger.info(f"[books] PDF 파일 크기: {pdf_path.stat().st_size} bytes")
        sys.stdout.flush()
        
        try:
            logger.info(f"[books] 파이프라인 실행 시작...")
            sys.stdout.flush()
            result = pipeline.process(pdf_path)
            logger.info(f"[books] 파이프라인 실행 완료")
            sys.stdout.flush()
        except FileNotFoundError as e:
            logger.error(f"[books] ========================================")
            logger.error(f"[books] [에러] PDF 파일을 찾을 수 없습니다")
            logger.error(f"[books] ========================================")
            logger.error(f"[books] 파일 경로: {pdf_path}")
            logger.error(f"[books] 에러 메시지: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"[books] ========================================")
            sys.stdout.flush()
            
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                book.parse_status = ParseStatus.FAILED
                db.commit()
            return
        except Exception as e:
            logger.error(f"[books] ========================================")
            logger.error(f"[books] [에러] 파이프라인 실행 중 예외 발생")
            logger.error(f"[books] ========================================")
            logger.error(f"[books] 에러 타입: {type(e).__name__}")
            logger.error(f"[books] 에러 메시지: {e}")
            logger.error(f"[books] PDF 경로: {pdf_path}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"[books] ========================================")
            sys.stdout.flush()
            
            # 파싱 실패 상태 업데이트
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                book.parse_status = ParseStatus.FAILED
                db.commit()
            return
        
        # 파이프라인 결과 확인
        lectures = result.get('lectures', [])
        problems = result.get('problems', [])
        
        logger.info(f"[books] 파이프라인 결과: 강의 {len(lectures)}개, 문제 {len(problems)}개")
        logger.info(f"[books] PDF 경로: {pdf_path}")
        logger.info(f"[books] 과목: {pipeline_subject}")
        sys.stdout.flush()
        
        # 강의가 없으면 파싱 실패로 처리
        if not lectures:
            logger.warning(f"[books] ========================================")
            logger.warning(f"[books] [경고] 강의를 찾을 수 없습니다. 파싱이 실패했습니다.")
            logger.warning(f"[books] ========================================")
            logger.warning(f"[books] 가능한 원인:")
            logger.warning(f"  1. PDF에 강의 제목이 없거나 인식되지 않음")
            logger.warning(f"  2. 강의 제목 패턴이 PDF 형식과 맞지 않음")
            logger.warning(f"  3. OCR 품질이 낮아 텍스트 추출 실패")
            logger.warning(f"[books] 해결 방법:")
            logger.warning(f"  1. 캐시 삭제: data/{pipeline_subject}/cache/ 폴더 삭제 후 재시도")
            logger.warning(f"  2. 강의 제목 패턴 확인: processing/parsers/literature.py의 lecture_title_patterns 확인")
            logger.warning(f"  3. OCR 품질 확인: Tesseract 한국어 언어팩 설치 확인")
            logger.warning(f"[books] ========================================")
            logger.warning(f"[books] 상세 디버그 로그는 위의 UnifiedPipeline 출력을 확인하세요.")
            logger.warning(f"[books] ========================================")
            sys.stdout.flush()
            
            # 파싱 실패 상태 업데이트
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                book.parse_status = ParseStatus.FAILED
                db.commit()
            return
        
        # 교재 정보 조회 (커리큘럼 생성 전에 필요)
        book = db.query(Book).filter(Book.book_id == book_id).first()
        if not book:
            print(f"[books] 경고: 교재를 찾을 수 없음: {book_id}")
            return

        # 파이프라인 완료 후 커리큘럼 자동 생성
        # 기존 데이터 삭제 (JSON 파일이 새로 생성되었으므로)
        print(f"[books] 기존 데이터 삭제 시작: {book_id}")
        
        # 1. 기존 커리큘럼 및 LearningUnit 삭제
        existing_curricula = db.query(Curriculum).filter(Curriculum.book_id == book_id).all()
        for curriculum in existing_curricula:
            learning_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == curriculum.curriculum_id
            ).all()
            for lu in learning_units:
                db.delete(lu)
            db.delete(curriculum)
            logger.info(f"[books]   Curriculum 삭제: {curriculum.curriculum_id} (LearningUnit {len(learning_units)}개)")
        
        # 2. 기존 Lesson 및 Unit 삭제
        existing_lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        for lesson in existing_lessons:
            units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            for unit in units:
                db.delete(unit)
            db.delete(lesson)
            logger.info(f"[books]   Lesson 삭제: {lesson.lesson_id} (Unit {len(units)}개)")
        
        db.commit()
        logger.info(f"[books] 기존 데이터 삭제 완료: Curriculum {len(existing_curricula)}개, Lesson {len(existing_lessons)}개")
        sys.stdout.flush()
        
        curriculum_id = None
        try:
            # JSON 파일이 생성되었는지 확인 (최대 3초 대기)
            data_dir = settings.API_DIR / "data" / pipeline_subject
            lectures_dir = data_dir / "lectures"
            
            import time
            max_wait = 3  # 최대 3초 대기
            wait_interval = 0.5  # 0.5초마다 확인
            waited = 0
            
            lecture_files = []
            while waited < max_wait:
                lecture_files = sorted(lectures_dir.glob("lecture_*.json"))
                lecture_files = [f for f in lecture_files if f.name != "lectures.json"]
                if lecture_files:
                    break
                time.sleep(wait_interval)
                waited += wait_interval
                logger.info(f"[books] JSON 파일 대기 중... ({waited:.1f}초)")
                sys.stdout.flush()
            
            if not lecture_files:
                logger.warning(f"[books] ⚠️ 경고: JSON 파일이 생성되지 않았습니다. {lectures_dir}")
                logger.warning(f"[books] 파이프라인은 완료되었지만 JSON 파일이 없어 DB 동기화를 건너뜁니다.")
                logger.warning(f"[books] 디렉토리 내용: {list(lectures_dir.glob('*')) if lectures_dir.exists() else '디렉토리 없음'}")
                sys.stdout.flush()
            else:
                logger.info(f"[books] ✅ JSON 파일 확인: {len(lecture_files)}개 발견")
                logger.info(f"[books] JSON → DB 동기화 시작...")
                sys.stdout.flush()
                
                curriculum_id = _create_curriculum_from_pipeline(
                    book_id=book_id,
                    subject_enum=subject_enum,
                    pipeline_subject=pipeline_subject,
                    title=book.title,
                    db=db
                )
                logger.info(f"[books] ✅ 커리큘럼 자동 생성 완료: {curriculum_id}")
                sys.stdout.flush()
                
                # Lesson 개수 확인
                lesson_count = db.query(Lesson).filter(Lesson.book_id == book_id).count()
                unit_count = db.query(Unit).join(Lesson).filter(Lesson.book_id == book_id).count()
                logger.info(f"[books] ✅ 프론트엔드 연동 완료: {lesson_count}개 Lesson, {unit_count}개 Unit 생성됨")
                sys.stdout.flush()
                
                if lesson_count == 0:
                    logger.warning(f"[books] ⚠️ 경고: Lesson이 0개입니다. JSON 파일은 있지만 DB 동기화가 실패했을 수 있습니다.")
                    logger.warning(f"[books] 수동 동기화 시도: /books/{book_id}/sync-from-json")
                    sys.stdout.flush()
        except Exception as e:
            logger.error(f"[books] ❌ 커리큘럼 생성 실패 (파이프라인은 성공): {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 예외가 발생해도 파싱은 완료된 것으로 표시 (JSON 파일은 생성됨)
            logger.warning(f"[books] ⚠️ JSON 파일은 생성되었으므로 수동 동기화 가능: /books/{book_id}/sync-from-json")
            sys.stdout.flush()

        # 파싱 완료 상태 업데이트
        book.parse_status = ParseStatus.DONE
        db.commit()
        
        # 최종 Lesson 개수 확인
        final_lesson_count = db.query(Lesson).filter(Lesson.book_id == book_id).count()
        logger.info(f"[books] ========================================")
        logger.info(f"[books] PDF 파이프라인 완료: {book_id}")
        logger.info(f"[books]   - 강의: {len(lectures)}개")
        logger.info(f"[books]   - 문제: {len(problems)}개")
        logger.info(f"[books]   - 커리큘럼: {curriculum_id}")
        logger.info(f"[books]   - Lesson: {final_lesson_count}개 (프론트엔드 연동)")
        logger.info(f"[books] ========================================")
        sys.stdout.flush()
            
    except Exception as e:
        logger.error(f"[books] ========================================")
        logger.error(f"[books] PDF 파이프라인 전체 실패: {e}")
        logger.error(f"[books] ========================================")
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"[books] ========================================")
        sys.stdout.flush()
        
        # 파싱 실패 상태 업데이트
        try:
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                book.parse_status = ParseStatus.FAILED
                db.commit()
        except Exception as db_error:
            logger.error(f"[books] DB 업데이트 실패: {db_error}")
            sys.stdout.flush()
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
    print(f"[books] ========================================")
    print(f"[books] [업로드] 파일 업로드 시작")
    print(f"[books] ========================================")
    print(f"[books] 파일명: {file.filename}")
    print(f"[books] 파일 크기: {file.size} bytes")
    print(f"[books] 저장 경로: {file_path}")
    print(f"[books] 교재 ID: {book_id}")
    print(f"[books] 과목: {subject}")
    print(f"[books] 제목: {title}")
    sys.stdout.flush()
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    print(f"[books] 파일 저장 완료: {file_path.exists()}, 크기: {file_path.stat().st_size if file_path.exists() else 0} bytes")
    sys.stdout.flush()
    
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
    
    print(f"[books] DB에 교재 생성 완료: {book_id}, 상태: {book.parse_status}")
    sys.stdout.flush()
    
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
    
    print(f"[books] 백그라운드 작업 등록 시작...")
    print(f"[books] 파일 경로: {file_path}")
    print(f"[books] 파일 존재 여부: {file_path.exists()}")
    print(f"[books] 파일 경로 타입: {type(file_path)}")
    sys.stdout.flush()
    
    try:
        background_tasks.add_task(
            _process_pdf_background,
            book_id,
            file_path,
            subject,
            ai_options
        )
        print(f"[books] ✅ 백그라운드 작업 등록 완료: {book_id}")
        print(f"[books] ========================================")
        sys.stdout.flush()
    except Exception as e:
        print(f"[books] ❌ 백그라운드 작업 등록 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        raise
    
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
    
    # 파싱 진행률 계산
    if book.parse_status == ParseStatus.DONE:
        progress = 100
    elif book.parse_status == ParseStatus.FAILED:
        progress = 0
    elif book.parse_status == ParseStatus.PROCESSING:
        # 파싱 중이면 진행률을 추정 (실제로는 파이프라인 단계별로 계산 가능)
        progress = 50  # 중간 단계로 표시
    else:
        progress = 0
    
    return BookParseStatusResponse(
        book_id=book.book_id,
        status=book.parse_status,
        progress=progress,
    )


@router.post("/books/{book_id}/reparse")
async def reparse_book(
    book_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
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
            print(f"[books] 재파싱 시작: {book_id}")

            # 파싱 상태를 PROCESSING으로 업데이트
            book.parse_status = ParseStatus.PROCESSING
            db.commit()

            # 캐시 삭제 (강제 재파싱을 위해)
            pipeline_subject = _subject_to_pipeline_subject(book.subject)
            cache_dir = settings.DATA_DIR / pipeline_subject / "cache"
            if cache_dir.exists():
                print(f"[books] 캐시 삭제: {cache_dir}")
                import shutil
                try:
                    shutil.rmtree(cache_dir)
                except Exception as cache_err:
                    print(f"[books] 캐시 삭제 실패 (계속 진행): {cache_err}")

            # 기본 AI 옵션 (기본 ML 기능만 활성화)
            ai_options = {
                "enable_ml_deduplication": True,
                "enable_ml_classification": True,
                "enable_layout_analysis": False,
                "enable_math_recognition": False,
                "enable_llm_metadata": False,
                "enable_llm_explanations": False,
                "enable_llm_recommendations": False,
                "openai_api_key": None,
                "education_level": "high",
            }

            # 백그라운드에서 PDF 파이프라인 실행
            background_tasks.add_task(
                _process_pdf_background,
                book_id,
                file_path,
                book.subject.value,
                ai_options
            )

            print(f"[books] 재파싱 백그라운드 작업 시작: {book_id}")

            return {
                "ok": True,
                "message": "재파싱이 시작되었습니다.",
                "status": book.parse_status.value if hasattr(book.parse_status, 'value') else str(book.parse_status)
            }
        except Exception as e:
            print(f"[books] 재파싱 실패: {e}")
            import traceback
            traceback.print_exc()

            # 파싱 실패 상태 업데이트
            book.parse_status = ParseStatus.FAILED
            db.commit()

            raise HTTPException(
                status_code=500,
                detail=f"재파싱 중 오류가 발생했습니다: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="PDF 파일만 재파싱할 수 있습니다."
        )


@router.post("/books/{book_id}/sync-from-json")
async def sync_book_from_json(
    book_id: str,
    db: Session = Depends(get_db)
):
    """
    JSON 파일에서 DB로 동기화 (재파싱 없이)
    
    JSON 파일은 이미 생성되어 있지만 DB에 저장되지 않은 경우 사용
    기존 DB 데이터를 삭제하고 새로 저장합니다.
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    try:
        # 기존 데이터 삭제
        print(f"[books] 기존 데이터 삭제 시작: {book_id}")
        
        # 1. 기존 커리큘럼 및 LearningUnit 삭제
        existing_curricula = db.query(Curriculum).filter(Curriculum.book_id == book_id).all()
        for curriculum in existing_curricula:
            # LearningUnit 삭제
            learning_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == curriculum.curriculum_id
            ).all()
            for lu in learning_units:
                db.delete(lu)
            db.delete(curriculum)
            print(f"[books]   Curriculum 삭제: {curriculum.curriculum_id} (LearningUnit {len(learning_units)}개)")
        
        # 2. 기존 Lesson 및 Unit 삭제
        existing_lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        for lesson in existing_lessons:
            # Unit 삭제
            units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            for unit in units:
                db.delete(unit)
            db.delete(lesson)
            print(f"[books]   Lesson 삭제: {lesson.lesson_id} (Unit {len(units)}개)")
        
        db.commit()
        print(f"[books] 기존 데이터 삭제 완료: Curriculum {len(existing_curricula)}개, Lesson {len(existing_lessons)}개")
        
        # Subject enum 변환
        subject_enum = book.subject
        pipeline_subject = _subject_to_pipeline_subject(subject_enum)
        
        print(f"[books] JSON → DB 동기화 시작: {book_id} (과목: {pipeline_subject})")
        
        # 커리큘럼 생성 (JSON 파일 읽기)
        curriculum_id = _create_curriculum_from_pipeline(
            book_id=book_id,
            subject_enum=subject_enum,
            pipeline_subject=pipeline_subject,
            title=book.title,
            db=db
        )
        
        print(f"[books] JSON → DB 동기화 완료: {curriculum_id}")
        
        # Lesson 개수 확인
        lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        
        return {
            "ok": True,
            "message": f"동기화 완료: {len(lessons)}개 강의가 생성되었습니다.",
            "curriculum_id": curriculum_id,
            "lessons_count": len(lessons)
        }
    except Exception as e:
        print(f"[books] JSON → DB 동기화 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"동기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/books/sync-all-from-json")
async def sync_all_books_from_json(
    subject: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    특정 과목의 모든 교재를 JSON에서 DB로 동기화
    
    Args:
        subject: 과목 (korean, math, english) - None이면 모든 과목
    """
    from app.core.config import settings
    
    # 과목별 매핑
    subject_mapping = {
        "korean": ("literature", Subject.KOREAN),
        "literature": ("literature", Subject.KOREAN),
        "math": ("math1", Subject.MATH),
        "english": ("english", Subject.ENGLISH),
    }
    
    results = []
    
    if subject:
        # 특정 과목만 동기화
        if subject.lower() not in subject_mapping:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 과목: {subject}")
        
        pipeline_subject, subject_enum = subject_mapping[subject.lower()]
        books = db.query(Book).filter(Book.subject == subject_enum).all()
        
        for book in books:
            try:
                print(f"[books] {book.book_id} 동기화 시작...")
                
                # 기존 데이터 삭제
                existing_curricula = db.query(Curriculum).filter(Curriculum.book_id == book.book_id).all()
                for curriculum in existing_curricula:
                    learning_units = db.query(LearningUnit).filter(
                        LearningUnit.curriculum_id == curriculum.curriculum_id
                    ).all()
                    for lu in learning_units:
                        db.delete(lu)
                    db.delete(curriculum)
                
                existing_lessons = db.query(Lesson).filter(Lesson.book_id == book.book_id).all()
                for lesson in existing_lessons:
                    units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
                    for unit in units:
                        db.delete(unit)
                    db.delete(lesson)
                
                db.commit()
                
                # JSON → DB 동기화
                curriculum_id = _create_curriculum_from_pipeline(
                    book_id=book.book_id,
                    subject_enum=subject_enum,
                    pipeline_subject=pipeline_subject,
                    title=book.title,
                    db=db
                )
                
                lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
                results.append({
                    "book_id": book.book_id,
                    "title": book.title,
                    "curriculum_id": curriculum_id,
                    "lessons_count": lesson_count,
                    "status": "success"
                })
                print(f"[books] ✅ {book.book_id} 동기화 완료: {lesson_count}개 Lesson")
            except Exception as e:
                print(f"[books] ❌ {book.book_id} 동기화 실패: {e}")
                results.append({
                    "book_id": book.book_id,
                    "title": book.title,
                    "status": "failed",
                    "error": str(e)
                })
    else:
        # 모든 과목 동기화
        for subj_key, (pipeline_subject, subject_enum) in subject_mapping.items():
            books = db.query(Book).filter(Book.subject == subject_enum).all()
            for book in books:
                try:
                    print(f"[books] {book.book_id} ({pipeline_subject}) 동기화 시작...")
                    
                    # 기존 데이터 삭제
                    existing_curricula = db.query(Curriculum).filter(Curriculum.book_id == book.book_id).all()
                    for curriculum in existing_curricula:
                        learning_units = db.query(LearningUnit).filter(
                            LearningUnit.curriculum_id == curriculum.curriculum_id
                        ).all()
                        for lu in learning_units:
                            db.delete(lu)
                        db.delete(curriculum)
                    
                    existing_lessons = db.query(Lesson).filter(Lesson.book_id == book.book_id).all()
                    for lesson in existing_lessons:
                        units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
                        for unit in units:
                            db.delete(unit)
                        db.delete(lesson)
                    
                    db.commit()
                    
                    # JSON → DB 동기화
                    curriculum_id = _create_curriculum_from_pipeline(
                        book_id=book.book_id,
                        subject_enum=subject_enum,
                        pipeline_subject=pipeline_subject,
                        title=book.title,
                        db=db
                    )
                    
                    lesson_count = db.query(Lesson).filter(Lesson.book_id == book.book_id).count()
                    results.append({
                        "book_id": book.book_id,
                        "title": book.title,
                        "subject": pipeline_subject,
                        "curriculum_id": curriculum_id,
                        "lessons_count": lesson_count,
                        "status": "success"
                    })
                    print(f"[books] ✅ {book.book_id} 동기화 완료: {lesson_count}개 Lesson")
                except Exception as e:
                    print(f"[books] ❌ {book.book_id} 동기화 실패: {e}")
                    results.append({
                        "book_id": book.book_id,
                        "title": book.title,
                        "subject": pipeline_subject,
                        "status": "failed",
                        "error": str(e)
                    })
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    total_lessons = sum(r.get("lessons_count", 0) for r in results if r.get("status") == "success")
    
    return {
        "ok": True,
        "message": f"{success_count}개 교재 동기화 완료 (총 {total_lessons}개 Lesson)",
        "results": results
    }


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


@router.delete("/books/{book_id}")
async def delete_book(
    book_id: str,
    db: Session = Depends(get_db)
):
    """
    교재 삭제
    
    교재와 관련된 모든 데이터(레슨, 유닛, 커리큘럼, 학습 단위 등)를 함께 삭제합니다.
    """
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="교재를 찾을 수 없습니다.")
    
    try:
        # 1. 관련 Lesson 및 Unit 명시적으로 삭제
        lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        lesson_count = len(lessons)
        unit_count = 0
        
        # Lesson 삭제 전에 orphaned units 확인 (join이 작동하도록)
        orphaned_units = db.query(Unit).join(Lesson).filter(Lesson.book_id == book_id).all()
        if orphaned_units:
            print(f"[books] 경고: {len(orphaned_units)}개 orphaned unit 발견, 삭제 중...")
            for unit in orphaned_units:
                db.delete(unit)
            unit_count += len(orphaned_units)
        
        # Unit과 관련된 Answer, ReviewQueue 등을 먼저 삭제 (Unit 삭제 전에)
        from app.db.models import Answer, ReviewQueue
        for lesson in lessons:
            lesson_units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            for unit in lesson_units:
                # Answer 삭제
                answers = db.query(Answer).filter(Answer.unit_id == unit.unit_id).all()
                for answer in answers:
                    db.delete(answer)
                # ReviewQueue 삭제
                review_items = db.query(ReviewQueue).filter(ReviewQueue.unit_id == unit.unit_id).all()
                for review_item in review_items:
                    db.delete(review_item)
        
        # 모든 Unit을 삭제
        for lesson in lessons:
            units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            unit_count += len(units)
            for unit in units:
                db.delete(unit)
        
        # 그 다음 모든 Lesson 삭제
        for lesson in lessons:
            db.delete(lesson)
            print(f"[books] Lesson 삭제: {lesson.lesson_id}")
        
        print(f"[books] Lesson 및 Unit 삭제 완료: Lesson {lesson_count}개, Unit {unit_count}개")
        
        # 2. 관련 Curriculum 및 LearningUnit 명시적으로 삭제
        curricula = db.query(Curriculum).filter(Curriculum.book_id == book_id).all()
        curriculum_count = len(curricula)
        learning_unit_count = 0
        
        for curriculum in curricula:
            # LearningUnit 삭제
            learning_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == curriculum.curriculum_id
            ).all()
            learning_unit_count += len(learning_units)
            for lu in learning_units:
                db.delete(lu)
            # Curriculum 삭제
            db.delete(curriculum)
            print(f"[books] Curriculum 삭제: {curriculum.curriculum_id} (LearningUnit {len(learning_units)}개)")
        
        print(f"[books] Curriculum 및 LearningUnit 삭제 완료: Curriculum {curriculum_count}개, LearningUnit {learning_unit_count}개")
        
        # 3. UserProgress에서 book_id를 NULL로 설정 (진행 상황 초기화)
        from app.db.models import UserProgress
        progress_records = db.query(UserProgress).filter(UserProgress.book_id == book_id).all()
        for progress in progress_records:
            progress.book_id = None
            progress.lesson_id = None
            progress.unit_id = None
            progress.syncpoint_id = None
        print(f"[books] UserProgress 초기화: {len(progress_records)}개 레코드")
        
        # 4. PDF 파일 삭제 (file_path가 있는 경우)
        if book.file_path:
            try:
                pdf_path = Path(book.file_path)
                if pdf_path.exists():
                    pdf_path.unlink()
                    print(f"[books] PDF 파일 삭제: {pdf_path}")
            except Exception as e:
                print(f"[books] 경고: PDF 파일 삭제 실패: {e}")
        
        # 5. 데이터 디렉토리 삭제 (api/data/{subject}/ 폴더)
        try:
            subject_str = _subject_to_pipeline_subject(book.subject)
            data_dir = settings.API_DIR / "data" / subject_str
            if data_dir.exists():
                # 주의: 이 디렉토리는 여러 교재가 공유할 수 있으므로
                # 실제로는 교재별로 구분된 데이터만 삭제해야 하지만,
                # 현재 구조상 교재별 구분이 어려우므로 경고만 출력
                print(f"[books] 경고: 데이터 디렉토리 {data_dir}는 여러 교재가 공유할 수 있어 삭제하지 않습니다.")
                print(f"[books]   수동으로 정리하려면: {data_dir}")
        except Exception as e:
            print(f"[books] 경고: 데이터 디렉토리 확인 실패: {e}")
        
        # 6. Book 삭제
        db.delete(book)
        db.commit()
        
        print(f"[books] 교재 삭제 완료: {book_id}")
        print(f"[books]   - Lesson: {lesson_count}개, Unit: {unit_count}개")
        print(f"[books]   - Curriculum: {curriculum_count}개, LearningUnit: {learning_unit_count}개")
        print(f"[books]   - UserProgress: {len(progress_records)}개 초기화")
        
        print(f"[books] 교재 삭제 완료: {book_id} (Curriculum {len(curricula)}개, Progress {len(progress_records)}개 정리, 데이터 디렉토리 삭제)")
        return {"ok": True, "message": "교재가 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        print(f"[books] 교재 삭제 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"교재 삭제 실패: {str(e)}")


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
