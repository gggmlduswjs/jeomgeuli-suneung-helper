"""
진도 관련 라우터
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import UserProgress
from app.schemas.progress import ProgressCreate, ProgressResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/progress", response_model=dict)
async def save_progress(
    data: ProgressCreate,
    db: Session = Depends(get_db),
):
    """진도 저장"""
    # 기존 진도 찾기 또는 생성
    progress = db.query(UserProgress).filter(UserProgress.user_id == data.user_id).first()
    
    if progress:
        # 업데이트
        progress.book_id = data.book_id
        progress.lesson_id = data.lesson_id
        progress.unit_id = data.unit_id
        progress.syncpoint_id = data.syncpoint_id
    else:
        # 생성
        progress = UserProgress(
            user_id=data.user_id,
            book_id=data.book_id,
            lesson_id=data.lesson_id,
            unit_id=data.unit_id,
            syncpoint_id=data.syncpoint_id,
        )
        db.add(progress)
    
    db.commit()
    return {"ok": True}


@router.get("/progress/continue", response_model=ProgressResponse)
async def get_continue(
    user_id: str = Query(default=settings.DEFAULT_USER_ID, description="사용자 ID"),
    db: Session = Depends(get_db),
):
    """이어하기 (현재 학습 위치 반환)"""
    try:
        progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
        
        if not progress:
            # 진도가 없으면 빈 응답
            return ProgressResponse(
                user_id=user_id,
                book_id=None,
                lesson_id=None,
                unit_id=None,
                syncpoint_id=None,
                updated_at=None,
            )
        
        return ProgressResponse(
            user_id=progress.user_id,
            book_id=progress.book_id,
            lesson_id=progress.lesson_id,
            unit_id=progress.unit_id,
            syncpoint_id=progress.syncpoint_id,
            updated_at=progress.updated_at,
        )
    except Exception as e:
        logger.error(f"[progress] Error in get_continue: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
