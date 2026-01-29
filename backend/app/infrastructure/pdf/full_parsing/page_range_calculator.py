"""
페이지 범위 계산기
템플릿 기반 페이지 범위 계산 로직 분리
"""
import logging
from typing import Optional, Tuple
from pathlib import Path

from app.infrastructure.pdf.parsers.template_manager import TemplateManager
from app.infrastructure.pdf.exceptions import PageRangeError

logger = logging.getLogger(__name__)


class PageRangeCalculator:
    """페이지 범위 계산기
    
    템플릿의 강의 목록을 기반으로 필요한 페이지 범위를 계산
    """
    
    def __init__(self, template_manager: TemplateManager):
        """
        Args:
            template_manager: 템플릿 매니저 인스턴스
        """
        self.template_manager = template_manager
    
    def calculate_from_template(
        self,
        subject: str
    ) -> Optional[Tuple[int, Optional[int]]]:
        """템플릿의 강의 목록에서 필요한 페이지 범위 계산
        
        Args:
            subject: 과목명
            
        Returns:
            (시작 페이지, 종료 페이지) 튜플 또는 None
            (템플릿이 없거나 페이지 정보가 없으면)
            
        Raises:
            PageRangeError: 페이지 범위 계산 중 오류 발생 시
        """
        try:
            # 템플릿 매니저에서 해당 과목의 템플릿 확인
            subject_templates = self.template_manager.get_templates_by_subject(subject)
            if not subject_templates:
                logger.debug(f"[PageRangeCalculator] {subject} 과목의 템플릿 없음")
                return None
            
            # 가장 최신 템플릿 선택
            template = max(
                subject_templates,
                key=lambda t: (
                    t.updated_at if t.updated_at else t.created_at or "",
                    t.confidence
                )
            )
            
            # 템플릿의 강의 목록에서 페이지 범위 계산
            toc_lecture_list = template.config.get('toc_lecture_list', [])
            if not toc_lecture_list:
                logger.debug(f"[PageRangeCalculator] 템플릿 {template.name}에 강의 목록 없음")
                return None
            
            # 페이지 정보가 있는 강의들만 필터링
            lectures_with_pages = [
                l for l in toc_lecture_list 
                if l.get('start_page') is not None and isinstance(l.get('start_page'), int)
            ]
            
            if not lectures_with_pages:
                logger.debug(f"[PageRangeCalculator] 페이지 정보가 있는 강의 없음")
                return None
            
            # 최소 시작 페이지와 최대 종료 페이지 계산
            start_pages = [l['start_page'] for l in lectures_with_pages]
            end_pages = [l.get('end_page') for l in lectures_with_pages if l.get('end_page') is not None]
            
            min_start = min(start_pages)
            max_end = max(end_pages) if end_pages else None
            
            # TOC 페이지도 포함 (일반적으로 1-7페이지)
            toc_end = template.config.get('toc_end_page', 7)
            actual_start = min(1, min_start)  # TOC 시작 페이지
            
            logger.info(
                f"[PageRangeCalculator] 템플릿 기반 페이지 범위 계산: "
                f"{actual_start}~{max_end or '끝'} (강의: {min_start}~{max_end or '끝'}, TOC: 1~{toc_end})"
            )
            
            return (actual_start, max_end)
            
        except Exception as e:
            logger.warning(f"[PageRangeCalculator] 페이지 범위 계산 실패: {e}")
            # 페이지 범위 계산 실패는 치명적이지 않으므로 None 반환 (폴백 사용)
            return None
