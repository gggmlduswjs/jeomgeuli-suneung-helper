"""
PDF 처리 도구 자동 감지 유틸리티

환경에 독립적으로 Poppler, Tesseract 경로를 자동 감지합니다.
"""
import os
import platform
import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def find_poppler_path() -> Optional[str]:
    """
    Poppler 경로를 자동으로 찾습니다.

    우선순위:
    1. 환경 변수 POPPLER_PATH
    2. PATH에서 pdftoppm 찾기
    3. 플랫폼별 기본 경로

    Returns:
        Poppler bin 디렉토리 경로 또는 None
    """
    # 1. 환경 변수
    env_path = os.getenv('POPPLER_PATH')
    if env_path and Path(env_path).exists():
        logger.info(f"Poppler found from POPPLER_PATH: {env_path}")
        return env_path

    # 2. PATH에서 pdftoppm 찾기
    pdftoppm = shutil.which('pdftoppm')
    if pdftoppm:
        poppler_bin = str(Path(pdftoppm).parent)
        logger.info(f"Poppler found in PATH: {poppler_bin}")
        return poppler_bin

    # 3. 플랫폼별 기본 경로
    system = platform.system()
    possible_paths = []

    if system == 'Windows':
        possible_paths = [
            r'C:\poppler\Library\bin',
            r'C:\poppler\bin',
            r'C:\Program Files\poppler\bin',
            r'C:\Program Files (x86)\poppler\bin',
        ]
    elif system == 'Linux':
        possible_paths = [
            '/usr/bin',
            '/usr/local/bin',
        ]
    elif system == 'Darwin':  # macOS
        possible_paths = [
            '/usr/local/bin',
            '/opt/homebrew/bin',
            '/usr/bin',
        ]

    for path in possible_paths:
        pdftoppm_path = Path(path) / ('pdftoppm.exe' if system == 'Windows' else 'pdftoppm')
        if pdftoppm_path.exists():
            logger.info(f"Poppler found at default location: {path}")
            return path

    logger.warning("Poppler not found. PDF to image conversion may fail.")
    logger.warning("Install poppler-utils or set POPPLER_PATH environment variable.")
    return None


def find_tesseract_cmd() -> Optional[str]:
    """
    Tesseract 실행 파일 경로를 자동으로 찾습니다.

    우선순위:
    1. 환경 변수 TESSERACT_CMD
    2. PATH에서 tesseract 찾기
    3. 플랫폼별 기본 경로

    Returns:
        Tesseract 실행 파일 경로 또는 None
    """
    # 1. 환경 변수
    env_cmd = os.getenv('TESSERACT_CMD')
    if env_cmd and Path(env_cmd).exists():
        logger.info(f"Tesseract found from TESSERACT_CMD: {env_cmd}")
        return env_cmd

    # 2. PATH에서 tesseract 찾기
    tesseract = shutil.which('tesseract')
    if tesseract:
        logger.info(f"Tesseract found in PATH: {tesseract}")
        return tesseract

    # 3. 플랫폼별 기본 경로
    system = platform.system()
    possible_paths = []

    if system == 'Windows':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]
    elif system == 'Linux':
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
        ]
    elif system == 'Darwin':  # macOS
        possible_paths = [
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            '/usr/bin/tesseract',
        ]

    for path in possible_paths:
        if Path(path).exists():
            logger.info(f"Tesseract found at default location: {path}")
            return path

    logger.warning("Tesseract not found. OCR functionality may be limited.")
    logger.warning("Install tesseract-ocr or set TESSERACT_CMD environment variable.")
    return None


def get_poppler_path() -> Optional[str]:
    """
    Poppler 경로를 가져옵니다 (캐시됨).
    """
    if not hasattr(get_poppler_path, '_cached_path'):
        get_poppler_path._cached_path = find_poppler_path()
    return get_poppler_path._cached_path


def get_tesseract_cmd() -> Optional[str]:
    """
    Tesseract 경로를 가져옵니다 (캐시됨).
    """
    if not hasattr(get_tesseract_cmd, '_cached_cmd'):
        get_tesseract_cmd._cached_cmd = find_tesseract_cmd()
    return get_tesseract_cmd._cached_cmd


def check_pdf_tools() -> dict:
    """
    PDF 처리 도구 사용 가능 여부를 확인합니다.

    Returns:
        {
            'poppler': {'available': bool, 'path': str},
            'tesseract': {'available': bool, 'path': str}
        }
    """
    poppler_path = get_poppler_path()
    tesseract_cmd = get_tesseract_cmd()

    return {
        'poppler': {
            'available': poppler_path is not None,
            'path': poppler_path
        },
        'tesseract': {
            'available': tesseract_cmd is not None,
            'path': tesseract_cmd
        }
    }
