"""
PDF 추출기 기본 클래스
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional


class BaseExtractor(ABC):
    """
    PDF 추출기 기본 인터페이스
    
    추출 단계에서는 구조 해석을 하지 않고,
    좌표 기반 원본 블록만 추출합니다.
    """
    
    @abstractmethod
    def extract_blocks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        PDF에서 텍스트/이미지 블록 추출
        
        Returns:
            List[Dict]: 각 블록의 정보
                - type: "text" | "image" | "table"
                - content: 내용 (텍스트 또는 이미지 경로)
                - bbox: [x0, y0, x1, y1] 좌표
                - page: 페이지 번호 (1-based)
                - metadata: 추가 메타데이터
        """
        pass
    
    @abstractmethod
    def extract_text(self, pdf_path: Path) -> str:
        """
        PDF에서 순수 텍스트만 추출 (레거시 호환)
        
        Returns:
            str: 추출된 텍스트
        """
        pass
    
    def to_json(self, blocks: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        추출 결과를 JSON 형식으로 변환
        
        Args:
            blocks: 추출된 블록 리스트
            output_path: 저장 경로 (선택적)
        
        Returns:
            Dict: JSON 구조
        """
        result = {
            "version": "1.0",
            "extractor": self.__class__.__name__,
            "pages": {},
            "blocks": blocks,
        }
        
        # 페이지별로 그룹화
        for block in blocks:
            page_num = block.get("page", 1)
            if page_num not in result["pages"]:
                result["pages"][str(page_num)] = []
            result["pages"][str(page_num)].append(block)
        
        if output_path:
            import json
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
