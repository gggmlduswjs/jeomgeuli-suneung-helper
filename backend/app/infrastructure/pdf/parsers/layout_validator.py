"""
레이아웃 정보 기반 검증기
템플릿의 layout_info를 활용하여 섹션 경계 판별 및 필터링
"""
import logging
from typing import List, Optional

from app.infrastructure.pdf.types import SectionData, JSONDict

logger = logging.getLogger(__name__)


class LayoutBasedValidator:
    """레이아웃 정보 기반 검증"""
    
    def __init__(self, layout_info: Optional[JSONDict] = None, page_height: float = 1000.0):
        """
        Args:
            layout_info: 레이아웃 정보 딕셔너리
                {
                    "header_height": 50,
                    "footer_height": 30,
                    "margin": {"top": 20, "bottom": 20, "left": 30, "right": 30},
                    "column_count": 2,
                    "content_area": {"x_min": 30, "x_max": 570, "y_min": 50, "y_max": 800}
                }
            page_height: 페이지 높이 (픽셀, 기본값 1000)
        """
        self.layout_info = layout_info or {}
        self.page_height = page_height
        self.enabled = bool(self.layout_info)
        
        # 레이아웃 정보 추출
        self.header_height = self.layout_info.get('header_height', 0)
        self.footer_height = self.layout_info.get('footer_height', 0)
        self.margin = self.layout_info.get('margin', {})
        self.content_area = self.layout_info.get('content_area', {})
        self.column_count = self.layout_info.get('column_count', 1)
        
        if self.enabled:
            logger.info(
                f"[LayoutValidator] 활성화: "
                f"헤더={self.header_height}px, 푸터={self.footer_height}px, "
                f"컬럼={self.column_count}개"
            )
    
    def is_in_content_area(
        self,
        bbox: List[float]
    ) -> bool:
        """bbox가 콘텐츠 영역 내에 있는지 확인
        
        Args:
            bbox: [x_min, y_min, x_max, y_max] 형식의 바운딩 박스
            
        Returns:
            콘텐츠 영역 내에 있으면 True
        """
        if not self.enabled or not self.content_area or len(bbox) < 4:
            return True  # 검증 불가능하면 통과
        
        x_min, y_min, x_max, y_max = bbox[0], bbox[1], bbox[2], bbox[3]
        
        content_x_min = self.content_area.get('x_min', 0)
        content_x_max = self.content_area.get('x_max', 1000)
        content_y_min = self.content_area.get('y_min', 0)
        content_y_max = self.content_area.get('y_max', self.page_height)
        
        in_x_range = content_x_min <= x_min <= content_x_max and content_x_min <= x_max <= content_x_max
        in_y_range = content_y_min <= y_min <= content_y_max and content_y_min <= y_max <= content_y_max
        
        return in_x_range and in_y_range
    
    def is_in_header_footer(
        self,
        bbox: List[float]
    ) -> bool:
        """bbox가 헤더/푸터 영역에 있는지 확인
        
        Args:
            bbox: [x_min, y_min, x_max, y_max] 형식의 바운딩 박스
            
        Returns:
            헤더/푸터 영역에 있으면 True
        """
        if not self.enabled or len(bbox) < 4:
            return False
        
        y_min = bbox[1]
        y_max = bbox[3] if len(bbox) > 3 else y_min
        
        # 헤더 영역
        if y_max < self.header_height:
            return True
        
        # 푸터 영역
        if y_min > (self.page_height - self.footer_height):
            return True
        
        return False
    
    def filter_header_footer(
        self,
        sections: List[SectionData]
    ) -> List[SectionData]:
        """헤더/푸터 영역 섹션 필터링

        Args:
            sections: 섹션 리스트

        Returns:
            필터링된 섹션 리스트
        """
        if not self.enabled:
            return sections
        
        filtered = []
        removed_count = 0
        
        for section in sections:
            bbox = section.get('bbox', [])
            
            if self.is_in_header_footer(bbox):
                removed_count += 1
                logger.debug(
                    f"[LayoutValidator] 헤더/푸터 영역 섹션 제외: "
                    f"'{section.get('title', 'N/A')[:30]}...' (y: {bbox[1] if len(bbox) > 1 else 'N/A'})"
                )
                continue
            
            if not self.is_in_content_area(bbox):
                removed_count += 1
                logger.debug(
                    f"[LayoutValidator] 콘텐츠 영역 밖 섹션 제외: "
                    f"'{section.get('title', 'N/A')[:30]}...'"
                )
                continue
            
            filtered.append(section)
        
        if removed_count > 0:
            logger.info(f"[LayoutValidator] {removed_count}개 섹션 필터링 완료")
        
        return filtered
    
    def get_content_area_bbox(self) -> Optional[List[float]]:
        """콘텐츠 영역의 bbox 반환
        
        Returns:
            [x_min, y_min, x_max, y_max] 또는 None
        """
        if not self.content_area:
            return None
        
        return [
            self.content_area.get('x_min', 0),
            self.content_area.get('y_min', 0),
            self.content_area.get('x_max', 1000),
            self.content_area.get('y_max', self.page_height)
        ]
    
    def validate_section_spacing(
        self,
        section1: SectionData,
        section2: SectionData,
        min_spacing: float = 10.0
    ) -> bool:
        """두 섹션 간 간격 검증

        Args:
            section1: 첫 번째 섹션
            section2: 두 번째 섹션
            min_spacing: 최소 간격 (픽셀)

        Returns:
            간격이 충분하면 True
        """
        bbox1 = section1.get('bbox', [])
        bbox2 = section2.get('bbox', [])
        
        if len(bbox1) < 4 or len(bbox2) < 4:
            return True  # 검증 불가능하면 통과
        
        # section1의 하단과 section2의 상단 간격
        y1_bottom = bbox1[3]
        y2_top = bbox2[1]
        
        spacing = y2_top - y1_bottom
        
        return spacing >= min_spacing
