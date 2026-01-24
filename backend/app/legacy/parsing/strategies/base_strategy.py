"""
과목별 파싱 전략 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParsingStrategy(ABC):
    """과목별 파싱 전략 기본 클래스"""
    
    @abstractmethod
    def extract_lectures(self, all_ocr_data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        강의 목록 추출
        
        Args:
            all_ocr_data: OCR 데이터 리스트
            config: 과목별 설정
            
        Returns:
            강의 리스트
        """
        pass
    
    @abstractmethod
    def extract_problems(self, all_ocr_data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        문제 목록 추출
        
        Args:
            all_ocr_data: OCR 데이터 리스트
            config: 과목별 설정
            
        Returns:
            문제 리스트
        """
        pass
