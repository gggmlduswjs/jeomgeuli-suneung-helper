"""
OCR 텍스트 전처리기
OCR 결과의 품질을 향상시키고 섹션 추출 정확도를 높임
"""
import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """OCR 텍스트 전처리기
    
    기능:
    - 공백 정규화
    - 특수 문자 정리
    - 폰트 인코딩 문제 해결
    - 텍스트 품질 점수 계산
    """
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """텍스트 정규화
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정규화된 텍스트
        """
        if not text:
            return ""
        
        # 1. CID 문자 제거
        text = re.sub(r'\(cid:\d+\)', '', text)
        
        # 2. 공백 정규화 (여러 공백 → 하나)
        text = re.sub(r'\s+', ' ', text)
        
        # 3. 앞뒤 공백 제거
        text = text.strip()
        
        # 4. 특수 문자 정리
        # 잘못 인식된 문자 교정
        replacements = {
            '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
            '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
            '．': '.', '，': ',', '：': ':', '；': ';',
            '（': '(', '）': ')', '［': '[', '］': ']',
            '【': '[', '】': ']', '「': '"', '」': '"',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    @staticmethod
    def calculate_quality_score(text: str) -> float:
        """텍스트 품질 점수 계산 (0.0-1.0)
        
        Args:
            text: 평가할 텍스트
            
        Returns:
            품질 점수 (높을수록 좋음)
        """
        if not text:
            return 0.0
        
        score = 1.0
        
        # 1. CID 문자 비율 (패널티)
        cid_count = len(re.findall(r'\(cid:\d+\)', text))
        if len(text) > 0:
            cid_ratio = cid_count / len(text)
            score -= cid_ratio * 0.5  # 최대 0.5 감점
        
        # 2. 한글 비율 (보너스)
        korean_chars = len(re.findall(r'[가-힣]', text))
        if len(text) > 0:
            korean_ratio = korean_chars / len(text)
            score += korean_ratio * 0.2  # 최대 0.2 가점
        
        # 3. 특수 문자 비율 (패널티)
        special_chars = len(re.findall(r'[^\w\s가-힣]', text))
        if len(text) > 0:
            special_ratio = special_chars / len(text)
            if special_ratio > 0.3:  # 30% 이상이면 패널티
                score -= (special_ratio - 0.3) * 0.3
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def preprocess_ocr_data(ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """OCR 데이터 전처리
        
        Args:
            ocr_data: 원본 OCR 데이터
            
        Returns:
            전처리된 OCR 데이터
        """
        processed = []
        
        for page_data in ocr_data:
            texts = page_data.get('text', [])
            processed_texts = []
            quality_scores = []
            
            for text in texts:
                normalized = TextPreprocessor.normalize_text(str(text))
                if normalized:
                    processed_texts.append(normalized)
                    quality_scores.append(
                        TextPreprocessor.calculate_quality_score(normalized)
                    )
            
            # 전처리된 데이터 생성
            processed_page = page_data.copy()
            processed_page['text'] = processed_texts
            processed_page['quality_scores'] = quality_scores
            processed_page['avg_quality'] = (
                sum(quality_scores) / len(quality_scores) 
                if quality_scores else 0.0
            )
            
            processed.append(processed_page)
        
        return processed
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 2) -> List[str]:
        """텍스트에서 키워드 추출
        
        Args:
            text: 원본 텍스트
            min_length: 최소 키워드 길이
            
        Returns:
            키워드 리스트
        """
        if not text:
            return []
        
        # 한글 단어 추출
        korean_words = re.findall(r'[가-힣]+', text)
        
        # 최소 길이 필터링
        keywords = [w for w in korean_words if len(w) >= min_length]
        
        return keywords
