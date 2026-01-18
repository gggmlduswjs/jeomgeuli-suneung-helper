"""
알림 포인트 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import Syncpoint, Lesson, SyncLog
from app.schemas.syncpoint import SyncpointResponse, SyncLogCreate

router = APIRouter()


@router.get("/lessons/{lesson_id}/syncpoints", response_model=List[SyncpointResponse])
async def list_syncpoints(
    lesson_id: str,
    db: Session = Depends(get_db),
):
    """알림 포인트 목록"""
    # 강 존재 확인
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="강을 찾을 수 없습니다.")
    
    syncpoints = db.query(Syncpoint).filter(
        Syncpoint.lesson_id == lesson_id
    ).order_by(Syncpoint.timestamp_sec).all()
    
    return [
        SyncpointResponse(
            syncpoint_id=sp.syncpoint_id,
            timestamp_sec=sp.timestamp_sec,
            hint_type=sp.hint_type,
            unit_id=sp.unit_id,
        )
        for sp in syncpoints
    ]


@router.post("/syncpoints/log", response_model=dict)
async def log_syncpoint(
    data: SyncLogCreate,
    db: Session = Depends(get_db),
):
    """알림 로그 전송 (확장 프로그램용)"""
    log = SyncLog(
        user_id=data.user_id,
        lesson_id=data.lesson_id,
        syncpoint_id=data.syncpoint_id,
        event=data.event,
    )
    db.add(log)
    db.commit()
    
    return {"ok": True}
