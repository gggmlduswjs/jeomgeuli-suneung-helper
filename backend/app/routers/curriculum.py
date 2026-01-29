"""
커리큘럼 관련 라우터
"""
import uuid
import json
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Response
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Curriculum, LearningUnit, CurriculumStatus, Subject
from app.schemas.curriculum import (
    CurriculumCreate,
    CurriculumResponse,
    CurriculumDetailResponse,
    CurriculumUpdate,
    CurriculumGenerateRequest,
    LessonInfo,
    LearningPathItem,
    ConnectionInfo
)
from app.core.config import settings
from app.core.exceptions import (
    CurriculumNotFoundException, LessonNotFoundException,
    UnitNotFoundException, InvalidSubjectException
)

# AutoCurriculumBuilder (삭제된 모듈 대체용)
try:
    from app.services.curriculum_template import AutoCurriculumBuilder
except ImportError:
    class AutoCurriculumBuilder:
        def __init__(self, subject: str = "literature"):
            self.subject = subject
        
        def build(self, *args, **kwargs) -> dict:
            raise HTTPException(status_code=501, detail="커리큘럼 자동 생성이 지원되지 않습니다.")
        
        def build_curriculum(self, *args, **kwargs) -> dict:
            raise HTTPException(status_code=501, detail="커리큘럼 자동 생성이 지원되지 않습니다.")


from app.services.curriculum_service import (
    _save_curriculum_to_json,
    _create_learning_flow,
    _generate_curriculum_background,
)
router = APIRouter()



@router.post("/curriculum/generate", response_model=CurriculumResponse, status_code=201)
async def generate_curriculum(
    background_tasks: BackgroundTasks,
    subject: str = Form(...),
    title: str = Form(...),
    book_id: Optional[str] = Form(None),
    hwp_files: List[UploadFile] = File(...),
    pdf_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    커리큘럼 자동 생성
    
    Args:
        subject: 과목 (KOREAN, ENGLISH, MATH)
        title: 커리큘럼 제목
        book_id: 교재 ID (선택)
        hwp_files: 강의대본 HWP 파일 리스트
        pdf_file: PDF 파일 (선택)
        
    Returns:
        생성된 커리큘럼 정보
    """
    # Subject enum 변환
    try:
        subject_enum = Subject(subject.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 과목: {subject}")
    
    # 커리큘럼 ID 생성
    curriculum_id = f"cur_{uuid.uuid4().hex[:12]}"
    
    # 커리큘럼 생성 (DB에 저장)
    curriculum = Curriculum(
        curriculum_id=curriculum_id,
        book_id=book_id,
        subject=subject_enum,
        title=title,
        status=CurriculumStatus.GENERATING,
        lesson_count=0,
    )
    db.add(curriculum)
    db.commit()
    db.refresh(curriculum)
    
    # 백그라운드에서 커리큘럼 생성 작업 실행
    background_tasks.add_task(
        _generate_curriculum_background,
        curriculum_id,
        subject_enum,
        hwp_files,
        pdf_file,
        db
    )
    
    return CurriculumResponse(
        curriculum_id=curriculum.curriculum_id,
        book_id=curriculum.book_id,
        subject=curriculum.subject,
        title=curriculum.title,
        status=curriculum.status,
        lesson_count=curriculum.lesson_count,
        created_at=curriculum.created_at,
        updated_at=curriculum.updated_at,
    )


@router.get("/curriculum", response_model=List[CurriculumResponse])
async def list_curricula(
    subject: Optional[str] = None,
    book_id: Optional[str] = None,
    response: Response = None,
    db: Session = Depends(get_db),
):
    # 캐시 방지 헤더 추가
    if response:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    """커리큘럼 목록 조회"""
    query = db.query(Curriculum)
    
    if subject:
        try:
            subject_enum = Subject(subject.upper())
            query = query.filter(Curriculum.subject == subject_enum)
        except ValueError:
            raise InvalidSubjectException(subject)
    
    if book_id:
        query = query.filter(Curriculum.book_id == book_id)
    
    curricula = query.order_by(Curriculum.created_at.desc()).all()
    
    return [
        CurriculumResponse(
            curriculum_id=c.curriculum_id,
            book_id=c.book_id,
            subject=c.subject,
            title=c.title,
            status=c.status,
            lesson_count=c.lesson_count,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in curricula
    ]


@router.get("/curriculum/{curriculum_id}", response_model=CurriculumDetailResponse)
async def get_curriculum(
    curriculum_id: str,
    response: Response,
    db: Session = Depends(get_db),
):
    """커리큘럼 상세 조회"""
    # 캐시 방지 헤더 추가 (항상 최신 데이터 제공)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise CurriculumNotFoundException(curriculum_id)
    
    # 학습 단위 조회
    learning_units = db.query(LearningUnit).filter(
        LearningUnit.curriculum_id == curriculum_id
    ).order_by(LearningUnit.order).all()
    
    # 학습 단위를 레슨별로 그룹화 (order 기반)
    # order = lesson_number * 10000 + unit_index 형식
    lessons_dict = {}
    
    for unit in learning_units:
        # order에서 레슨 번호 추출
        lesson_number = unit.order // 10000
        unit_index = unit.order % 10000
        
        if lesson_number not in lessons_dict:
            lessons_dict[lesson_number] = {
                'learning_units': [],
                'sections': [],
                'pdf_references': [],
                'section_types': set()
            }
        
        # PDF 참조 정보 파싱
        pdf_refs = json.loads(unit.pdf_references) if unit.pdf_references else []
        
        # 이미지 경로 찾기 (section_type과 page 기반)
        image_path = None
        if pdf_refs and len(pdf_refs) > 0:
            page = pdf_refs[0].get('page', 0)
            if page > 0:
                # 과목별 이미지 디렉토리 결정
                subject_lower = curriculum.subject.value.lower()
                if subject_lower == 'korean':
                    subject_lower = 'literature'  # korean은 literature 폴더 사용
                
                # section_type에 따라 이미지 디렉토리 결정
                if unit.section_type == 'concept':
                    image_dir = f"/api/data/{subject_lower}/concepts_images"
                    # concepts_images에서 해당 페이지의 이미지 찾기
                    concepts_dir = settings.API_DIR / "data" / subject_lower / "concepts_images"
                    if concepts_dir.exists():
                        # 페이지 번호로 시작하는 이미지 찾기
                        pattern = f"concept_p{page:02d}_*.png"
                        matches = sorted(list(concepts_dir.glob(pattern)))
                        if matches:
                            # unit_index를 기반으로 이미지 선택 (같은 페이지에 여러 이미지가 있을 경우)
                            # unit_index가 0이면 첫 번째, 1이면 두 번째 이미지 사용
                            # 하지만 concept는 보통 섹션 순서대로 매칭
                            match_index = min(unit_index, len(matches) - 1) if unit_index >= 0 else 0
                            image_filename = matches[match_index].name
                            image_path = f"{image_dir}/{image_filename}"
                elif unit.section_type == 'problem':
                    image_dir = f"/api/data/{subject_lower}/problems_images"
                    problems_dir = settings.API_DIR / "data" / subject_lower / "problems_images"
                    if problems_dir.exists():
                        # 문제 번호를 우선적으로 사용
                        problem_number = pdf_refs[0].get('problem_number', None)
                        if problem_number:
                            # problem_number가 "01", "02" 등 문자열 형태일 수 있음
                            try:
                                prob_num = int(problem_number)
                                pattern = f"problem_p{page:02d}_{prob_num:02d}.png"
                                prob_file = problems_dir / pattern
                                if prob_file.exists():
                                    image_path = f"{image_dir}/{prob_file.name}"
                            except (ValueError, TypeError):
                                # 숫자 변환 실패 시 기존 로직 사용
                                pattern = f"problem_p{page:02d}_*.png"
                                matches = sorted(list(problems_dir.glob(pattern)))
                                if matches:
                                    # problem_index를 사용 (0부터 시작)
                                    prob_idx = pdf_refs[0].get('problem_index', unit_index)
                                    match_index = min(prob_idx, len(matches) - 1) if prob_idx >= 0 else 0
                                    image_filename = matches[match_index].name
                                    image_path = f"{image_dir}/{image_filename}"
                        else:
                            # problem_number가 없으면 기존 로직 사용
                            pattern = f"problem_p{page:02d}_*.png"
                            matches = sorted(list(problems_dir.glob(pattern)))
                            if matches:
                                prob_idx = pdf_refs[0].get('problem_index', unit_index)
                                match_index = min(prob_idx, len(matches) - 1) if prob_idx >= 0 else 0
                                image_filename = matches[match_index].name
                                image_path = f"{image_dir}/{image_filename}"
                else:
                    # content, example, general 등은 content_images 사용
                    image_dir = f"/api/data/{subject_lower}/content_images"
                    content_dir = settings.API_DIR / "data" / subject_lower / "content_images"
                    if content_dir.exists():
                        # image_filename이 pdf_refs에 있으면 직접 사용
                        image_filename = pdf_refs[0].get('image_filename', None)
                        if image_filename:
                            image_path = f"{image_dir}/{image_filename}"
                        else:
                            # 없으면 패턴으로 찾기
                            pattern = f"content_p{page:02d}_*.png"
                            matches = sorted(list(content_dir.glob(pattern)))
                            if matches:
                                # image_index가 있으면 사용, 없으면 unit_index 사용
                                img_idx = pdf_refs[0].get('image_index', unit_index)
                                match_index = min(img_idx, len(matches) - 1) if img_idx >= 0 else 0
                                image_filename = matches[match_index].name
                                image_path = f"{image_dir}/{image_filename}"
        
        # subject_metadata 파싱 (문제의 경우 선택지와 정답 정보 포함)
        problem_metadata = None
        if unit.section_type == 'problem' and unit.subject_metadata:
            try:
                problem_metadata = json.loads(unit.subject_metadata)
            except:
                pass
        
        unit_data = {
            'unit_index': unit_index,
            'section_type': unit.section_type,
            'title': unit.title,  # title 필드 추가
            'section_name': unit.title or unit.section_type,  # section_name도 title 사용
            'content': unit.content,
            'key_points': [],
            'pdf_references': pdf_refs,
            'image_path': image_path,  # 이미지 경로 추가
            'problem_metadata': problem_metadata  # 문제 메타데이터 (선택지, 정답 등)
        }
        lessons_dict[lesson_number]['learning_units'].append(unit_data)
        lessons_dict[lesson_number]['section_types'].add(unit.section_type)
        
        # PDF 참조 정보 수집
        if unit.pdf_references:
            try:
                refs = json.loads(unit.pdf_references)
                if isinstance(refs, list):
                    lessons_dict[lesson_number]['pdf_references'].extend(refs)
                else:
                    lessons_dict[lesson_number]['pdf_references'].append(refs)
            except:
                pass
    
    # 레슨 정보 생성 (레슨 번호 순서대로)
    lessons = []
    for lesson_number in sorted(lessons_dict.keys()):
        lesson_data = lessons_dict[lesson_number]
        
        # 레슨 제목 추출: pdf_references에서 lecture_title 가져오기
        # api/data/literature/lectures/lecture_XX.json의 title 필드 사용
        lesson_title = None
        if lesson_data['pdf_references']:
            for ref in lesson_data['pdf_references']:
                if isinstance(ref, dict) and ref.get('lecture_title'):
                    lesson_title = ref.get('lecture_title')
                    break
        
        # lecture_title이 없으면 기본 형식 사용
        if not lesson_title:
            main_section = sorted(lesson_data['section_types'], key=lambda x: (
                x != 'ot', x != 'general', x
            ))[0] if lesson_data['section_types'] else 'general'
            lesson_title = f"{lesson_number}강 {main_section}"
        
        # 학습 단위를 unit_index 순서로 정렬 (order에서 추출한 unit_index 사용)
        lesson_data['learning_units'].sort(key=lambda x: x.get('unit_index', 0))
        
        lessons.append(LessonInfo(
            lesson_number=lesson_number,
            title=lesson_title,  # lecture_data.title 사용 (예: "1강 | 시의 표현과 형식 >>> 고전 시가")
            learning_units=lesson_data['learning_units'],
            sections=[],  # 섹션 정보는 추후 추가
            pdf_references=lesson_data['pdf_references'][:10] if lesson_data['pdf_references'] else [],  # 최대 10개만
            dependencies=[],
            estimated_time=len(lesson_data['learning_units']) * 5
        ))
    
    # 학습 경로 생성 (간단한 구현)
    learning_path = [
        LearningPathItem(lesson=i, order=i+1, title=lesson.title)
        for i, lesson in enumerate(lessons)
    ]
    
    # 연결 정보 (간단한 구현)
    connections = [
        ConnectionInfo(
            from_lesson=i,
            to_lesson=i+1,
            type='sequential',
            keywords=[]
        )
        for i in range(len(lessons) - 1)
    ]
    
    return CurriculumDetailResponse(
        curriculum_id=curriculum.curriculum_id,
        book_id=curriculum.book_id,
        subject=curriculum.subject,
        title=curriculum.title,
        status=curriculum.status,
        lesson_count=curriculum.lesson_count,
        lessons=lessons,
        learning_path=learning_path,
        connections=connections,
        total_lessons=len(lessons),
        total_units=len(learning_units),
        created_at=curriculum.created_at,
        updated_at=curriculum.updated_at,
    )


@router.get("/curriculum/{curriculum_id}/lessons/{lesson_number}", response_model=LessonInfo)
async def get_curriculum_lesson(
    curriculum_id: str,
    lesson_number: int,
    db: Session = Depends(get_db),
):
    """커리큘럼의 특정 레슨 조회"""
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise CurriculumNotFoundException(curriculum_id)
    
    # 학습 단위 조회
    learning_units = db.query(LearningUnit).filter(
        LearningUnit.curriculum_id == curriculum_id
    ).order_by(LearningUnit.order).all()
    
    # 해당 레슨 번호의 학습 단위만 필터링
    # order = lesson_number * 10000 + unit_index 형식
    min_order = lesson_number * 10000
    max_order = (lesson_number + 1) * 10000
    
    lesson_units = [
        unit for unit in learning_units
        if min_order <= unit.order < max_order
    ]
    
    if not lesson_units:
        raise HTTPException(status_code=404, detail=f"레슨 {lesson_number}을 찾을 수 없습니다.")
    
    # 학습 단위 데이터 구성
    unit_data_list = []
    section_types = set()
    pdf_references = []
    
    for unit in lesson_units:
        unit_index = unit.order % 10000
        unit_data = {
            'unit_index': unit_index,
            'section_type': unit.section_type,
            'content': unit.content,
            'key_points': [],
            'pdf_references': json.loads(unit.pdf_references) if unit.pdf_references else []
        }
        unit_data_list.append(unit_data)
        section_types.add(unit.section_type)
        
        # PDF 참조 정보 수집
        if unit.pdf_references:
            try:
                refs = json.loads(unit.pdf_references)
                if isinstance(refs, list):
                    pdf_references.extend(refs)
                else:
                    pdf_references.append(refs)
            except:
                pass
    
    # unit_index 순서로 정렬
    unit_data_list.sort(key=lambda x: x['unit_index'])
    
    # 레슨 제목 생성 (주요 섹션 타입 기반)
    main_section = sorted(section_types, key=lambda x: (
        x != 'ot', x != 'general', x
    ))[0] if section_types else 'general'
    
    return LessonInfo(
        lesson_number=lesson_number,
        title=f"{lesson_number}강 {main_section}",
        subject=curriculum.subject,
        learning_units=unit_data_list,
        sections=[],  # 섹션 정보는 추후 추가
        pdf_references=pdf_references[:10] if pdf_references else [],  # 최대 10개만
        dependencies=[],
        estimated_time=len(unit_data_list) * 5
    )


@router.patch("/curriculum/{curriculum_id}", response_model=CurriculumResponse)
async def update_curriculum(
    curriculum_id: str,
    update_data: CurriculumUpdate,
    db: Session = Depends(get_db),
):
    """커리큘럼 수정"""
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise CurriculumNotFoundException(curriculum_id)
    
    if update_data.title:
        curriculum.title = update_data.title
    
    # 학습 경로 업데이트는 추후 구현
    # lessons 업데이트는 추후 구현
    
    db.commit()
    db.refresh(curriculum)
    
    return CurriculumResponse(
        curriculum_id=curriculum.curriculum_id,
        book_id=curriculum.book_id,
        subject=curriculum.subject,
        title=curriculum.title,
        status=curriculum.status,
        lesson_count=curriculum.lesson_count,
        created_at=curriculum.created_at,
        updated_at=curriculum.updated_at,
    )


@router.delete("/curriculum/{curriculum_id}", status_code=204)
async def delete_curriculum(
    curriculum_id: str,
    db: Session = Depends(get_db),
):
    """커리큘럼 삭제"""
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise CurriculumNotFoundException(curriculum_id)
    
    db.delete(curriculum)
    db.commit()
    
    return None


@router.post("/curriculum/{curriculum_id}/lessons/{lesson_number}/units/{unit_id}/extract-text")
async def extract_text_from_image(
    curriculum_id: str,
    lesson_number: int,
    unit_id: str,
    db: Session = Depends(get_db),
):
    """
    학습 단위의 캡처 이미지에서 OCR로 텍스트 추출
    
    이미지 경로: api/data/pdfs/captures/{subject}/lesson_{lesson_number:02d}/{block_id}.png
    추출한 텍스트는 subject_metadata에 저장
    """
    # EnhancedOCR (삭제된 모듈 대체용)
    try:
        from app.services.pdf_extract.enhanced_ocr import EnhancedOCR
    except ImportError:
        class EnhancedOCR:
            def __init__(self, *args, **kwargs):
                pass
            
            def extract(self, *args, **kwargs) -> dict:
                raise HTTPException(status_code=501, detail="Enhanced OCR이 지원되지 않습니다.")
    from PIL import Image
    from datetime import datetime
    from app.core.config import settings
    
    # 학습 단위 확인
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise CurriculumNotFoundException(curriculum_id)
    
    min_order = lesson_number * 10000
    max_order = (lesson_number + 1) * 10000
    
    unit = db.query(LearningUnit).filter(
        LearningUnit.unit_id == unit_id,
        LearningUnit.curriculum_id == curriculum_id,
        LearningUnit.order >= min_order,
        LearningUnit.order < max_order
    ).first()
    
    if not unit:
        raise UnitNotFoundException(unit_id)
    
    # pdf_references에서 block_id 추출
    pdf_refs = json.loads(unit.pdf_references) if unit.pdf_references else {}
    if isinstance(pdf_refs, list):
        block_id = pdf_refs[0].get('block_id') if pdf_refs else None
    else:
        block_id = pdf_refs.get('block_id') if isinstance(pdf_refs, dict) else None
    
    if not block_id:
        raise HTTPException(status_code=400, detail="이미지 블록 ID를 찾을 수 없습니다.")
    
    # 이미지 경로 구성
    subject = curriculum.subject.value.lower()
    image_path = settings.API_DIR / "data" / "pdfs" / "captures" / subject / f"lesson_{lesson_number:02d}" / f"{block_id}.png"
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"이미지 파일을 찾을 수 없습니다: {image_path}")
    
    try:
        # OCR 수행
        ocr = EnhancedOCR(lang='kor+eng')
        image = Image.open(image_path)
        result = ocr.extract_from_page_image(image, page_num=1)
        
        extracted_text = result.get('text', '')
        blocks = result.get('blocks', [])
        
        # 기존 subject_metadata 가져오기
        metadata = {}
        if unit.subject_metadata:
            try:
                metadata = json.loads(unit.subject_metadata)
            except:
                metadata = {}
        
        # 추출한 텍스트 저장
        metadata['extracted_text'] = extracted_text
        metadata['extracted_blocks'] = blocks
        metadata['extraction_timestamp'] = datetime.utcnow().isoformat()
        
        # 문제/보기 텍스트 자동 분리 시도 (간단한 휴리스틱)
        # "①", "②", "③", "④", "⑤" 패턴으로 보기 분리
        if '①' in extracted_text or '1번' in extracted_text:
            lines = extracted_text.split('\n')
            problem_text = []
            choices = []
            current_choice = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 보기 시작 패턴 감지
                if any(marker in line for marker in ['①', '②', '③', '④', '⑤', '1번', '2번', '3번', '4번', '5번']):
                    if current_choice:
                        choices.append(current_choice)
                    # 보기 번호 제거하고 텍스트만 추출
                    choice_text = line
                    for marker in ['①', '②', '③', '④', '⑤']:
                        choice_text = choice_text.replace(marker, '').strip()
                    for marker in ['1번', '2번', '3번', '4번', '5번']:
                        choice_text = choice_text.replace(marker, '').strip()
                    current_choice = choice_text
                elif current_choice:
                    # 현재 보기에 이어서 추가
                    current_choice += ' ' + line
                else:
                    # 문제 지문
                    problem_text.append(line)
            
            if current_choice:
                choices.append(current_choice)
            
            if problem_text:
                metadata['problem_text'] = '\n'.join(problem_text)
            if choices:
                metadata['choices'] = choices
        
        # DB 업데이트
        unit.subject_metadata = json.dumps(metadata, ensure_ascii=False)
        db.commit()
        db.refresh(unit)
        
        return {
            "ok": True,
            "extracted_text": extracted_text,
            "problem_text": metadata.get('problem_text'),
            "choices": metadata.get('choices', []),
            "blocks_count": len(blocks)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR 추출 실패: {str(e)}")
