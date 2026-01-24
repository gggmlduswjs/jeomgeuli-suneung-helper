"""
환경 변수 및 설정 관리
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


# .env 파일 경로 계산 (api/.env)
_config_file_path = Path(__file__).resolve()
_api_dir = _config_file_path.parent.parent.parent  # api/app/core/config.py -> api/
_env_file_path = _api_dir / ".env"

# .env 파일이 있으면 먼저 로드 (pydantic-settings보다 우선)
# main.py에서 이미 로드했을 수 있지만, 여기서도 다시 확인
# Config 로그를 한 번만 출력하도록 플래그 사용
_config_logged = False

if _env_file_path.exists() and not os.getenv('OPENAI_API_KEY'):
    try:
        with open(_env_file_path, 'r', encoding='utf-8-sig') as f:  # BOM 제거
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'OPENAI_API_KEY':
                        os.environ[key] = value
        if not _config_logged:
            print(f"[Config] .env 파일 로드: {_env_file_path}")
            _config_logged = True
    except Exception as e:
        if not _config_logged:
            print(f"[Config] .env 파일 로드 실패: {e}")
            _config_logged = True

# 로그는 한 번만 출력 (병렬 처리 시 중복 방지)
if not _config_logged:
    api_key_status = '설정됨' if os.getenv('OPENAI_API_KEY') else '설정 안됨'
    if api_key_status == '설정됨':
        print(f"[Config] OPENAI_API_KEY: {api_key_status}")
    _config_logged = True

class Settings(BaseSettings):
    # 프로젝트 루트 경로 (api 폴더의 부모)
    # config.py 위치: api/app/core/config.py
    # .parent.parent.parent = api/
    # .parent = 프로젝트 루트
    BASE_DIR: Path = _api_dir.parent
    # API 폴더 경로
    API_DIR: Path = _api_dir
    
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
    
    # Roboflow API 설정 (YOLO 모델 사용 시)
    ROBOFLOW_API_KEY: Optional[str] = None
    ROBOFLOW_WORKSPACE_ID: Optional[str] = None
    ROBOFLOW_PROJECT_ID: Optional[str] = None
    
    model_config = SettingsConfigDict(
        # .env 파일은 api/ 폴더에 있음
        env_file=str(_env_file_path),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # .env 파일의 추가 필드는 무시
    )


# 설정 인스턴스
settings = Settings()

# 디버그: 현재 설정된 API 키 확인
print(f"[Config] Settings 인스턴스 생성 후 OPENAI_API_KEY: {'설정됨' if settings.OPENAI_API_KEY else '설정 안됨'}")

# .env 파일에서 환경 변수 직접 로드 (pydantic-settings가 못 읽을 경우 대비)
if not settings.OPENAI_API_KEY and _env_file_path.exists():
    try:
        print(f"[Config] .env 파일 직접 파싱 시도: {_env_file_path}")
        with open(_env_file_path, 'r', encoding='utf-8-sig') as f:  # BOM 제거
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'OPENAI_API_KEY':
                        settings.OPENAI_API_KEY = value
                        os.environ['OPENAI_API_KEY'] = value
                        print(f"[Config] OPENAI_API_KEY 로드 성공 (라인 {line_num})")
                        break
    except Exception as e:
        print(f"[Config] .env 파일 로드 실패: {e}")
        import traceback
        traceback.print_exc()

# 최종 확인
if settings.OPENAI_API_KEY:
    print(f"[Config] 최종 확인: OPENAI_API_KEY 설정됨 (길이: {len(settings.OPENAI_API_KEY)})")
else:
    print(f"[Config] 최종 확인: OPENAI_API_KEY 설정 안됨")
    env_key = os.getenv('OPENAI_API_KEY')
    print(f"[Config] 환경 변수 os.getenv('OPENAI_API_KEY'): {'있음 (길이: ' + str(len(env_key)) + ')' if env_key else '없음'}")
    # 환경 변수에 있으면 settings에 복사
    if env_key and not settings.OPENAI_API_KEY:
        settings.OPENAI_API_KEY = env_key
        print(f"[Config] 환경 변수에서 settings로 복사 완료")

# 디렉토리 생성
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
settings.PARSED_DIR.mkdir(parents=True, exist_ok=True)
settings.LECTURE_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
settings.PDFS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATASETS_DIR.mkdir(parents=True, exist_ok=True)