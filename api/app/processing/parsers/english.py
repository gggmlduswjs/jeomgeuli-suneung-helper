"""
영어 파서 (래핑 버전)
기존 EnglishParsingStrategy를 래핑하여 사용
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from .base import BaseParser

logger = logging.getLogger(__name__)


class EnglishParser(BaseParser):
    """영어 과목 파서 (기존 전략 래핑)"""

    def __init__(self, config_path: Path = None):
        """
        Args:
            config_path: config.json 경로
        """
        self.config_path = config_path
        self.config = self._load_config() if config_path else {}

    def _load_config(self) -> Dict[str, Any]:
        """config.json 로드"""
        if not self.config_path or not self.config_path.exists():
            logger.warning(f"config.json을 찾을 수 없음: {self.config_path}")
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"config.json 로드 실패: {e}")
            return {}

    def parse(self, ocr_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """OCR 데이터 파싱"""
        from app.parsing.strategies.english_strategy import EnglishParsingStrategy

        strategy = EnglishParsingStrategy()
        lectures = strategy.extract_lectures(ocr_data, self.config)
        problems = strategy.extract_problems(ocr_data, self.config)

        logger.info(f"영어 파싱 완료: {len(lectures)}개 강의, {len(problems)}개 문제")

        return {
            'lectures': lectures,
            'problems': problems,
            'metadata': {
                'total_lectures': len(lectures),
                'total_problems': len(problems),
                'status': 'wrapped'
            }
        }
