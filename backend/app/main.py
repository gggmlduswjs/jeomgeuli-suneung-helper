"""
FastAPI 메인 애플리케이션
"""
# ⚠️ 중요: 모든 import보다 먼저 .env 파일 로드
import os
from pathlib import Path
from app.utils.env_loader import load_env_file

# .env 파일 로드 (backend/ 폴더에서 자동으로 찾음)
_current_dir = Path(__file__).resolve().parent.parent  # backend/app/main.py -> backend/
_env_file = _current_dir / ".env"
load_env_file(_env_file)

# 로드 확인
if os.getenv('OPENAI_API_KEY'):
    print(f"[Main] OPENAI_API_KEY 로드 완료")
else:
    print(f"[Main] OPENAI_API_KEY 로드 안됨")

from fastapi import FastAPI, HTTPException
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from app.core.config import settings
from app.infrastructure.database.session import init_db
from app.routers import books, lessons, units, curriculum, ai, literature, english, math1, braille, templates, health, subjects, answers, progress

# 데이터베이스 초기화 (오류 발생 시에도 앱은 시작)
try:
    init_db()
    print("[Main] 데이터베이스 초기화 완료")
except Exception as e:
    print(f"[Main] 경고: 데이터베이스 초기화 실패 (앱은 계속 실행됩니다): {e}")

app = FastAPI(
    title="점글이 MVP 2.0 API",
    description="시각장애인을 위한 수능 학습 지원 API",
    version="2.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(subjects.router, prefix="/api/v1", tags=["subjects"])
app.include_router(books.router, prefix="/api/v1", tags=["books"])
app.include_router(lessons.router, prefix="/api/v1", tags=["lessons"])
app.include_router(units.router, prefix="/api/v1", tags=["units"])
app.include_router(progress.router, prefix="/api/v1", tags=["progress"])
app.include_router(answers.router, prefix="/api/v1", tags=["answers"])
app.include_router(curriculum.router, prefix="/api/v1", tags=["curriculum"])
app.include_router(ai.router, prefix="/api/v1", tags=["ai"])
app.include_router(literature.router, prefix="/api/v1", tags=["literature"])
app.include_router(english.router, prefix="/api/v1", tags=["english"])
app.include_router(math1.router, prefix="/api/v1", tags=["math1"])
app.include_router(templates.router, prefix="/api/v1", tags=["templates"])
app.include_router(braille.router, prefix="/api", tags=["braille"])  # /api/braille/convert 경로 지원
# literature_ai.py의 기능은 ai.py로 통합됨 (호환성을 위해 /literature/ai/* 경로 유지)

# 정적 파일 서빙 (PDF 캡쳐 이미지)
# 두 경로 모두 확인: data/pdfs/captures와 backend/data/pdfs/captures
captures_dir1 = settings.BASE_DIR / "data" / "pdfs" / "captures"
captures_dir2 = settings.API_DIR / "data" / "pdfs" / "captures"

# 우선순위: backend/data/pdfs/captures가 있으면 사용, 없으면 data/pdfs/captures 사용
captures_dir = captures_dir2 if captures_dir2.exists() else captures_dir1

if captures_dir.exists():
    app.mount("/api/v1/captures", StaticFiles(directory=str(captures_dir)), name="captures")
    print(f"[Main] 캡쳐 이미지 서빙 활성화: {captures_dir}")
else:
    print(f"[Main] 캡쳐 이미지 디렉토리를 찾을 수 없습니다:")
    print(f"  - 시도 1: {captures_dir1} (존재: {captures_dir1.exists()})")
    print(f"  - 시도 2: {captures_dir2} (존재: {captures_dir2.exists()})")

# 정적 파일 서빙 (강의 대본 JSON 및 블록 JSON)
# backend/data/ 디렉토리 전체를 서빙 (/api/data/ 엔드포인트로 접근)
# 캐시 방지를 위해 커스텀 StaticFiles 사용
from fastapi.responses import FileResponse
from fastapi import Request

# 우선순위: backend/data/ 먼저 확인, 없으면 프로젝트 루트 data/
backend_data_dir = settings.API_DIR / "data"
data_dir = settings.DATA_DIR

def find_data_file(file_path: str) -> Optional[Path]:
    """데이터 파일 찾기 (backend/data 우선)"""
    # backend/data/ 먼저 확인
    backend_file = backend_data_dir / file_path
    if backend_file.exists() and backend_file.is_file():
        return backend_file
    
    # 프로젝트 루트 data/ 확인
    root_file = data_dir / file_path
    if root_file.exists() and root_file.is_file():
        return root_file
    
    return None

if backend_data_dir.exists() or data_dir.exists():
    @app.get("/api/data/{file_path:path}")
    async def serve_data_file(file_path: str, request: Request):
        """JSON 파일 및 PDF 서빙 (캐시 방지)"""
        file_full_path = find_data_file(file_path)
        if file_full_path:
            return FileResponse(
                str(file_full_path),
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    print(f"[Main] 데이터 파일 서빙 활성화:")
    print(f"  - backend/data: {backend_data_dir} (존재: {backend_data_dir.exists()})")
    print(f"  - 프로젝트 루트 data: {data_dir} (존재: {data_dir.exists()})")


@app.get("/")
async def root():
    return {"message": "점글이 MVP 2.0 API", "version": "2.0.0"}
