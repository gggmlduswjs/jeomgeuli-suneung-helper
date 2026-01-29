"""
커리큘럼 생성 서비스
파이프라인 결과를 커리큘럼으로 변환하는 로직
"""
import json
import uuid
import logging
import re
from typing import Optional, Dict, List, Any
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.infrastructure.database.models import (
    Book, Subject, Curriculum, LearningUnit, CurriculumStatus
)
from app.services.book_conversion import convert_learning_units_to_units

logger = logging.getLogger(__name__)

# ML 기반 섹션 분류기 (선택적)
try:
    from app.services.ml_section_classifier import get_section_classifier
    ML_CLASSIFIER_AVAILABLE = True
except ImportError:
    ML_CLASSIFIER_AVAILABLE = False
    # ML 분류기는 선택적 의존성이므로 경고 없이 무시


def create_curriculum_from_pipeline(
    book_id: Optional[str],
    subject_enum: Subject,
    pipeline_subject: str,
    title: str,
    db: Session
) -> str:
    """
    파이프라인 결과를 커리큘럼으로 변환
    
    Args:
        book_id: 교재 ID (None일 수 있음)
        subject_enum: 과목 enum
        pipeline_subject: 파이프라인 과목 문자열 ("literature", "math1", "english")
        title: 커리큘럼 제목
        db: 데이터베이스 세션
        
    Returns:
        생성된 커리큘럼 ID
    """
    # 커리큘럼 ID 생성
    curriculum_id = f"cur_{uuid.uuid4().hex[:12]}"
    
    # 파이프라인 데이터 경로 (교재별로 분리됨)
    # 교재별 디렉토리: data/{subject}/{book_id}/
    data_dir = settings.API_DIR / "data" / pipeline_subject / book_id
    lectures_dir = data_dir / "lectures"
    
    # 과목 검증: pipeline_subject와 subject_enum이 일치하는지 확인
    expected_subject_mapping = {
        "literature": Subject.KOREAN,
        "math1": Subject.MATH,
        "english": Subject.ENGLISH
    }
    expected_subject = expected_subject_mapping.get(pipeline_subject)
    if expected_subject and expected_subject != subject_enum:
        logger.warning(f"[curriculum_service] ⚠️ 경고: pipeline_subject({pipeline_subject})와 subject_enum({subject_enum})이 일치하지 않음!")
        logger.warning(f"[curriculum_service] 예상 과목: {expected_subject}, 실제 과목: {subject_enum}")
    
    # book_id가 있으면 Book의 subject도 검증
    if book_id:
        book = db.query(Book).filter(Book.book_id == book_id).first()
        if book and book.subject != subject_enum:
            logger.warning(f"[curriculum_service] ⚠️ 경고: Book.subject({book.subject})와 subject_enum({subject_enum})이 일치하지 않음!")
            logger.warning(f"[curriculum_service] Book.subject를 {subject_enum}으로 업데이트합니다.")
            book.subject = subject_enum
            db.commit()
    
    # 디렉토리 존재 확인
    if not lectures_dir.exists():
        logger.warning(f"[curriculum_service] ❌ 경고: 강의 디렉토리가 존재하지 않음: {lectures_dir}")
        return curriculum_id
    
    # lectures.json 대신 실제 lecture_*.json 파일들을 직접 읽기
    lecture_files = sorted(lectures_dir.glob("lecture_*.json"))
    # lectures.json은 제외
    lecture_files = [f for f in lecture_files if f.name != "lectures.json"]
    
    if not lecture_files:
        logger.warning(f"[curriculum_service] ❌ 경고: 강의 파일을 찾을 수 없음: {lectures_dir}")
        logger.debug(f"[curriculum_service] 디렉토리 내용: {list(lectures_dir.glob('*'))}")
        return curriculum_id
    
    logger.info(f"[curriculum_service] ✅ JSON 파일 발견: {len(lecture_files)}개")
    
    logger.info(f"[curriculum_service] 발견된 강의 파일: {len(lecture_files)}개")
    
    # 각 파일에서 lecture_id 추출하여 lectures 리스트 생성
    # 과목 검증: JSON 파일의 subject 필드 확인
    lectures = []
    skipped_count = 0
    for lecture_file in lecture_files:
        try:
            with open(lecture_file, "r", encoding="utf-8") as f:
                lecture_data = json.load(f)
            
            # 과목 검증: JSON 파일의 subject가 일치하는지 확인
            json_subject = lecture_data.get("subject", "").lower()
            expected_subject = pipeline_subject.lower()
            
            if json_subject and json_subject != expected_subject:
                logger.warning(f"[curriculum_service] ⚠️ 경고: {lecture_file.name}의 subject({json_subject})가 예상 과목({expected_subject})과 일치하지 않음. 건너뜀.")
                skipped_count += 1
                continue
            
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
            logger.warning(f"[curriculum_service] 경고: 파일 읽기 실패 {lecture_file}: {e}")
            continue
    
    if skipped_count > 0:
        logger.warning(f"[curriculum_service] ⚠️ {skipped_count}개 강의 파일이 과목 불일치로 건너뛰어짐")
    
    if not lectures:
        logger.warning(f"[curriculum_service] 경고: 강의 데이터가 없음")
        return curriculum_id
    
    logger.info(f"[curriculum_service] 로드된 강의: {len(lectures)}개")
    
    # 커리큘럼 생성 (book_id가 None일 수 있음)
    # subject_enum 검증 (데이터 일관성)
    curriculum = Curriculum(
        curriculum_id=curriculum_id,
        book_id=book_id,  # None일 수 있음
        subject=subject_enum,  # 과목 필드 명시적으로 설정
        title=title,
        status=CurriculumStatus.DONE,
        lesson_count=len(lectures),  # 실제 JSON 파일 개수
    )
    db.add(curriculum)
    db.commit()
    db.refresh(curriculum)
    
    logger.info(f"[curriculum_service] Curriculum 생성: {curriculum_id}, 과목: {subject_enum}, 강의: {len(lectures)}개")
    
    # 각 강의(lecture)를 레슨(lesson)으로 변환
    # 각 JSON 파일을 하나의 Lesson으로 변환 (단순화)
    import re
    
    for lecture in lectures:
        lecture_id = lecture.get("lecture_id", 0)
        lecture_number = lecture.get("lecture_number", lecture_id)
        lecture_file = lecture.get("file")
        
        if not lecture_file or not lecture_file.exists():
            logger.warning(f"[curriculum_service] 경고: 강의 파일을 찾을 수 없음: {lecture_file}")
            continue
        
        # 강의 상세 파일 읽기
        with open(lecture_file, "r", encoding="utf-8") as f:
            lecture_data = json.load(f)
        
        # 과목 재검증 (이중 확인)
        json_subject = lecture_data.get("subject", "").lower()
        expected_subject = pipeline_subject.lower()
        if json_subject and json_subject != expected_subject:
            logger.warning(f"[curriculum_service] ⚠️ 경고: {lecture_file.name}의 subject({json_subject})가 예상 과목({expected_subject})과 일치하지 않음. 건너뜀.")
            continue
        
        # lecture_data.title을 레슨 제목으로 사용 (예: "1강 | 시의 표현과 형식 >>> 고전 시가")
        lecture_title = lecture_data.get("title", f"{lecture_number}강")
        
        # 제목이 없거나 너무 짧으면 기본 제목 사용
        if not lecture_title or len(lecture_title.strip()) < 2:
            lecture_title = f"{lecture_number}강"
        
        sections = lecture_data.get("sections", [])
        problems = lecture_data.get("problems", [])  # 문제 목록 추가
        
        # 섹션과 문제가 없어도 최소한 빈 LearningUnit을 생성하여 Lesson이 생성되도록 함
        if not sections and not problems:
            logger.warning(f"[curriculum_service] 경고: 강의 {lecture_id}에 섹션이나 문제가 없음 - 빈 LearningUnit 생성")
            # 빈 LearningUnit 생성 (Lesson이 생성되도록 하기 위함)
            order = lecture_number * 10000
            empty_learning_unit = LearningUnit(
                unit_id=f"lu_{uuid.uuid4().hex[:12]}",
                curriculum_id=curriculum_id,
                section_type="general",
                title=lecture_title,
                content="",
                order=order,
                break_points=None,
                pdf_references=json.dumps([{
                    "lecture_id": lecture_id,
                    "lecture_title": lecture_title,
                    "page": lecture_data.get("page", 0)
                }], ensure_ascii=False),
                subject_metadata=None,
            )
            db.add(empty_learning_unit)
            logger.info(f"[curriculum_service]   빈 LearningUnit 생성: {empty_learning_unit.unit_id} (order: {order})")
            continue
        
        # 섹션 인덱스 추적 (본문/문제 추가 시에도 순서 유지)
        # 실제 DB에 저장되는 순서를 추적
        actual_unit_index = 0
        
        # 각 섹션을 이미지 단위로 학습 단위 변환
        logger.info(f"[curriculum_service] 강의 {lecture_id} ({lecture_number}강): 섹션 {len(sections)}개, 문제 {len(problems)}개 발견")

        # Lesson은 convert_learning_units_to_units에서 생성하므로 여기서는 생성하지 않음
        # LearningUnit만 생성하고, 나중에 Lesson과 Unit으로 변환

        # 이미지 디렉토리 경로 (교재별)
        # 교재별 디렉토리: data/{subject}/{book_id}/
        data_dir = settings.API_DIR / "data" / pipeline_subject / book_id
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
        logger.debug(f"[curriculum_service]   섹션 순서: 개념 {len(concept_sections)}개, 본문 {len(content_sections)}개, 기타 {len(other_sections)}개")
        
        for idx, section in sorted_sections:
            unit_id = f"lu_{uuid.uuid4().hex[:12]}"
            logger.debug(f"[curriculum_service]   섹션 {idx}: type={section.get('type', 'general')}, title={section.get('title', 'N/A')[:50]}")
            
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
                            logger.debug(f"[curriculum_service]   ML 분류: '{section_title[:30]}' -> {section_type} (신뢰도: {classification_result['confidence']:.2f})")
                        else:
                            # 신뢰도가 낮으면 정규식 기반 분류로 Fallback
                            section_type = classification_result["section_type"]
                    except Exception as e:
                        logger.debug(f"[curriculum_service]   ML 섹션 분류 실패, 정규식 사용: {e}")
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
                            logger.debug(f"[curriculum_service]   작품 감지 (ML): {section.get('title', 'N/A')[:50]} (신뢰도: {work_detection['confidence']:.2f})")
                    except Exception as e:
                        logger.debug(f"[curriculum_service]   ML 작품 감지 실패, 정규식 사용: {e}")
                
                # ML 감지 실패 시 정규식 기반 감지 (Fallback)
                if not is_work:
                    import re
                    # 작가명 패턴: "- 박두진, 「해」" 같은 형식
                    work_pattern = r'-\s*[가-힣\s]+,?\s*「[가-힣\s]+」'
                    if re.search(work_pattern, content_text):
                        is_work = True
                        logger.debug(f"[curriculum_service]   작품 감지 (작가명 패턴): {section.get('title', 'N/A')[:50]}")
                    # 또는 content가 시적 표현(반복, 운율 등)을 포함하는 경우
                    elif any(keyword in content_text for keyword in ["해야", "솟아라", "고운", "청산"]):
                        # 시적 반복 패턴 확인
                        if content_text.count("해야") > 2 or content_text.count("솟아라") > 2:
                            is_work = True
                            logger.debug(f"[curriculum_service]   작품 감지 (시적 표현): {section.get('title', 'N/A')[:50]} (해야: {content_text.count('해야')}, 솟아라: {content_text.count('솟아라')})")
            
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
                        
                        logger.debug(f"[curriculum_service]   작품 분리: work_start_idx={work_start_idx}, 개념 줄 수={len(concept_content)}, 작품 줄 수={len(work_content)}")
                        
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
                            logger.warning(f"[curriculum_service]   경고: 본문 이미지 디렉토리가 존재하지 않음: {content_dir}")
                        else:
                            # 패턴1: content_p{page:02d}_*.png (원본 페이지)
                            if work_page > 0:
                                pattern1 = f"content_p{work_page:02d}_*.png"
                                work_images = sorted(list(content_dir.glob(pattern1)))
                                logger.info(f"[curriculum_service]   본문 이미지 검색 (패턴1: {pattern1}): {len(work_images)}개 발견")
                            
                            # 패턴2: content_p{page+1:02d}_*.png (다음 페이지)
                            if not work_images and work_page > 0:
                                next_page = work_page + 1
                                pattern2 = f"content_p{next_page:02d}_*.png"
                                next_images = sorted(list(content_dir.glob(pattern2)))
                                if next_images:
                                    work_images = next_images
                                    work_page = next_page  # 페이지 번호 업데이트
                                    logger.info(f"[curriculum_service]   본문 이미지 검색 (패턴2: {pattern2}): {len(work_images)}개 발견")
                            
                            # 패턴3: content_{lecture_id:02d}_*.png (강의 ID 기반)
                            if not work_images:
                                pattern3 = f"content_{lecture_id:02d}_*.png"
                                work_images = sorted(list(content_dir.glob(pattern3)))
                                logger.info(f"[curriculum_service]   본문 이미지 검색 (패턴3: {pattern3}): {len(work_images)}개 발견")
                            
                            if not work_images:
                                logger.warning(f"[curriculum_service]   경고: 본문 이미지를 찾을 수 없음 (page {work_page})")
                        
                        if work_images:
                            logger.info(f"[curriculum_service]   본문 섹션에 이미지 {len(work_images)}개 발견")

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
                                    logger.debug(f"[curriculum_service]     본문 이미지 {img_idx + 1}: 라인 {start_idx+1}-{end_idx} ({end_idx - start_idx}줄)")

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
                                logger.debug(f"[curriculum_service]   본문 이미지 단위 추가: {work_unit_title[:50]} (이미지: {img_path.name}, 텍스트: {len(image_work_content)}자, 전체: {len(work_content_str)}자, order: {work_order})")
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
                            logger.debug(f"[curriculum_service]   작품 섹션 추가 (이미지 없음): {work_title[:50]} (전체 내용: {len(work_content_str)}자, order: {work_order})")
                    elif work_start_idx == 0:
                        logger.warning(f"[curriculum_service]   경고: 작품이 첫 줄부터 시작 (work_start_idx=0), 분리하지 않음")
                    else:
                        logger.warning(f"[curriculum_service]   경고: 작품 시작 위치를 찾을 수 없음 (work_start_idx=None)")
            
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
                    logger.debug(f"[curriculum_service]   원본 섹션 '{section.get('title', 'N/A')[:50]}'은(는) 작품이 분리되었고 개념 부분이 없어 저장하지 않음")
                else:
                    logger.debug(f"[curriculum_service]   섹션 '{section.get('title', 'N/A')[:50]}'은(는) 내용과 제목이 모두 없어 저장하지 않음")
                continue  # 다음 섹션으로 넘어감
            
            # content가 비어있으면 제목을 content로 사용 (최소한의 내용 보장)
            if not has_content:
                content = section.get("title", f"{lecture_number}강 {section_type}")
                logger.info(f"[curriculum_service]   섹션 '{section.get('title', 'N/A')[:50]}'은(는) 내용이 없지만 제목을 사용하여 Unit 생성")
            
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
                    logger.info(f"[curriculum_service]   개념 이미지 검색 (패턴1: {pattern1}): {len(all_images)}개 발견")

                    # 같은 페이지의 n번째 섹션이면 n번째 이미지만 선택
                    if all_images:
                        section_idx_in_page = get_section_index_in_page(page, section_type)
                        if section_idx_in_page < len(all_images):
                            images = [all_images[section_idx_in_page]]
                            logger.debug(f"[curriculum_service]   페이지 {page}의 {section_idx_in_page+1}번째 개념 섹션 → 이미지: {images[0].name}")
                        else:
                            logger.warning(f"[curriculum_service]   경고: 페이지 {page}의 {section_idx_in_page+1}번째 섹션이지만 이미지는 {len(all_images)}개만 있음")

                # 패턴2: concept_{lecture_id:02d}_*.png (예: concept_02_*.png)
                if not images:
                    pattern2 = f"concept_{lecture_id:02d}_*.png"
                    images = sorted(list(concepts_dir.glob(pattern2)))
                    logger.info(f"[curriculum_service]   개념 이미지 검색 (패턴2: {pattern2}): {len(images)}개 발견")

                # 패턴3: concept_*_강의 {lecture_id}.png (예: concept_02_강의 2.png)
                if not images:
                    pattern3 = f"concept_*_강의 {lecture_id}.png"
                    images = sorted(list(concepts_dir.glob(pattern3)))
                    logger.info(f"[curriculum_service]   개념 이미지 검색 (패턴3: {pattern3}): {len(images)}개 발견")

            elif section_type == "content":
                # 본문 이미지 검색 (디렉토리가 없어도 계속 진행)
                if content_dir.exists():
                    # 패턴1: content_p{page:02d}_*.png (예: content_p14_01.png)
                    if page > 0:
                        pattern1 = f"content_p{page:02d}_*.png"
                        all_images = sorted(list(content_dir.glob(pattern1)))
                        logger.info(f"[curriculum_service]   본문 이미지 검색 (패턴1: {pattern1}): {len(all_images)}개 발견")

                        # 같은 페이지의 n번째 섹션이면 n번째 이미지만 선택
                        if all_images:
                            section_idx_in_page = get_section_index_in_page(page, section_type)
                            if section_idx_in_page < len(all_images):
                                images = [all_images[section_idx_in_page]]
                                logger.debug(f"[curriculum_service]   페이지 {page}의 {section_idx_in_page+1}번째 본문 섹션 → 이미지: {images[0].name}")
                            else:
                                logger.warning(f"[curriculum_service]   경고: 페이지 {page}의 {section_idx_in_page+1}번째 섹션이지만 이미지는 {len(all_images)}개만 있음")

                    # 패턴2: content_{lecture_id:02d}_*.png (예: content_02_*.png)
                    if not images:
                        pattern2 = f"content_{lecture_id:02d}_*.png"
                        images = sorted(list(content_dir.glob(pattern2)))
                        logger.info(f"[curriculum_service]   본문 이미지 검색 (패턴2: {pattern2}): {len(images)}개 발견")
                else:
                    logger.info(f"[curriculum_service]   본문 이미지 디렉토리가 없음: {content_dir} (이미지 없이 Unit 생성)")

            elif section_type == "problem":
                # 문제 이미지 검색 (디렉토리가 없어도 계속 진행)
                if problems_dir.exists():
                    # 패턴1: problem_p{page:02d}_*.png (예: problem_p14_01.png)
                    if page > 0:
                        pattern1 = f"problem_p{page:02d}_*.png"
                        all_images = sorted(list(problems_dir.glob(pattern1)))
                        logger.info(f"[curriculum_service]   문제 이미지 검색 (패턴1: {pattern1}): {len(all_images)}개 발견")

                        # 같은 페이지의 n번째 섹션이면 n번째 이미지만 선택
                        if all_images:
                            section_idx_in_page = get_section_index_in_page(page, section_type)
                            if section_idx_in_page < len(all_images):
                                images = [all_images[section_idx_in_page]]
                                logger.debug(f"[curriculum_service]   페이지 {page}의 {section_idx_in_page+1}번째 문제 섹션 → 이미지: {images[0].name}")
                            else:
                                logger.warning(f"[curriculum_service]   경고: 페이지 {page}의 {section_idx_in_page+1}번째 섹션이지만 이미지는 {len(all_images)}개만 있음")
                else:
                    logger.info(f"[curriculum_service]   문제 이미지 디렉토리가 없음: {problems_dir} (이미지 없이 Unit 생성)")
            
            # 이미지가 있으면 각 이미지마다 학습 단위 생성, 없으면 1개만 생성
            if images:
                logger.info(f"[curriculum_service]   섹션 '{section_title[:50]}'에 이미지 {len(images)}개 발견")

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
                        logger.debug(f"[curriculum_service]     이미지 {img_idx + 1}: 라인 {start_idx+1}-{end_idx} ({end_idx - start_idx}줄)")

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
                        "image_filename": img_path.name,
                        "image_path": section.get('image_path')  # 파싱 단계에서 크롭한 이미지 API 경로
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
                    logger.debug(f"[curriculum_service]   이미지 단위 저장: {unit_title[:50]} (이미지: {img_path.name}, 텍스트: {len(image_content)}자, order: {order})")
            else:
                # 이미지가 없으면 기존처럼 1개만 생성
                order = lecture_id * 10000 + actual_unit_index
                pdf_ref = {
                    "page": page,
                    "lecture_id": lecture_id,
                    "lecture_number": lecture_number,
                    "lecture_title": lecture_title,
                    "section_index": idx,
                    "image_filename": section.get('image_filename'),  # 파싱 단계 이미지 파일명
                    "image_path": section.get('image_path')  # 파싱 단계에서 크롭한 이미지 API 경로
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
                logger.debug(f"[curriculum_service]   섹션 저장 (이미지 없음): {section_title[:50]} (order: {order}, type: {section_type})")
        
        # 문제들을 학습 단위로 변환 (개념-본문 순서 이후에 처리)
        problems_raw = lecture_data.get("problems", [])

        # 중복 제거 (순서 유지)
        problems_seen = set()
        problems = []
        for p in problems_raw:
            if p not in problems_seen:
                problems.append(p)
                problems_seen.add(p)

        logger.debug(f"[curriculum_service] 문제 처리 시작: {len(problems)}개 문제 (원본: {len(problems_raw)}개, 중복 제거됨: {len(problems_raw) - len(problems)}개)")

        # 문제 파일 디렉토리 확인 (problems 또는 problems_images)
        problems_dir = data_dir / "problems"  # JSON 파일 디렉토리
        problems_images_dir = data_dir / "problems_images"  # 이미지 디렉토리
        logger.debug(f"[curriculum_service] 문제 JSON 디렉토리: {problems_dir} (존재: {problems_dir.exists()})")
        logger.debug(f"[curriculum_service] 문제 이미지 디렉토리: {problems_images_dir} (존재: {problems_images_dir.exists()})")
        
        # 문제 파일 목록 확인
        problem_files_all = []
        if problems_dir.exists():
            problem_files_all = list(problems_dir.glob('*.json'))
            logger.debug(f"[curriculum_service] 문제 JSON 파일 목록 ({len(problem_files_all)}개): {[f.name for f in problem_files_all[:10]]}")
        elif problems_images_dir.exists():
            # problems_images 디렉토리에서도 JSON 파일 찾기 시도
            problem_files_all = list(problems_images_dir.glob('*.json'))
            logger.debug(f"[curriculum_service] 문제 JSON 파일 목록 (problems_images에서, {len(problem_files_all)}개): {[f.name for f in problem_files_all[:10]]}")
            problems_dir = problems_images_dir  # 대체 경로 사용
        
        # 강의의 시작 페이지 추출 (첫 번째 섹션의 페이지)
        lecture_start_page = None
        if sections:
            for section in sections:
                section_page = section.get('page', 0)
                if section_page > 0:
                    lecture_start_page = section_page
                    break

        logger.debug(f"[curriculum_service] 강의 시작 페이지: {lecture_start_page}")

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
                        logger.debug(f"[curriculum_service]   문제 {prob_idx + 1} ({problem_num}): 페이지 {page_num} 매칭")
                        break

                # 페이지 기반으로 못 찾으면 전체 검색 (첫 번째만)
                if not problem_files:
                    pattern1_files = list(problems_dir.glob(f"problem_p*_{problem_num_padded}.json"))
                    if pattern1_files:
                        problem_files = [pattern1_files[0]]  # 첫 번째만 사용
                        logger.debug(f"[curriculum_service]   문제 {prob_idx + 1} ({problem_num}): 전체 검색으로 첫 번째 파일 사용 - {pattern1_files[0].name}")
            
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
                                logger.debug(f"[curriculum_service]     이미지 패턴1 매칭: {pattern1}")
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
                                logger.debug(f"[curriculum_service]     이미지 패턴2 매칭: {pattern2} -> {len(problem_images)}개")
                        
                        # 패턴3: *{problem_num}*.png (문제 번호 기반)
                        if not problem_images:
                            prob_num_padded = problem_num.zfill(2)
                            pattern3 = f"*{prob_num_padded}*.png"
                            all_images = sorted(list(problems_images_dir.glob(pattern3)))
                            if all_images:
                                problem_images = all_images[:1]  # 첫 번째만 사용
                                logger.debug(f"[curriculum_service]     이미지 패턴3 매칭: {pattern3} -> {len(problem_images)}개")
                    
                    # 이미지가 있으면 각 이미지마다 학습 단위 생성, 없으면 1개만 생성
                    if problem_images:
                        logger.info(f"[curriculum_service]   문제 {prob_idx + 1} ({problem_num}): 이미지 {len(problem_images)}개 발견")
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
                            logger.debug(f"[curriculum_service]   문제 이미지 단위 저장: {unit_title[:50]} (이미지: {img_path.name}, order: {order})")
                    else:
                        # 이미지가 없으면 기존처럼 1개만 생성
                        unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                        order = lecture_id * 10000 + actual_unit_index
                        actual_unit_index += 1
                        logger.debug(f"[curriculum_service]   문제 {prob_idx + 1} ({problem_num}): {problem_file.name} (이미지 없음, order: {order})")
                        
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
                    logger.warning(f"[curriculum_service]   경고: 문제 파일 읽기 실패 {problem_file}: {e}")
            else:
                # 문제 파일을 찾지 못한 경우
                logger.warning(f"[curriculum_service]   경고: 문제 파일을 찾을 수 없음 (번호: {problem_num}, 페이지: {lecture_start_page})")
                if problems_dir.exists():
                    all_files = list(problems_dir.glob('*.json'))
                    if all_files:
                        logger.debug(f"[curriculum_service]   디렉토리 내 JSON 파일 ({len(all_files)}개): {[f.name for f in all_files[:10]]}")
                    else:
                        logger.debug(f"[curriculum_service]   디렉토리 내 JSON 파일 없음")
                else:
                    logger.debug(f"[curriculum_service]   문제 디렉토리가 존재하지 않음: {problems_dir}")
                logger.info(f"[curriculum_service]   기본 문제 Unit 생성 (파일 없음)")
                
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
                logger.debug(f"[curriculum_service]   기본 문제 Unit 저장: {problem_title} (order: {order})")
    
    db.commit()
    total_units = db.query(LearningUnit).filter(LearningUnit.curriculum_id == curriculum_id).count()
    logger.info(f"[curriculum_service] 커리큘럼 생성 완료: {curriculum_id}")
    logger.debug(f"[curriculum_service]   처리된 강의 수: {len(lectures)}개")
    logger.debug(f"[curriculum_service]   학습 단위 총 개수: {total_units}개")
    
    # 각 강의별 학습 단위 개수 확인
    for lecture in lectures:
        lecture_id = lecture.get("lecture_id", 0)
        lecture_num = lecture.get("lecture_number", lecture_id)
        units_for_lecture = db.query(LearningUnit).filter(
            LearningUnit.curriculum_id == curriculum_id,
            LearningUnit.order >= lecture_num * 10000,
            LearningUnit.order < (lecture_num + 1) * 10000
        ).count()
        logger.debug(f"[curriculum_service]   {lecture_num}강: {units_for_lecture}개 학습 단위")

    # LearningUnit → Unit 변환 (프론트엔드 호환성)
    logger.info(f"[curriculum_service] 프론트엔드 호환을 위해 LearningUnit → Lesson + Unit 변환 시작")
    conversion_stats = convert_learning_units_to_units(
        curriculum_id=curriculum_id,
        book_id=book_id,
        db=db
    )
    logger.info(f"[curriculum_service] 변환 완료: {conversion_stats['lessons_created']}개 Lesson, {conversion_stats['units_created']}개 Unit")

    return curriculum_id



# 헬퍼 함수들 (curriculum.py에서 이동)
def _save_curriculum_to_json(curriculum_id: str, curriculum_data: Dict, uploads_dir: Path, subject: Optional[str] = None):
    """커리큘럼 데이터를 JSON 파일로 저장 (데이터 제작용) - 과목별 폴더로 분리"""
    from datetime import datetime
    
    # 과목별 폴더명 매핑
    subject_map = {
        'korean': 'korean',
        'literature': 'korean',  # 문학도 korean 폴더에
        'math': 'math1',
        'math1': 'math1',
        'english': 'english',
    }
    
    # 과목명 결정
    subject_name = subject or curriculum_data.get('subject', 'general')
    subject_name = subject_name.lower()
    folder_name = subject_map.get(subject_name, 'general')
    
    # 저장 디렉토리 생성 (과목별 폴더)
    json_dir = uploads_dir.parent / "curricula" / folder_name
    json_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON 파일 경로
    json_path = json_dir / f"{curriculum_id}.json"
    
    # 저장할 데이터 구조
    json_data = {
        "curriculum_id": curriculum_id,
        "subject": curriculum_data.get('subject'),
        "total_lessons": curriculum_data.get('total_lessons', 0),
        "total_units": curriculum_data.get('total_units', 0),
        "created_at": datetime.utcnow().isoformat(),
        "lessons": []
    }
    
    # 레슨별 데이터 구조화
    for lesson_data in curriculum_data.get('lessons', []):
        lesson_json = {
            "lesson_number": lesson_data.get('lesson_number', 0),
            "title": lesson_data.get('title', ''),
            "sections": lesson_data.get('sections', []),
            "pdf_references": lesson_data.get('pdf_references', []),
            "dependencies": lesson_data.get('dependencies', []),
            "estimated_time": lesson_data.get('estimated_time', 0),
            "learning_units": []
        }
        
        # 학습 단위 데이터
        for unit_data in lesson_data.get('learning_units', []):
            unit_json = {
                "unit_index": unit_data.get('unit_index', 0),
                "section_type": unit_data.get('section_type', 'general'),
                "section_name": unit_data.get('section_name', unit_data.get('section_type', 'general')),  # 섹션 이름 추가
                "content": unit_data.get('content', ''),
                "key_points": unit_data.get('key_points', []),
                "pdf_references": unit_data.get('pdf_references', []),
                "break_points": unit_data.get('break_points', [])
            }
            lesson_json["learning_units"].append(unit_json)
        
        json_data["lessons"].append(lesson_json)
    
    # 학습 경로 및 연결 정보
    json_data["learning_path"] = curriculum_data.get('learning_path', [])
    json_data["connections"] = curriculum_data.get('connections', [])
    
    # 학습 흐름 정보 추가
    json_data["learning_flow"] = _create_learning_flow(json_data["lessons"], json_data["learning_path"])
    
    # JSON 파일로 저장
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"[curriculum_service] JSON saved to: {json_path}")



def _create_learning_flow(lessons: List[Dict], learning_path: List[Dict]) -> Dict:
    """학습 흐름 정보 생성"""
    flow = {
        "overview": {
            "total_lessons": len(lessons),
            "total_units": sum(len(lesson.get('learning_units', [])) for lesson in lessons),
            "estimated_total_time": sum(lesson.get('estimated_time', 0) for lesson in lessons)
        },
        "sequence": [],
        "lesson_details": {}
    }
    
    # 학습 경로 순서대로 정리
    for path_item in learning_path:
        lesson_num = path_item.get('lesson', path_item.get('order', 0))
        
        # 해당 레슨 찾기
        lesson = next((l for l in lessons if l.get('lesson_number') == lesson_num), None)
        if not lesson:
            continue
        
        # 학습 단위 흐름 생성
        units_flow = []
        for unit in lesson.get('learning_units', []):
            unit_flow = {
                "unit_index": unit.get('unit_index', 0),
                "section_type": unit.get('section_type', 'general'),
                "content_preview": unit.get('content', '')[:100] + '...' if len(unit.get('content', '')) > 100 else unit.get('content', ''),
                "key_points": unit.get('key_points', [])[:3],  # 최대 3개
                "pdf_references": unit.get('pdf_references', [])
            }
            units_flow.append(unit_flow)
        
        # 레슨 상세 정보
        flow["lesson_details"][str(lesson_num)] = {
            "title": lesson.get('title', ''),
            "estimated_time": lesson.get('estimated_time', 0),
            "unit_count": len(lesson.get('learning_units', [])),
            "sections": lesson.get('sections', []),
            "dependencies": lesson.get('dependencies', [])
        }
        
        # 학습 순서에 추가
        flow["sequence"].append({
            "order": path_item.get('order', len(flow["sequence"]) + 1),
            "lesson_number": lesson_num,
            "title": lesson.get('title', ''),
            "units": units_flow
        })
    
    return flow


def _generate_curriculum_background(
    curriculum_id: str,
    subject_enum: Subject,
    hwp_files: List[Any],  # List[UploadFile] - FastAPI UploadFile 타입
    pdf_file: Optional[Any],  # Optional[UploadFile] - FastAPI UploadFile 타입
    db: Session
):
    """
    백그라운드에서 커리큘럼 생성 작업 실행
    
    Args:
        curriculum_id: 커리큘럼 ID
        subject_enum: 과목 enum
        hwp_files: HWP 파일 리스트
        pdf_file: PDF 파일 (선택)
        db: 데이터베이스 세션
    """
    try:
        # 커리큘럼 조회
        curriculum = db.query(Curriculum).filter(
            Curriculum.curriculum_id == curriculum_id
        ).first()
        
        if not curriculum:
            logger.error(f"커리큘럼을 찾을 수 없습니다: {curriculum_id}")
            return
        
        # 상태를 GENERATING으로 설정
        curriculum.status = CurriculumStatus.GENERATING
        db.commit()
        
        # TODO: HWP 파일 처리 로직 구현
        # TODO: PDF 파일 처리 로직 구현
        # TODO: 커리큘럼 데이터 생성 및 저장
        
        # 상태를 COMPLETED로 설정
        curriculum.status = CurriculumStatus.COMPLETED
        curriculum.lesson_count = 0  # TODO: 실제 레슨 수로 업데이트
        db.commit()
        
        logger.info(f"커리큘럼 생성 완료: {curriculum_id}")
        
    except Exception as e:
        logger.error(f"커리큘럼 생성 중 오류 발생: {curriculum_id}, {str(e)}", exc_info=True)
        
        # 오류 발생 시 상태를 FAILED로 설정
        try:
            curriculum = db.query(Curriculum).filter(
                Curriculum.curriculum_id == curriculum_id
            ).first()
            if curriculum:
                curriculum.status = CurriculumStatus.FAILED
                db.commit()
        except Exception as commit_error:
            logger.error(f"상태 업데이트 실패: {str(commit_error)}")


