"""
파서 설정 관리자
중앙화된 설정 로드 및 관리
"""
import json
import logging
from pathlib import Path
from typing import Optional

from app.infrastructure.pdf.types import JSONDict

logger = logging.getLogger(__name__)


class ParserConfigManager:
    """파서 설정 중앙 관리자"""
    
    # 기본 설정 (과목별)
    DEFAULT_CONFIGS = {
        'literature': {
            "lecture_title_patterns": [
                r'^\d+강\s+[가-힣]+',
                r'^\d+\s+[가-힣]+',
            ],
            "toc_lecture_patterns": [
                r'^\d+강\s*\|\s*[가-힣]',
                r'^\d+강\s*\|',
                r'^\d+\s*강\s*\|',
            ],
            "concept_title_patterns": [
                r'^\d+\s*[\.]\s+[가-힣]{2,}',
                r'^\d+\s+[가-힣]{2,}',
            ],
            "content_header_patterns": [
                r'작품으로\s*이해하기',
                r'작품\s*이해',
            ],
            "problem_number_pattern": r'^\d{2}$',
            "start_content_page": 8,
            "toc_end_page": 7,
            "paragraph_y_threshold": 25,
            # 커리큘럼 구조 (과목별 기본값)
            "is_lecture_based": True,
            "lecture_units": ["concept", "passage", "problem"],
            "unit_order": ["concept", "passage", "problem"]
        },
        'math1': {
            "lecture_title_patterns": [
                r'^\d+단원',
                r'^\d+\s*단원',
                r'Unit\s*\d+',
            ],
            "problem_number_pattern": r'^\d+\.',
            "start_content_page": 1,
            "paragraph_y_threshold": 20,
            # 커리큘럼 구조 (과목별 기본값)
            "is_lecture_based": True,
            "lecture_units": ["concept", "example", "exercise", "problem"],  # 수학은 예제/유제 포함
            "unit_order": ["concept", "example", "exercise", "problem"]
        },
        'english': {
            "lecture_title_patterns": [
                r'Unit\s*\d+',
                r'^\d+단원',
                r'^\d+\s*Unit',
            ],
            "problem_number_pattern": r'^\d+\.',
            "start_content_page": 1,
            "paragraph_y_threshold": 20,
            # 커리큘럼 구조 (과목별 기본값)
            "is_lecture_based": True,
            "lecture_units": ["concept", "passage", "problem"],
            "unit_order": ["concept", "passage", "problem"]
        }
    }
    
    @classmethod
    def load_config(
        cls,
        subject: str,
        config_path: Optional[Path] = None
    ) -> JSONDict:
        """
        설정 로드 (파일이 있으면 파일 우선, 없으면 기본값 사용)
        
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
            config_path: config.json 경로 (None이면 기본 경로 시도)
            
        Returns:
            설정 딕셔너리
        """
        # 1. 파일에서 로드 시도
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    logger.info(f"설정 파일 로드 완료: {config_path}")
                    # 기본 설정과 병합
                    default_config = cls.DEFAULT_CONFIGS.get(subject, {})
                    merged_config = {**default_config, **file_config}
                    return merged_config
            except Exception as e:
                logger.warning(f"설정 파일 로드 실패: {e}, 기본 설정 사용")
        
        # 2. 기본 경로에서 시도
        if not config_path:
            # 기본 경로: backend/data/{subject}/config.json
            from app.core.config import settings
            default_config_path = settings.API_DIR / "data" / subject / "config.json"
            if default_config_path.exists():
                try:
                    with open(default_config_path, 'r', encoding='utf-8') as f:
                        file_config = json.load(f)
                        logger.info(f"기본 경로에서 설정 로드: {default_config_path}")
                        default_config = cls.DEFAULT_CONFIGS.get(subject, {})
                        merged_config = {**default_config, **file_config}
                        return merged_config
                except Exception as e:
                    logger.warning(f"기본 경로 설정 로드 실패: {e}, 기본 설정 사용")
        
        # 3. 기본 설정 반환
        default_config = cls.DEFAULT_CONFIGS.get(subject, {})
        if default_config:
            logger.info(f"기본 설정 사용: {subject}")
            return default_config.copy()
        else:
            logger.warning(f"과목 '{subject}'에 대한 기본 설정이 없습니다. 빈 설정 반환")
            return {}
    
    @classmethod
    def get_default_config(cls, subject: str) -> Dict[str, Any]:
        """
        기본 설정만 반환 (파일 로드 없이)
        
        Args:
            subject: 과목명
            
        Returns:
            기본 설정 딕셔너리
        """
        return cls.DEFAULT_CONFIGS.get(subject, {}).copy()
