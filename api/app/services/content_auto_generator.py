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
        """매뉴얼 규칙 준수 여부 검증 및 자동 수정"""
        issues = []
        fixed_sections = []
        
        for i, section in enumerate(sections):
            fixed_section = section.copy()
            
            # 1. 텍스트 길이 검증 및 자동 조절
            content = fixed_section["content"]
            content_len = len(content)
            
            if content_len > self.manual_rules["text_length"]["max"]:
                # 텍스트가 너무 길면 자동으로 분할
                fixed_content = self._auto_adjust_text_length(content)
                fixed_section["content"] = fixed_content
                issues.append({
                    "section": i,
                    "type": "text_too_long",
                    "message": f"섹션 {i}: 텍스트가 너무 깁니다 ({content_len}자) - 자동 분할됨",
                    "fixed": True
                })
            elif content_len < self.manual_rules["text_length"]["min"]:
                issues.append({
                    "section": i,
                    "type": "text_too_short",
                    "message": f"섹션 {i}: 텍스트가 너무 짧습니다 ({content_len}자)",
                    "fixed": False
                })
            
            # 2. 기호 사용 규칙 검증 및 자동 수정
            fixed_content = self._fix_symbol_usage(fixed_section["content"], fixed_section["type"])
            if fixed_content != fixed_section["content"]:
                issues.append({
                    "section": i,
                    "type": "symbol_conflict",
                    "message": "설명 섹션에 원숫자 사용 - 자동 수정됨",
                    "fixed": True
                })
                fixed_section["content"] = fixed_content
            
            # 3. 정보 순서 자동 최적화
            fixed_content = self._optimize_info_order(fixed_section["content"], fixed_section.get("type"), fixed_section.get("timestamp"))
            if fixed_content != fixed_section["content"]:
                fixed_section["content"] = fixed_content
                issues.append({
                    "section": i,
                    "type": "info_order",
                    "message": "정보 순서 최적화됨",
                    "fixed": True
                })
            
            fixed_sections.append(fixed_section)
        
        # 수정된 섹션으로 업데이트
        sections[:] = fixed_sections
        
        return {
            "is_compliant": len([i for i in issues if not i.get("fixed", False)]) == 0,
            "issues": issues,
            "score": max(0, 100 - len([i for i in issues if not i.get("fixed", False)]) * 10),  # 수정되지 않은 이슈만 점수 감점
            "improvements": [i for i in issues if i.get("fixed", False)]  # 개선 사항
        }
    
    def _auto_adjust_text_length(self, text: str) -> str:
        """텍스트 길이 자동 조절 (말하는 단위로 분할)"""
        max_len = self.manual_rules["text_length"]["max"]
        
        if len(text) <= max_len:
            return text
        
        # 문장 단위로 분할
        sentences = re.split(r'([.!?]\s+)', text)
        
        # 문장을 합치면서 최대 길이를 넘지 않도록
        units = []
        current_unit = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            
            if len(current_unit) + len(sentence) <= max_len:
                current_unit += sentence
            else:
                if current_unit:
                    units.append(current_unit.strip())
                current_unit = sentence
        
        if current_unit:
            units.append(current_unit.strip())
        
        # 첫 번째 단위만 반환 (나머지는 별도 섹션으로 처리)
        return units[0] if units else text[:max_len]
    
    def _fix_symbol_usage(self, content: str, section_type: str) -> str:
        """기호 사용 규칙 자동 수정"""
        fixed_content = content
        
        # 설명 섹션에서 원숫자 사용 금지
        if section_type == "explanation" or section_type == "concept":
            # 원숫자를 화살표로 변경
            fixed_content = re.sub(r'([①②③④⑤])', self.manual_rules["symbol_rules"]["explanation"], fixed_content)
        
        return fixed_content
    
    def _optimize_info_order(self, content: str, section_type: Optional[str], timestamp: Optional[str]) -> str:
        """정보 순서 자동 최적화 (유형 정보 먼저, 시간 정보 나중)"""
        if not timestamp:
            return content
        
        # 시간 정보 패턴 찾기
        timestamp_pattern = r'(\d+)\s*분\s*(\d+)\s*초'
        timestamp_match = re.search(timestamp_pattern, content)
        
        if not timestamp_match:
            return content
        
        # 유형 정보 패턴 찾기 (해설, 개념, 문제 등)
        type_patterns = [
            r'(해설|개념|예제|문제|정리)',
            r'(【[^】]+】)',
        ]
        
        type_match = None
        for pattern in type_patterns:
            type_match = re.search(pattern, content)
            if type_match:
                break
        
        # 시간 정보가 유형 정보보다 앞에 있으면 순서 변경
        if type_match and timestamp_match.start() < type_match.start():
            # 시간 정보 제거
            content_without_time = re.sub(timestamp_pattern, '', content, count=1).strip()
            
            # 유형 정보 뒤에 시간 정보 추가
            type_end = type_match.end()
            optimized = (
                content_without_time[:type_end] + 
                f" ({timestamp})" + 
                content_without_time[type_end:]
            )
            return optimized.strip()
        
        return content
    
    def generate_with_auto_fix(self, hwp_path: Path) -> Dict:
        """자동 수정을 포함한 구조화된 콘텐츠 생성"""
        result = self.generate_structured_content(hwp_path)
        
        # 검증 및 자동 수정
        validation = self.validate_manual_compliance(result["sections"])
        result["validation"] = validation
        
        # 개선 제안 생성
        result["suggestions"] = self._generate_improvement_suggestions(result["sections"], validation)
        
        return result
    
    def _generate_improvement_suggestions(self, sections: List[Dict], validation: Dict) -> List[Dict]:
        """개선 제안 자동 생성"""
        suggestions = []
        
        for issue in validation.get("issues", []):
            if not issue.get("fixed", False):
                suggestion = {
                    "section": issue.get("section"),
                    "type": issue.get("type"),
                    "message": issue.get("message"),
                    "suggestion": self._get_suggestion_for_issue(issue)
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _get_suggestion_for_issue(self, issue: Dict) -> str:
        """이슈 타입별 개선 제안"""
        issue_type = issue.get("type")
        
        suggestions_map = {
            "text_too_long": "텍스트를 말하는 단위로 더 작게 나누세요.",
            "text_too_short": "인접한 섹션과 합치거나 내용을 보강하세요.",
            "symbol_conflict": "원숫자 대신 화살표(→)를 사용하세요.",
            "info_order": "유형 정보를 앞에, 시간 정보를 뒤에 배치하세요.",
        }
        
        return suggestions_map.get(issue_type, "수동 검토가 필요합니다.")