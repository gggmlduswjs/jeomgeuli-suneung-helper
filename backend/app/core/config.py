"""
환경 변수 및 설정 관리
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


# .env 파일 경로 계산 (backend/.env)
_config_file_path = Path(__file__).resolve()
_api_dir = _config_file_path.parent.parent.parent  # backend/app/core/config.py -> backend/
_env_file_path = _api_dir / ".env"

# .env 파일이 있으면 로드 (main.py에서 이미 로드했을 수 있지만, 여기서도 확인)
# OPENAI_API_KEY가 없을 때만 로드 (이미 설정된 경우 덮어쓰지 않음)
if not os.getenv('OPENAI_API_KEY') and _env_file_path.exists():
    from app.utils.env_loader import load_env_file
    load_env_file(_env_file_path, silent=False)

# 데이터베이스 URL (Render.com 환경 변수 지원)
_base_dir = _api_dir.parent
_default_db_url = f"sqlite:///{_base_dir / 'data' / 'db.sqlite3'}"
_database_url = os.getenv("DATABASE_URL", _default_db_url)
# Render.com PostgreSQL URL 형식 변환 (postgres:// -> postgresql://)
if _database_url.startswith("postgres://"):
    _database_url = _database_url.replace("postgres://", "postgresql://", 1)


class Settings(BaseSettings):
    # 프로젝트 루트 경로 (backend 폴더의 부모)
    # config.py 위치: backend/app/core/config.py
    # .parent.parent.parent = backend/
    # .parent = 프로젝트 루트
    BASE_DIR: Path = _api_dir.parent
    # Backend 폴더 경로 (API_DIR은 하위 호환성을 위해 유지)
    API_DIR: Path = _api_dir
    
    # 데이터베이스
    # Render.com 등에서 환경 변수로 제공되면 사용, 없으면 SQLite 사용
    DATABASE_URL: str = _database_url
    
    # 파일 저장 경로
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = DATA_DIR / "uploads"  # API를 통해 업로드된 파일 (PDF, 한글)
    EXTRACTED_DIR: Path = DATA_DIR / "extracted"  # 추출된 텍스트 캐시
    PARSED_DIR: Path = DATA_DIR / "parsed"  # 파싱된 데이터
    # 학습 데이터셋 구축용 원본 파일
    LECTURE_SCRIPTS_DIR: Path = DATA_DIR / "lecture_scripts"  # 한글 파일 (강의 대본) - 과목별 폴더
    PDFS_DIR: Path = DATA_DIR / "pdfs"  # PDF 파일 (교재) - 과목별 하나씩
    DATASETS_DIR: Path = DATA_DIR / "datasets"  # 생성된 데이터셋
    
    # CORS
    # Render.com 환경 변수에서 가져오거나 기본값 사용
    _cors_origins_env = os.getenv("CORS_ORIGINS")
    CORS_ORIGINS: List[str] = (
        _cors_origins_env.split(",") if _cors_origins_env else [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
    )
    
    # 게스트 사용자 ID (MVP 2.0)
    DEFAULT_USER_ID: str = "u_demo"
    
    # 파일 업로드 제한
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # OpenAI API 설정 (AI 기능 사용 시 필요)
    OPENAI_API_KEY: Optional[str] = None
    
    # MathPix API 설정 (수식 OCR 사용 시 선택적)
    MATHPIX_APP_ID: Optional[str] = None
    MATHPIX_APP_KEY: Optional[str] = None

    # Roboflow API 설정 (YOLO 모델 사용 시)
    ROBOFLOW_API_KEY: Optional[str] = None
    ROBOFLOW_WORKSPACE_ID: Optional[str] = None
    ROBOFLOW_PROJECT_ID: Optional[str] = None

    # PDF 처리 도구 경로 (환경 변수로 설정 가능, 없으면 자동 감지)
    POPPLER_PATH: Optional[str] = None
    TESSERACT_CMD: Optional[str] = None
    
    model_config = SettingsConfigDict(
        # .env 파일은 api/ 폴더에 있음
        env_file=str(_env_file_path),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # .env 파일의 추가 필드는 무시
    )


# 설정 인스턴스
settings = Settings()

# PDF 처리 도구 자동 감지
if not settings.POPPLER_PATH or not settings.TESSERACT_CMD:
    from app.utils.pdf_tools import find_poppler_path, find_tesseract_cmd

    if not settings.POPPLER_PATH:
        detected_poppler = find_poppler_path()
        if detected_poppler:
            settings.POPPLER_PATH = detected_poppler

    if not settings.TESSERACT_CMD:
        detected_tesseract = find_tesseract_cmd()
        if detected_tesseract:
            settings.TESSERACT_CMD = detected_tesseract

# 디버그: 현재 설정된 API 키 확인
print(f"[Config] Settings 인스턴스 생성 후 OPENAI_API_KEY: {'설정됨' if settings.OPENAI_API_KEY else '설정 안됨'}")
print(f"[Config] Poppler path: {settings.POPPLER_PATH or '없음'}")
print(f"[Config] Tesseract cmd: {settings.TESSERACT_CMD or '없음'}")

# .env 파일에서 환경 변수 직접 로드 (pydantic-settings가 못 읽을 경우 대비)
if not settings.OPENAI_API_KEY and _env_file_path.exists():
    from app.utils.env_loader import load_env_file
    load_env_file(_env_file_path, silent=False)
    
    # 환경 변수에서 settings로 복사
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        settings.OPENAI_API_KEY = env_key
        print(f"[Config] OPENAI_API_KEY 환경 변수에서 settings로 복사 완료")

# 최종 확인 (디버그용)
if settings.OPENAI_API_KEY:
    print(f"[Config] 최종 확인: OPENAI_API_KEY 설정됨")
else:
    print(f"[Config] 최종 확인: OPENAI_API_KEY 설정 안됨")

# 디렉토리 생성
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
settings.PARSED_DIR.mkdir(parents=True, exist_ok=True)
settings.LECTURE_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
settings.PDFS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATASETS_DIR.mkdir(parents=True, exist_ok=True)