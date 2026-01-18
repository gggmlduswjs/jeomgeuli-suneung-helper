"""
복습 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models import ReviewQueue, Unit, Lesson
from app.schemas.review import ReviewQueueItem, ReviewComplete
from app.core.config import settings

router = APIRouter()


@router.get("/review/queue", response_model=List[ReviewQueueItem])
async def get_review_queue(
    user_id: str = Query(default=settings.DEFAULT_USER_ID),
    book_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """복습 큐 (오답 복습 리스트)"""
    query = db.query(ReviewQueue).filter(
        ReviewQueue.user_id == user_id,
        ReviewQueue.completed == False,
    )
    
    # book_id 필터링 (선택)
    if book_id:
        # Unit을 통해 book_id 필터링
        query = query.join(Unit).filter(Unit.lesson_id.in_(
            db.query(Lesson.lesson_id).filter(Lesson.book_id == book_id)
        ))
    
    # 우선순위 순으로 정렬
    items = query.order_by(ReviewQueue.priority.desc(), ReviewQueue.created_at.desc()).all()
    
    return [
        ReviewQueueItem(
            unit_id=item.unit_id,
            lesson_id=item.lesson_id,
            reason=item.reason,
            priority=item.priority,
        )
        for item in items
    ]


@router.post("/review/complete", response_model=dict)
async def complete_review(
    data: ReviewComplete,
    db: Session = Depends(get_db),
):
    """복습 완료 체크"""
    item = db.query(ReviewQueue).filter(
        ReviewQueue.user_id == data.user_id,
        ReviewQueue.unit_id == data.unit_id,
        ReviewQueue.completed == False,
    ).first()
    
    if item:
        item.completed = True
        db.commit()
    
    return {"ok": True}
