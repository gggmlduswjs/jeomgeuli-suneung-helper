"""
강의 대본 자동 제작 시스템
한글 파일 → 구조화된 텍스트 → 매뉴얼 준수 검증 → 최종 자료
"""
import re
from pathlib import Path
from typing import List, Dict, Optional
from app.services.hwp_extract import extract_text_from_hwp, extract_structure_from_hwp
from app.services.braille_convert import text_to_braille


class ContentAutoGenerator:
    def __init__(self):
        self.manual_rules = {
            "text_length": {
                "min": 50,
                "max": 200
            },
            "symbol_rules": {
                "problem_choices": "①②③④⑤",  # 문제 선지용
                "explanation": "→",  # 설명용 (원숫자 사용 금지)
                "key_point": "★",
                "section_break": "---"
            },
            "info_order": ["type", "time"],  # 유형 정보 먼저, 시간 정보 나중
        }
    
    def generate_structured_content(self, hwp_path: Path) -> Dict:
        """한글 파일에서 구조화된 학습 자료 자동 생성"""
        # 1. 텍스트 추출
        text = extract_text_from_hwp(hwp_path)
        if not text:
            return {
                "sections": [],
                "validation": {"is_compliant": False, "issues": ["텍스트 추출 실패"], "score": 0},
                "needs_review": True
            }
        
        structure = extract_structure_from_hwp(hwp_path)
        
        # 2. 말하는 단위로 자동 분할
        speech_units = self.split_by_speech_unit(text)
        
        # 3. 섹션별 처리
        sections = []
        for unit in speech_units:
            section = {
                "type": self.detect_section_type(unit),  # concept, key_point, problem
                "content": unit,
                "braille": text_to_braille(unit),
                "timestamp": self.extract_timestamp(unit),  # 있으면 추출
                "symbol": self.assign_symbol(unit)  # 매뉴얼 규칙에 맞는 기호
            }
            sections.append(section)
        
        # 4. 매뉴얼 규칙 검증
        validation_result = self.validate_manual_compliance(sections)
        
        return {
            "sections": sections,
            "validation": validation_result,
            "needs_review": not validation_result["is_compliant"]
        }
    
    def split_by_speech_unit(self, text: str) -> List[str]:
        """말하는 단위로 텍스트 분할
        - 문장 단위
        - 강사가 설명하는 구간 단위
        - 자연스러운 끊김 지점
        """
        # 문장 단위 분할
        sentences = re.split(r'[.!?]\s+', text)
        
        # 너무 짧은 문장은 합치기
        units = []
        current_unit = ""
        for sentence in sentences:
            if len(current_unit) + len(sentence) < self.manual_rules["text_length"]["max"]:
                current_unit += sentence + ". "
            else:
                if current_unit:
                    units.append(current_unit.strip())
                current_unit = sentence + ". "
        if current_unit:
            units.append(current_unit.strip())
        
        return units
    
    def detect_section_type(self, text: str) -> str:
        """섹션 타입 감지"""
        text_lower = text.lower()
        
        if re.search(r'개념|설명', text):
            return "concept"
        elif re.search(r'핵심|포인트', text):
            return "key_point"
        elif re.search(r'문제\s*\d+', text):
            return "problem"
        elif re.search(r'기출|탈탈', text):
            return "practice"
        elif re.search(r'요약|담판', text):
            return "summary"
        else:
            return "general"
    
    def extract_timestamp(self, text: str) -> Optional[str]:
        """시간 정보 추출 (예: "8분 14초")"""
        timestamp_pattern = r'(\d+)\s*분\s*(\d+)\s*초'
        match = re.search(timestamp_pattern, text)
        if match:
            return f"{match.group(1)}분 {match.group(2)}초"
        return None
    
    def assign_symbol(self, text: str) -> str:
        """적절한 기호 할당"""
        section_type = self.detect_section_type(text)
        
        if section_type == "key_point":
            return self.manual_rules["symbol_rules"]["key_point"]
        elif section_type == "problem":
            return "【문제】"
        elif section_type == "explanation":
            return self.manual_rules["symbol_rules"]["explanation"]
        else:
            return ""
    
    def validate_manual_compliance(self, sections: List[Dict]) -> Dict:
        """매뉴얼 규칙 준수 여부 검증"""
        issues = []
        
        for i, section in enumerate(sections):
            # 1. 텍스트 길이 검증 (말하는 단위로 적절히 끊겼는지)
            content_len = len(section["content"])
            if content_len > self.manual_rules["text_length"]["max"]:
                issues.append({
                    "section": i,
                    "type": "text_too_long",
                    "message": f"섹션 {i}: 텍스트가 너무 깁니다 ({content_len}자)"
                })
            elif content_len < self.manual_rules["text_length"]["min"]:
                issues.append({
                    "section": i,
                    "type": "text_too_short",
                    "message": f"섹션 {i}: 텍스트가 너무 짧습니다 ({content_len}자)"
                })
            
            # 2. 기호 사용 규칙 검증
            if section["type"] == "explanation" and re.search(r'[①②③④⑤]', section["content"]):
                issues.append({
                    "section": i,
                    "type": "symbol_conflict",
                    "message": "설명 섹션에 원숫자 사용 (문제 선지와 혼동 가능)"
                })
            
            # 3. 정보 순서 검증
            if section.get("timestamp") and section.get("type"):
                # 시간 정보가 유형 정보보다 앞에 있으면 경고
                # TODO: 실제 텍스트에서 위치 확인
                pass
        
        return {
            "is_compliant": len(issues) == 0,
            "issues": issues,
            "score": max(0, 100 - len(issues) * 10)  # 품질 점수
        }
