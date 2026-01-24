"""
폰트 정보 기반 섹션 분류기
템플릿의 font_info를 활용하여 섹션 타입 판별
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class FontBasedClassifier:
    """폰트 정보 기반 섹션 분류"""
    
    def __init__(self, font_info: Optional[Dict[str, Any]] = None):
        """
        Args:
            font_info: 폰트 정보 딕셔너리
                {
                    "concept_title": {"size": 14.0, "weight": "bold", "family": "NanumGothic"},
                    "passage_title": {"size": 12.0, "weight": "bold", "family": "NanumGothic"},
                    "problem_number": {"size": 11.0, "weight": "normal", "family": "NanumGothic"},
                    "body_text": {"size": 10.0, "weight": "normal", "family": "NanumGothic"}
                }
        """
        self.font_info = font_info or {}
        self.enabled = bool(self.font_info)
        
        if self.enabled:
            logger.info(f"[FontClassifier] 활성화: {list(self.font_info.keys())}")
    
    def classify_by_font(
        self,
        text_block: Dict[str, Any],
        line_text: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """폰트 정보로 섹션 타입 판별
        
        Args:
            text_block: 텍스트 블록 정보 (font_size, font_weight, font_family 포함 가능)
            line_text: 텍스트 내용 (선택)
            
        Returns:
            {
                'type': 섹션 타입 ('concept', 'passage', 'problem', None),
                'confidence': 신뢰도 (0.0-1.0),
                'matched_font': 매칭된 폰트 정보
            } 또는 None
        """
        if not self.enabled:
            return None
        
        # OCR 결과에서 폰트 정보 추출 시도
        # pdfplumber나 OCR 결과에 따라 필드명이 다를 수 있음
        block_font_size = (
            text_block.get('font_size') or
            text_block.get('size') or
            text_block.get('fontSize') or
            0
        )
        
        block_font_weight = (
            text_block.get('font_weight') or
            text_block.get('weight') or
            text_block.get('bold') or
            'normal'
        )
        
        # boolean을 문자열로 변환
        if isinstance(block_font_weight, bool):
            block_font_weight = 'bold' if block_font_weight else 'normal'
        
        block_font_family = (
            text_block.get('font_family') or
            text_block.get('family') or
            text_block.get('fontName') or
            ''
        )
        
        # 폰트 정보가 없으면 분류 불가
        if not block_font_size and not block_font_weight:
            return None
        
        best_match = None
        best_confidence = 0.0
        
        # 각 섹션 타입의 폰트와 비교
        for section_type, font_config in self.font_info.items():
            if not isinstance(font_config, dict):
                continue
            
            template_size = font_config.get('size', 0)
            template_weight = font_config.get('weight', 'normal')
            template_family = font_config.get('family', '')
            
            # 크기 비교 (1.0pt 이내 허용)
            size_match = False
            if template_size > 0 and block_font_size > 0:
                size_diff = abs(block_font_size - template_size)
                size_match = size_diff <= 1.0
            
            # weight 비교
            weight_match = (
                block_font_weight == template_weight or
                (block_font_weight == 'bold' and template_weight == 'bold') or
                (block_font_weight == 'normal' and template_weight == 'normal')
            )
            
            # family 비교 (선택적)
            family_match = True
            if template_family and block_font_family:
                family_match = template_family.lower() in block_font_family.lower() or \
                               block_font_family.lower() in template_family.lower()
            
            # 신뢰도 계산
            confidence = 0.0
            if size_match and weight_match:
                confidence = 0.9
                if family_match:
                    confidence = 1.0
            elif size_match:
                confidence = 0.6
            elif weight_match:
                confidence = 0.5
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = {
                    'type': section_type,
                    'confidence': confidence,
                    'matched_font': {
                        'size': template_size,
                        'weight': template_weight,
                        'family': template_family
                    },
                    'actual_font': {
                        'size': block_font_size,
                        'weight': block_font_weight,
                        'family': block_font_family
                    }
                }
        
        # 임계값 이상이면 반환
        if best_match and best_confidence >= 0.5:
            logger.debug(
                f"[FontClassifier] 매칭: '{line_text[:30] if line_text else 'N/A'}...' -> "
                f"{best_match['type']} (신뢰도: {best_confidence:.2f})"
            )
            return best_match
        
        return None
    
    def classify_line(
        self,
        line: List[Dict[str, Any]],
        line_text: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """줄 단위로 폰트 기반 분류
        
        Args:
            line: 단어 딕셔너리 리스트 (각 단어에 폰트 정보 포함 가능)
            line_text: 결합된 텍스트 (선택)
            
        Returns:
            분류 결과 또는 None
        """
        if not self.enabled or not line:
            return None
        
        # 줄의 첫 번째 단어의 폰트 정보 사용 (또는 가장 큰 폰트)
        best_word = None
        max_size = 0
        
        for word in line:
            word_size = (
                word.get('font_size') or
                word.get('size') or
                word.get('fontSize') or
                0
            )
            if word_size > max_size:
                max_size = word_size
                best_word = word
        
        if best_word:
            return self.classify_by_font(best_word, line_text)
        
        return None
