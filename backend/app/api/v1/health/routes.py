"""
헬스 체크 라우터
"""
from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter()


@router.get("/health")
async def health():
    """서버 상태 확인"""
    try:
        # 데이터베이스 연결 확인 (선택적)
        from app.infrastructure.database.session import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        finally:
            db.close()
        
        return {
            "ok": True,
            "service": "jeomgeuli-api",
            "database": db_status
        }
    except ImportError:
        # 데이터베이스 모듈을 불러올 수 없는 경우
        return {
            "ok": True,
            "service": "jeomgeuli-api",
            "database": "not_available"
        }
    except Exception as e:
        # 데이터베이스 확인 실패해도 서버는 정상
        return {
            "ok": True,
            "service": "jeomgeuli-api",
            "database": f"check_failed: {str(e)}"
        }
