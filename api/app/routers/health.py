"""
헬스 체크 라우터
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """서버 상태 확인"""
    return {"ok": True, "service": "jeomgeuli-api"}
