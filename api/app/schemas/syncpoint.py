"""
알림 포인트 관련 Pydantic 스키마
"""
from pydantic import BaseModel
from typing import Optional


class SyncpointResponse(BaseModel):
    syncpoint_id: str
    timestamp_sec: float
    hint_type: Optional[str]
    unit_id: Optional[str]
    
    class Config:
        from_attributes = True


class SyncLogCreate(BaseModel):
    user_id: str
    lesson_id: Optional[str] = None
    syncpoint_id: Optional[str] = None
    event: str  # "BEEP_PLAYED", "JUMP_CLICKED", "SCROLLED", "IGNORED"
