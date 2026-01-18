"""
커리큘럼 관련 라우터
"""
import uuid
import json
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Curriculum, LearningUnit, CurriculumStatus, Subject
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
from app.services.curriculum_template import AutoCurriculumBuilder
from app.core.config import settings

router = APIRouter()


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
    
    print(f"[Curriculum] JSON saved to: {json_path}")


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


def _generate_curriculum_background(
    curriculum_id: str,
    subject: Subject,
    hwp_files: List[UploadFile],
    pdf_file: Optional[UploadFile],
    db: Session,
):
    """백그라운드 커리큘럼 생성 작업"""
    try:
        # 임시 파일 저장
        uploads_dir = Path(settings.UPLOADS_DIR)
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        hwp_paths = []
        for hwp_file in hwp_files:
            file_path = uploads_dir / f"{curriculum_id}_{hwp_file.filename}"
            with open(file_path, "wb") as f:
                content = hwp_file.file.read()
                f.write(content)
            hwp_paths.append(file_path)
        
        pdf_path = None
        if pdf_file:
            pdf_path = uploads_dir / f"{curriculum_id}_{pdf_file.filename}"
            with open(pdf_path, "wb") as f:
                content = pdf_file.file.read()
                f.write(content)
        
        # 커리큘럼 빌더 생성
        builder = AutoCurriculumBuilder(subject)
        
        # 커리큘럼 생성
        curriculum_data = builder.build_curriculum(hwp_paths, pdf_path)
        
        # 학습 단위 저장 (각 레슨별로)
        lesson_count = 0
        global_order = 0  # 전체 학습 단위 순서
        
        for lesson_idx, lesson_data in enumerate(curriculum_data.get('lessons', [])):
            lesson_count += 1
            lesson_number = lesson_data.get('lesson_number', lesson_idx)
            
            # 각 학습 단위 저장 (레슨 번호를 order의 상위 비트로 사용)
            for unit_idx, unit_data in enumerate(lesson_data.get('learning_units', [])):
                unit_id = f"lu_{uuid.uuid4().hex[:12]}"
                
                # order = lesson_number * 10000 + unit_index
                # 이렇게 하면 레슨별로 그룹화 가능
                order = lesson_number * 10000 + unit_idx
                
                learning_unit = LearningUnit(
                    unit_id=unit_id,
                    curriculum_id=curriculum_id,
                    lesson_id=None,  # 추후 Lesson과 연결
                    section_type=unit_data.get('section_type', 'general'),
                    content=unit_data.get('content', ''),
                    order=order,
                    break_points=json.dumps(unit_data.get('break_points', []), ensure_ascii=False) if unit_data.get('break_points') else None,
                    pdf_references=json.dumps(unit_data.get('pdf_references', []), ensure_ascii=False) if unit_data.get('pdf_references') else None,
                )
                db.add(learning_unit)
                global_order += 1
        
        # 커리큘럼 업데이트
        curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
        if curriculum:
            curriculum.status = CurriculumStatus.DONE
            curriculum.lesson_count = lesson_count
            db.commit()
        
        # JSON 파일로 저장 (데이터 백업 및 재사용용) - 과목별 폴더로 저장
        _save_curriculum_to_json(curriculum_id, curriculum_data, uploads_dir, subject.value.lower())
        
        # 임시 파일 정리 (커리큘럼 생성 완료 후)
        try:
            for hwp_path in hwp_paths:
                if hwp_path.exists():
                    hwp_path.unlink()
            if pdf_path and pdf_path.exists():
                pdf_path.unlink()
        except Exception as cleanup_error:
            print(f"[경고] 임시 파일 정리 실패: {cleanup_error}")
        
    except Exception as e:
        # 에러 발생 시 상태 업데이트
        curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
        if curriculum:
            curriculum.status = CurriculumStatus.FAILED
            db.commit()
        print(f"[Curriculum] Error generating curriculum: {e}")


@router.get("/curriculum", response_model=List[CurriculumResponse])
async def list_curricula(
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """커리큘럼 목록 조회"""
    query = db.query(Curriculum)
    
    if subject:
        try:
            subject_enum = Subject(subject.upper())
            query = query.filter(Curriculum.subject == subject_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 과목: {subject}")
    
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
    db: Session = Depends(get_db),
):
    """커리큘럼 상세 조회"""
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다.")
    
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
        
        unit_data = {
            'unit_index': unit_index,
            'section_type': unit.section_type,
            'content': unit.content,
            'key_points': [],
            'pdf_references': json.loads(unit.pdf_references) if unit.pdf_references else []
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
        
        # 레슨 제목 생성 (주요 섹션 타입 기반)
        main_section = sorted(lesson_data['section_types'], key=lambda x: (
            x != 'ot', x != 'general', x
        ))[0] if lesson_data['section_types'] else 'general'
        
        # 학습 단위를 unit_index 순서로 정렬
        lesson_data['learning_units'].sort(key=lambda x: x['unit_index'])
        
        lessons.append(LessonInfo(
            lesson_number=lesson_number,
            title=f"{lesson_number}강 {main_section}",
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


@router.patch("/curriculum/{curriculum_id}", response_model=CurriculumResponse)
async def update_curriculum(
    curriculum_id: str,
    update_data: CurriculumUpdate,
    db: Session = Depends(get_db),
):
    """커리큘럼 수정"""
    curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if not curriculum:
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다.")
    
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
        raise HTTPException(status_code=404, detail="커리큘럼을 찾을 수 없습니다.")
    
    db.delete(curriculum)
    db.commit()
    
    return None
