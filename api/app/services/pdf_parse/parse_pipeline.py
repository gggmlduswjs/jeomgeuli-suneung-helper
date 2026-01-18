"""
PDF 파싱 파이프라인
추출 → 파싱 → 저장 단계 분리
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Book, Subject
from .base_parser import BaseParser
from app.services.pdf_extract.base_extractor import BaseExtractor
from app.services.pdf_extract.pdfplumber_extractor import PDFPlumberExtractor

# 순환 import 방지를 위해 파서는 lazy import 사용


class ParsePipeline:
    """
    PDF 파싱 파이프라인
    
    단계:
    1. Extract: PDF에서 블록 추출 → JSON 저장
    2. Parse: 과목별 파서로 구조화 → JSON 저장
    3. Save: 데이터베이스에 저장 (선택적)
    """
    
    # 과목별 파서 매핑 (lazy import로 변경)
    @staticmethod
    def _get_parser_map():
        """과목별 파서 매핑 (lazy import)"""
        from app.services.subject_strategies.math import MathParser
        from app.services.subject_strategies.korean import KoreanParser
        from app.services.subject_strategies.english import EnglishParser
        
        return {
            "MATH": MathParser,
            "KOREAN": KoreanParser,
            "ENGLISH": EnglishParser,
        }
    
    def __init__(
        self,
        extractor: Optional[BaseExtractor] = None,
        extract_dir: Optional[Path] = None,
        parsed_dir: Optional[Path] = None,
    ):
        """
        Args:
            extractor: PDF 추출기 (기본: PDFPlumberExtractor)
            extract_dir: 추출 결과 저장 디렉토리
            parsed_dir: 파싱 결과 저장 디렉토리
        """
        self.extractor = extractor or PDFPlumberExtractor()
        self.extract_dir = extract_dir or settings.EXTRACTED_DIR
        self.parsed_dir = parsed_dir or settings.PARSED_DIR
    
    def extract(self, pdf_path: Path, book_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Step 1: PDF에서 블록 추출
        
        Args:
            pdf_path: PDF 파일 경로
            book_id: 교재 ID (저장 파일명용)
        
        Returns:
            Dict: 추출된 블록 JSON
        """
        print(f"[Pipeline] Extract 단계 시작: {pdf_path}")
        
        # 블록 추출
        blocks = self.extractor.extract_blocks(pdf_path)
        
        # JSON으로 변환 및 저장
        output_file = book_id or pdf_path.stem
        extract_json_path = self.extract_dir / f"{output_file}_blocks.json"
        
        result = self.extractor.to_json(blocks, extract_json_path)
        
        print(f"[Pipeline] Extract 완료: {len(blocks)}개 블록, {extract_json_path}")
        
        return result
    
    def parse(
        self,
        extract_result: Dict[str, Any],
        subject: str,
        book_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Step 2: 추출 결과를 과목별로 파싱
        
        Args:
            extract_result: extract 단계 결과
            subject: 과목 (MATH, KOREAN, ENGLISH)
            book_id: 교재 ID
            metadata: 추가 메타데이터
        
        Returns:
            Dict: 파싱된 구조 JSON
        """
        print(f"[Pipeline] Parse 단계 시작: subject={subject}")
        
        # 파서 선택 (lazy import 사용)
        parser_map = self._get_parser_map()
        parser_class = parser_map.get(subject.upper())
        if not parser_class:
            raise ValueError(f"지원하지 않는 과목: {subject}")
        
        parser = parser_class()
        
        # 블록 추출
        blocks = extract_result.get("blocks", [])
        
        # 파싱
        parse_metadata = {
            "book_id": book_id,
            **(metadata or {}),
        }
        
        result = parser.parse(blocks, parse_metadata)
        
        # JSON 저장
        output_file = book_id or extract_result.get("extractor", "unknown")
        parsed_json_path = self.parsed_dir / subject.lower() / f"{output_file}_parsed.json"
        
        parser.save_result(result, parsed_json_path)
        
        print(f"[Pipeline] Parse 완료: {result.get('statistics', {})}, {parsed_json_path}")
        
        return result
    
    def run(
        self,
        pdf_path: Path,
        subject: str,
        book_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        save_to_db: bool = False,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        전체 파이프라인 실행
        
        Args:
            pdf_path: PDF 파일 경로
            subject: 과목
            book_id: 교재 ID
            metadata: 추가 메타데이터
            save_to_db: DB 저장 여부
            db: 데이터베이스 세션 (save_to_db=True일 때 필수)
        
        Returns:
            Dict: 파싱 결과
        """
        # Step 1: Extract
        extract_result = self.extract(pdf_path, book_id)
        
        # Step 2: Parse
        parse_result = self.parse(extract_result, subject, book_id, metadata)
        
        # Step 3: Save to DB (선택적)
        if save_to_db and db and book_id:
            self._save_to_db(parse_result, book_id, db)
        
        return {
            "extract": extract_result,
            "parse": parse_result,
            "book_id": book_id,
            "subject": subject,
        }
    
    def _save_to_db(self, parse_result: Dict[str, Any], book_id: str, db: Session):
        """
        파싱 결과를 데이터베이스에 저장 (향후 구현)
        """
        # TODO: Lesson, Unit 모델로 변환하여 저장
        print(f"[Pipeline] DB 저장: {book_id} (구현 예정)")
