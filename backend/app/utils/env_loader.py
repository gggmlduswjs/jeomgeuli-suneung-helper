"""
환경 변수 로딩 유틸리티
.env 파일을 안전하게 로드하는 공통 함수
"""
import os
from pathlib import Path
from typing import Optional


def load_env_file(env_file_path: Optional[Path] = None, silent: bool = False) -> bool:
    """
    .env 파일을 로드하고 환경 변수에 설정
    
    Args:
        env_file_path: .env 파일 경로 (None이면 자동으로 찾음)
        silent: True이면 로그를 출력하지 않음
        
    Returns:
        로드 성공 여부
    """
    if env_file_path is None:
        # backend/app/utils/env_loader.py -> backend/
        backend_dir = Path(__file__).resolve().parent.parent.parent
        env_file_path = backend_dir / ".env"
    
    if not env_file_path.exists():
        if not silent:
            print(f"[EnvLoader] .env 파일을 찾을 수 없습니다: {env_file_path}")
        return False
    
    try:
        loaded_count = 0
        with open(env_file_path, 'r', encoding='utf-8-sig') as f:  # BOM 제거
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # 주석이나 빈 줄은 건너뛰기
                if not line or line.startswith('#'):
                    continue
                
                # KEY=VALUE 형식 파싱
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 환경 변수에 설정 (이미 있으면 덮어쓰지 않음)
                    if key and not os.getenv(key):
                        os.environ[key] = value
                        loaded_count += 1
        
        if not silent:
            print(f"[EnvLoader] .env 파일 로드 완료: {env_file_path} ({loaded_count}개 변수)")
        return True
        
    except Exception as e:
        if not silent:
            print(f"[EnvLoader] .env 파일 로드 실패: {e}")
        return False


def get_env_or_default(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    환경 변수를 가져오거나 기본값 반환
    
    Args:
        key: 환경 변수 키
        default: 기본값
        
    Returns:
        환경 변수 값 또는 기본값
    """
    return os.getenv(key, default)
