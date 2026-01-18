"""
환경 변수 및 설정 관리
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 프로젝트 루트 경로
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    
    # 데이터베이스
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'db.sqlite3'}"
    
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
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    
    # 게스트 사용자 ID (MVP 2.0)
    DEFAULT_USER_ID: str = "u_demo"
    
    # 파일 업로드 제한
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # OpenAI API 설정 (AI 기능 사용 시 필요)
    OPENAI_API_KEY: Optional[str] = None
    
    # MathPix API 설정 (수식 OCR 사용 시 선택적)
    MATHPIX_APP_ID: Optional[str] = None
    MATHPIX_APP_KEY: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # .env 파일의 추가 필드는 무시
    )


# 설정 인스턴스
settings = Settings()

# 디렉토리 생성
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
settings.PARSED_DIR.mkdir(parents=True, exist_ok=True)
settings.LECTURE_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
settings.PDFS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATASETS_DIR.mkdir(parents=True, exist_ok=True)