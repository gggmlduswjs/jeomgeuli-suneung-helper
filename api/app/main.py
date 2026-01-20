"""
FastAPI 메인 애플리케이션
"""
# ⚠️ 중요: 모든 import보다 먼저 .env 파일 로드
import os
from pathlib import Path

# 현재 작업 디렉토리 기준으로 .env 파일 찾기
# uvicorn 실행 위치: api/ 폴더
_current_dir = Path(__file__).resolve().parent.parent  # api/app/main.py -> api/
_env_file = _current_dir / ".env"

# .env 파일 직접 파싱 (load_dotenv가 실패할 경우 대비)
if _env_file.exists():
    try:
        with open(_env_file, 'r', encoding='utf-8-sig') as f:  # BOM 제거
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value  # 환경 변수에 직접 설정
        print(f"[Main] .env 파일 로드 완료: {_env_file}")
        print(f"[Main] OPENAI_API_KEY 로드 여부: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    except Exception as e:
        print(f"[Main] .env 파일 로드 실패: {e}")
else:
    print(f"[Main] .env 파일을 찾을 수 없습니다: {_env_file}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from app.core.config import settings
from app.db.session import init_db
from app.routers import health, subjects, books, lessons, units, progress, answers, curriculum, ai, literature

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

# 라우터 등록 (필수만)
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

# 문학 AI 강의 라우터
try:
    from app.routers import literature_ai
    app.include_router(literature_ai.router, prefix="/api/v1", tags=["literature-ai"])
except ImportError:
    pass

# 정적 파일 서빙 (PDF 캡쳐 이미지)
# 두 경로 모두 확인: data/pdfs/captures와 api/data/pdfs/captures
captures_dir1 = settings.BASE_DIR / "data" / "pdfs" / "captures"
captures_dir2 = settings.API_DIR / "data" / "pdfs" / "captures"

# 우선순위: api/data/pdfs/captures가 있으면 사용, 없으면 data/pdfs/captures 사용
captures_dir = captures_dir2 if captures_dir2.exists() else captures_dir1

if captures_dir.exists():
    app.mount("/api/v1/captures", StaticFiles(directory=str(captures_dir)), name="captures")
    print(f"[Main] 캡쳐 이미지 서빙 활성화: {captures_dir}")
else:
    print(f"[Main] 캡쳐 이미지 디렉토리를 찾을 수 없습니다:")
    print(f"  - 시도 1: {captures_dir1} (존재: {captures_dir1.exists()})")
    print(f"  - 시도 2: {captures_dir2} (존재: {captures_dir2.exists()})")

# 정적 파일 서빙 (강의 대본 JSON 및 블록 JSON)
# api/data/ 디렉토리 전체를 서빙 (korean_1_blocks.json, korean_1_script.json 등)
# 캐시 방지를 위해 커스텀 StaticFiles 사용
from fastapi.responses import FileResponse
from fastapi import Request

data_dir = settings.API_DIR / "data"
if data_dir.exists():
    @app.get("/api/data/{file_path:path}")
    async def serve_data_file(file_path: str, request: Request):
        """JSON 파일 서빙 (캐시 방지)"""
        file_full_path = data_dir / file_path
        if file_full_path.exists() and file_full_path.is_file():
            return FileResponse(
                str(file_full_path),
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    print(f"[Main] 데이터 파일 서빙 활성화: {data_dir} (캐시 비활성화)")


@app.get("/")
async def root():
    return {"message": "점글이 MVP 2.0 API", "version": "2.0.0"}
