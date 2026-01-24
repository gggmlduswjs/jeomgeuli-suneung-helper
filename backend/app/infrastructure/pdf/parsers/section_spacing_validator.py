"""
섹션 간 간격 검증기
템플릿의 section_spacing을 활용하여 섹션 경계 판별
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SectionSpacingValidator:
    """섹션 간 간격 검증기"""
    
    def __init__(self, section_spacing: Optional[Dict[str, Any]] = None):
        """
        Args:
            section_spacing: 섹션 간격 정보 딕셔너리
                {
                    "concept_to_passage": 20,  // 픽셀 단위
                    "passage_to_problem": 30,
                    "problem_to_problem": 15,
                    "min_section_height": 50,  // 최소 섹션 높이
                    "max_section_height": 2000  // 최대 섹션 높이
                }
        """
        self.section_spacing = section_spacing or {}
        self.enabled = bool(self.section_spacing)
        
        # 간격 정보 추출
        self.concept_to_passage = self.section_spacing.get('concept_to_passage', 20)
        self.passage_to_problem = self.section_spacing.get('passage_to_problem', 30)
        self.problem_to_problem = self.section_spacing.get('problem_to_problem', 15)
        self.min_section_height = self.section_spacing.get('min_section_height', 50)
        self.max_section_height = self.section_spacing.get('max_section_height', 2000)
        
        if self.enabled:
            logger.info(
                f"[SectionSpacingValidator] 활성화: "
                f"concept->passage={self.concept_to_passage}px, "
                f"passage->problem={self.passage_to_problem}px, "
                f"problem->problem={self.problem_to_problem}px"
            )
    
    def get_expected_spacing(
        self,
        section1_type: str,
        section2_type: str
    ) -> float:
        """두 섹션 타입 간 예상 간격 반환
        
        Args:
            section1_type: 첫 번째 섹션 타입
            section2_type: 두 번째 섹션 타입
            
        Returns:
            예상 간격 (픽셀)
        """
        if not self.enabled:
            return 10.0  # 기본값
        
        # concept -> passage
        if section1_type == 'concept' and section2_type == 'passage':
            return self.concept_to_passage
        
        # passage -> problem
        if section1_type == 'passage' and section2_type == 'problem':
            return self.passage_to_problem
        
        # problem -> problem
        if section1_type == 'problem' and section2_type == 'problem':
            return self.problem_to_problem
        
        # 기본 간격
        return 15.0
    
    def validate_spacing(
        self,
        section1: Dict[str, Any],
        section2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """두 섹션 간 간격 검증
        
        Args:
            section1: 첫 번째 섹션
            section2: 두 번째 섹션
            
        Returns:
            {
                'valid': 검증 통과 여부,
                'actual_spacing': 실제 간격,
                'expected_spacing': 예상 간격,
                'confidence': 신뢰도
            }
        """
        if not self.enabled:
            return {
                'valid': True,
                'actual_spacing': 0,
                'expected_spacing': 0,
                'confidence': 0.5
            }
        
        bbox1 = section1.get('bbox', [])
        bbox2 = section2.get('bbox', [])
        
        if len(bbox1) < 4 or len(bbox2) < 4:
            return {
                'valid': True,
                'actual_spacing': 0,
                'expected_spacing': 0,
                'confidence': 0.0
            }
        
        # section1의 하단과 section2의 상단 간격
        y1_bottom = bbox1[3]
        y2_top = bbox2[1]
        actual_spacing = y2_top - y1_bottom
        
        section1_type = section1.get('type', 'unknown')
        section2_type = section2.get('type', 'unknown')
        expected_spacing = self.get_expected_spacing(section1_type, section2_type)
        
        # 간격이 예상 범위 내에 있으면 통과 (여유 있게 ±50%)
        min_spacing = expected_spacing * 0.5
        max_spacing = expected_spacing * 2.0
        
        valid = min_spacing <= actual_spacing <= max_spacing
        
        # 신뢰도 계산
        if valid:
            # 예상 간격에 가까울수록 높은 신뢰도
            diff = abs(actual_spacing - expected_spacing)
            confidence = max(0.5, 1.0 - (diff / expected_spacing))
        else:
            confidence = 0.3
        
        return {
            'valid': valid,
            'actual_spacing': actual_spacing,
            'expected_spacing': expected_spacing,
            'confidence': confidence
        }
    
    def validate_section_height(
        self,
        section: Dict[str, Any]
    ) -> Dict[str, Any]:
        """섹션 높이 검증
        
        Args:
            section: 섹션 정보
            
        Returns:
            {
                'valid': 검증 통과 여부,
                'height': 섹션 높이,
                'confidence': 신뢰도
            }
        """
        if not self.enabled:
            return {
                'valid': True,
                'height': 0,
                'confidence': 0.5
            }
        
        bbox = section.get('bbox', [])
        if len(bbox) < 4:
            return {
                'valid': True,
                'height': 0,
                'confidence': 0.0
            }
        
        height = bbox[3] - bbox[1]
        valid = self.min_section_height <= height <= self.max_section_height
        
        # 신뢰도 계산
        if valid:
            # 적절한 범위 내에 있으면 높은 신뢰도
            if self.min_section_height <= height <= self.max_section_height:
                confidence = 1.0
            else:
                confidence = 0.7
        else:
            confidence = 0.3
        
        return {
            'valid': valid,
            'height': height,
            'confidence': confidence
        }
    
    def find_section_boundaries(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """섹션 경계 찾기 (간격 기반)
        
        Args:
            sections: 섹션 리스트
            
        Returns:
            경계가 검증된 섹션 리스트
        """
        if not self.enabled or len(sections) < 2:
            return sections
        
        validated_sections = []
        
        for i, section in enumerate(sections):
            validated_section = {**section}
            
            # 높이 검증
            height_validation = self.validate_section_height(section)
            validated_section['height_valid'] = height_validation['valid']
            validated_section['height_confidence'] = height_validation['confidence']
            
            # 이전 섹션과의 간격 검증
            if i > 0:
                prev_section = sections[i - 1]
                spacing_validation = self.validate_spacing(prev_section, section)
                validated_section['spacing_valid'] = spacing_validation['valid']
                validated_section['spacing_confidence'] = spacing_validation['confidence']
                validated_section['actual_spacing'] = spacing_validation['actual_spacing']
                validated_section['expected_spacing'] = spacing_validation['expected_spacing']
            
            validated_sections.append(validated_section)
        
        return validated_sections
