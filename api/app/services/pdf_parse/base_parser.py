"""
파서 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class BaseParser(ABC):
    """
    과목별 PDF 파서 기본 인터페이스
    
    추출된 블록을 받아 과목별 구조로 해석합니다.
    """
    
    @abstractmethod
    def parse(self, blocks: List[Dict[str, Any]], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        블록 리스트를 과목별 구조로 파싱
        
        Args:
            blocks: 추출된 블록 리스트
            metadata: 추가 메타데이터 (book_id, title 등)
        
        Returns:
            Dict: 구조화된 콘텐츠
                - pages: 페이지별 구조
                - units: 학습 단위 리스트
                - metadata: 메타데이터
        """
        pass
    
    @abstractmethod
    def detect_content_type(self, block: Dict[str, Any]) -> str:
        """
        블록의 콘텐츠 타입 감지
        
        Returns:
            str: "concept" | "question" | "passage" | "formula" | "choice" | "other"
        """
        pass
    
    def save_result(self, result: Dict[str, Any], output_path: Path) -> Path:
        """
        파싱 결과를 JSON으로 저장
        
        Args:
            result: 파싱 결과
            output_path: 저장 경로
        
        Returns:
            Path: 저장된 파일 경로
        """
        import json
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return output_path
