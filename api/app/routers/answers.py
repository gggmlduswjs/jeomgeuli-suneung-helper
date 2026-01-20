"""
정답/오답 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.db.models import Answer, Unit
from app.schemas.answer import AnswerCreate, AnswerResponse

router = APIRouter()


@router.post("/answers", response_model=AnswerResponse, status_code=201)
async def submit_answer(
    data: AnswerCreate,
    db: Session = Depends(get_db),
):
    """정답/오답 기록"""
    # Unit 존재 확인
    unit = db.query(Unit).filter(Unit.unit_id == data.unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="학습 단위를 찾을 수 없습니다.")
    
    # Answer 생성
    answer_id = f"ans_{uuid.uuid4().hex[:12]}"
    answer = Answer(
        answer_id=answer_id,
        user_id=data.user_id,
        unit_id=data.unit_id,
        selected=data.selected,
        is_correct=data.is_correct,
    )
    db.add(answer)
    db.commit()

    # TODO: 오답인 경우 복습 큐에 추가 (나중에 구현)
    # if not data.is_correct:
    #     create_review_queue_for_wrong_answers(data.user_id, data.unit_id, db)

    return AnswerResponse(answer_id=answer_id, saved=True)
