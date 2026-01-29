"""
교재 관련 변환 및 처리 서비스
LearningUnit → Unit 변환, Subject 매핑 등
"""
import json
import uuid
import logging
from typing import Dict
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.infrastructure.database.models import (
    Subject, UnitType, LearningUnit, Lesson, Unit, Curriculum, Book
)


def subject_to_pipeline_subject(subject: Subject) -> str:
    """Subject enum을 textbook_pipeline의 subject 형식으로 변환"""
    mapping = {
        Subject.KOREAN: "literature",
        Subject.MATH: "math1",
        Subject.ENGLISH: "english",
    }
    return mapping.get(subject, "literature")


def map_section_type_to_unit_type(section_type: str) -> UnitType:
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


def convert_learning_units_to_units(
    curriculum_id: str,
    book_id: str,
    db: Session
) -> Dict[str, int]:
    """
    Curriculum의 LearningUnit들을 Lesson과 Unit으로 변환하여 프론트엔드 호환성 확보

    Args:
        curriculum_id: 커리큘럼 ID
        book_id: 교재 ID
        db: 데이터베이스 세션

    Returns:
        변환 통계 딕셔너리 {"lessons_created": int, "units_created": int}
    """
    logger.info(f"[book_conversion] LearningUnit → Unit 변환 시작: curriculum_id={curriculum_id}")

    # 1. 커리큘럼의 모든 LearningUnit 조회
    learning_units = db.query(LearningUnit).filter(
        LearningUnit.curriculum_id == curriculum_id
    ).order_by(LearningUnit.order).all()

    if not learning_units:
        logger.warning(f"[book_conversion] 변환할 LearningUnit이 없습니다.")
        return {"lessons_created": 0, "units_created": 0}

    # 2. 레슨별로 그룹화 (order = lecture_id * 10000 + unit_index)
    lessons_dict = {}
    for lu in learning_units:
        lesson_number = lu.order // 10000  # lecture_id를 추출

        if lesson_number not in lessons_dict:
            lessons_dict[lesson_number] = []

        lessons_dict[lesson_number].append(lu)

    logger.info(f"[book_conversion] {len(learning_units)}개 LearningUnit을 {len(lessons_dict)}개 레슨으로 그룹화")

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
            except Exception:
                pass

        # 기존 Lesson 확인 (같은 book_id와 index로)
        # Book의 subject도 함께 검증하여 다른 과목 데이터와 섞이지 않도록 함
        existing_lesson = db.query(Lesson).filter(
            Lesson.book_id == book_id,
            Lesson.index == lesson_number
        ).first()
        
        if existing_lesson:
            # Book의 subject 검증
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
                if curriculum and book.subject != curriculum.subject:
                    logger.warning(f"[book_conversion] ⚠️ 경고: Book.subject({book.subject})와 Curriculum.subject({curriculum.subject})이 일치하지 않음!")
                    logger.info(f"[book_conversion] Book.subject를 {curriculum.subject}으로 업데이트합니다.")
                    book.subject = curriculum.subject
                    db.commit()
            
            # 기존 Lesson 업데이트
            existing_lesson.title = lesson_title
            lesson = existing_lesson
            lesson_id = existing_lesson.lesson_id
            logger.info(f"[book_conversion]   Lesson 업데이트: {lesson_id} - {lesson_title}")
            
            # 기존 Lesson의 모든 Unit 삭제 (데이터 일관성 보장)
            existing_units = db.query(Unit).filter(Unit.lesson_id == lesson_id).all()
            if existing_units:
                logger.info(f"[book_conversion]   기존 Unit {len(existing_units)}개 삭제 중...")
                for unit in existing_units:
                    db.delete(unit)
                logger.info(f"[book_conversion]   기존 Unit 삭제 완료")
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
            logger.info(f"[book_conversion]   Lesson 생성: {lesson_id} - {lesson_title}")

        # 각 LearningUnit을 Unit으로 변환
        for lu in lesson_units:
            # UnitType 매핑
            unit_type = map_section_type_to_unit_type(lu.section_type)

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
                                # 우선순위 1: 파싱 단계에서 크롭한 이미지 경로 (image_path)
                                if ref.get('image_path'):
                                    image_paths.append(ref['image_path'])
                                    logger.debug(f"[book_conversion] 파싱 단계 이미지 사용: {ref['image_path']}")
                                # 우선순위 2: 기존 이미지 파일명 (image_filename)
                                elif ref.get('image_filename'):
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

                                        # 교재별 이미지 경로: /api/data/{subject}/{book_id}/{img_dir}/{filename}
                                        img_path = f"/api/data/{subject_lower}/{book_id}/{img_dir}/{ref['image_filename']}"
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
                        # 우선순위 1: 파싱 단계에서 크롭한 이미지 경로
                        if pdf_refs.get('image_path'):
                            image_paths.append(pdf_refs['image_path'])
                            logger.debug(f"[book_conversion] 파싱 단계 이미지 사용: {pdf_refs['image_path']}")
                        # 우선순위 2: 기존 이미지 파일명
                        elif pdf_refs.get('image_filename'):
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

                                # 교재별 이미지 경로: /api/data/{subject}/{book_id}/{img_dir}/{filename}
                                img_path = f"/api/data/{subject_lower}/{book_id}/{img_dir}/{pdf_refs['image_filename']}"
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
                    logger.error(f"[book_conversion] 이미지 경로/전체 작품 내용 추출 실패: {e}")
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
                    logger.debug(f"[book_conversion]   작품 Unit에 전체 작품 내용 저장 (pdf_references에서): {len(full_work_content)}자")
                elif lu.content and len(lu.content) > 100:  # content가 충분히 길면 전체 작품으로 간주
                    # content가 전체 작품 내용인 경우 (이미지가 없을 때)
                    braille_text_value = lu.content
                    logger.debug(f"[book_conversion]   작품 Unit에 전체 작품 내용 저장 (content에서): {len(lu.content)}자")
                elif lu.braille_text and len(lu.braille_text) > 100:
                    # braille_text에 이미 전체 내용이 있는 경우
                    braille_text_value = lu.braille_text
                    logger.debug(f"[book_conversion]   작품 Unit에 전체 작품 내용 저장 (braille_text에서): {len(lu.braille_text)}자")
                elif lu.content:
                    # 작품 내용이 짧아도 content를 사용
                    braille_text_value = lu.content
                    logger.debug(f"[book_conversion]   작품 Unit에 내용 저장: {len(lu.content)}자")
                else:
                    # content도 없으면 기존 braille_text 유지
                    logger.warning(f"[book_conversion]   작품 Unit 내용 없음 (기존 braille_text 유지)")

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
                except Exception:
                    pass

            db.add(unit)
            units_created += 1

        # LearningUnit에 lesson_id 설정 (양방향 참조)
        for lu in lesson_units:
            lu.lesson_id = lesson_id

    # 4. 커밋
    db.commit()

    # 5. 변환 결과 검증
    final_lesson_count = db.query(Lesson).filter(Lesson.book_id == book_id).count()
    final_unit_count = db.query(Unit).join(Lesson).filter(Lesson.book_id == book_id).count()
    
    logger.info(f"[book_conversion] 변환 완료: {lessons_created}개 Lesson 생성, {units_created}개 Unit 생성")
    logger.info(f"[book_conversion] 최종 검증: {final_lesson_count}개 Lesson, {final_unit_count}개 Unit (DB)")
    
    # 경고: 변환된 Unit 수와 실제 DB의 Unit 수가 다를 수 있음 (기존 Unit 삭제 후 재생성)
    if units_created != final_unit_count:
        logger.warning(f"[book_conversion] ⚠️ 주의: 생성된 Unit 수({units_created})와 DB의 Unit 수({final_unit_count})가 다릅니다.")
        logger.info(f"[book_conversion] 이는 기존 Unit을 삭제하고 재생성했기 때문일 수 있습니다.")
    
    # Lesson별 Unit 개수 확인
    lessons = db.query(Lesson).filter(Lesson.book_id == book_id).order_by(Lesson.index).all()
    for lesson in lessons:
        lesson_unit_count = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).count()
        if lesson_unit_count == 0:
            logger.warning(f"[book_conversion] ⚠️ 경고: Lesson {lesson.index} ({lesson.title})에 Unit이 없습니다.")
        else:
            logger.debug(f"[book_conversion]   Lesson {lesson.index} ({lesson.title}): {lesson_unit_count}개 Unit")

    return {
        "lessons_created": lessons_created,
        "units_created": units_created,
        "final_lesson_count": final_lesson_count,
        "final_unit_count": final_unit_count
    }
