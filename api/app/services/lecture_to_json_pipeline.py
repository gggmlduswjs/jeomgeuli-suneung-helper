"""
강의 대본 → 구조화된 JSON 파이프라인

강의 대본을 읽어서 학습 시스템에서 바로 사용 가능한 JSON 형식으로 변환
"""
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.services.lecture_script_parser import LectureScriptParser
from app.services.curriculum_generator import CurriculumGenerator
from app.services.hwp_extract import extract_text_from_hwp


class LectureToJSONPipeline:
    """강의 대본을 구조화된 JSON으로 변환하는 파이프라인"""
    
    # 과목명 매핑
    SUBJECT_MAP = {
        'literature': 'korean',
        'math1': 'math',
        'english': 'english',
        'korean': 'korean',
        'math': 'math',
    }
    
    # Unit type 매핑
    TYPE_MAP = {
        'ot': 'intro',
        'intro': 'intro',
        'overview': 'intro',
        'concept': 'concept',
        'definition': 'definition',
        'textbook_content': 'concept',
        'example': 'example',
        'problem': 'problem_intro',
        'problem_intro': 'problem_intro',
        'summary': 'summary',
        'notation': 'notation',
        'main_content': 'concept',
    }
    
    def __init__(self, subject: str):
        """
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
        """
        self.subject = subject
        self.parser = LectureScriptParser(subject=subject)
        self.generator = CurriculumGenerator(subject=subject)
    
    def process_lecture_file(self, file_path: Path, lesson_number: Optional[int] = None) -> Dict[str, Any]:
        """
        강의 대본 파일을 구조화된 JSON으로 변환
        
        Args:
            file_path: 강의 대본 파일 경로 (.txt, .hwp)
            lesson_number: 강의 번호 (없으면 파일명에서 추출)
            
        Returns:
            구조화된 JSON 데이터
        """
        # 파일 읽기
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                script_text = f.read()
        elif file_path.suffix.lower() in ['.hwp', '.hwpx']:
            script_text = extract_text_from_hwp(file_path)
            if not script_text:
                raise ValueError(f"HWP 파일에서 텍스트를 추출할 수 없습니다: {file_path}")
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {file_path.suffix}")
        
        return self.process_lecture_text(script_text, lesson_number, file_path.name)
    
    def process_lecture_text(self, script_text: str, lesson_number: Optional[int] = None, 
                            filename: Optional[str] = None) -> Dict[str, Any]:
        """
        강의 대본 텍스트를 구조화된 JSON으로 변환
        
        Args:
            script_text: 강의 대본 텍스트
            lesson_number: 강의 번호
            filename: 파일명 (레슨 번호 추출용)
            
        Returns:
            구조화된 JSON 데이터
        """
        # 강의 번호 추출
        if lesson_number is None:
            if filename:
                lesson_number = self._extract_lesson_number_from_filename(filename)
            if lesson_number is None:
                match = re.search(r'(\d+)\s*강', script_text, re.IGNORECASE)
                lesson_number = int(match.group(1)) if match else 1
        
        # 강의 대본 파싱
        parsed = self.parser.parse(script_text)
        
        # 문학 과목의 경우 구조화
        if self.subject == 'literature':
            parsed = self.generator._structure_literature_script(parsed)
        
        # 학습 단위 생성
        break_points = self.generator._identify_break_points(parsed)
        pdf_refs = self.generator._extract_pdf_references(parsed)
        learning_units = self.generator._create_learning_units(parsed, break_points, pdf_refs)
        
        # JSON 구조 생성
        return self._build_json_structure(parsed, learning_units, lesson_number)
    
    def _build_json_structure(self, parsed: Dict, learning_units: List[Dict], 
                            lesson_number: int) -> Dict[str, Any]:
        """파싱된 데이터를 목표 JSON 구조로 변환"""
        subject_code = self.SUBJECT_MAP.get(self.subject, self.subject)
        lesson_id = f"{subject_code}_{lesson_number:02d}"
        
        # 레슨 제목 추출
        title = self._extract_title(parsed, lesson_number)
        
        # 섹션별로 그룹화
        sections = self._group_units_into_sections(learning_units, lesson_id)
        
        return {
            "subject": subject_code,
            "lessonId": lesson_id,
            "title": title,
            "order": lesson_number,
            "sections": sections
        }
    
    def _extract_title(self, parsed: Dict, lesson_number: int) -> str:
        """레슨 제목 추출"""
        sections = parsed.get('sections', [])
        
        # 첫 번째 섹션에서 제목 추출 시도
        if sections:
            first_section = sections[0]
            content = first_section.get('content', '')
            
            # "수능특강 문학 1강" 같은 패턴
            title_match = re.search(r'수능특강\s*([가-힣]+)\s*\d+강', content)
            if title_match:
                return f"{lesson_number}강 {title_match.group(1)}"
            
            # "1강" 다음의 제목 추출
            title_match = re.search(r'\d+강\s*([가-힣\s]+)', content)
            if title_match:
                return title_match.group(1).strip()
        
        # 기본값
        return f"{lesson_number}강"
    
    def _group_units_into_sections(self, learning_units: List[Dict], lesson_id: str) -> List[Dict]:
        """학습 단위를 섹션별로 그룹화"""
        sections = []
        current_section = None
        current_section_units = []
        section_index = 0
        
        for unit in learning_units:
            section_type = unit.get('section_type', 'general')
            section_name = unit.get('section_name', section_type)
            
            # 섹션 변경 감지
            if current_section != section_type:
                # 이전 섹션 저장
                if current_section is not None:
                    sections.append({
                        "sectionId": f"{lesson_id}_{section_index:02d}",
                        "title": self._get_section_title(current_section, current_section_units),
                        "units": current_section_units
                    })
                    section_index += 1
                
                # 새 섹션 시작
                current_section = section_type
                current_section_units = []
            
            # Unit 생성
            unit_index = len(current_section_units)
            unit_id = f"{lesson_id}_{section_index:02d}_u{unit_index + 1}"
            
            # 내용 정제 (강사 멘트 제거, 교재용 서술문으로 변환)
            content = self._refine_content(unit.get('content', ''))
            
            current_section_units.append({
                "unitId": unit_id,
                "type": self.TYPE_MAP.get(section_type, 'concept'),
                "content": content
            })
        
        # 마지막 섹션 저장
        if current_section is not None:
            sections.append({
                "sectionId": f"{lesson_id}_{section_index:02d}",
                "title": self._get_section_title(current_section, current_section_units),
                "units": current_section_units
            })
        
        return sections
    
    def _get_section_title(self, section_type: str, units: List[Dict]) -> str:
        """섹션 제목 생성"""
        # 섹션 타입에 따른 기본 제목
        title_map = {
            'intro': '인트로',
            'ot': '오리엔테이션',
            'main_content': '본문',
            'concept': '개념',
            'textbook_content': '본문',
            'summary': '정리',
            'problem_1': '문제 1',
            'problem_2': '문제 2',
            'problem_3': '문제 3',
        }
        
        # problem_X 형식 처리
        if section_type.startswith('problem_'):
            problem_num = section_type.replace('problem_', '')
            return f'문제 {problem_num}'
        
        return title_map.get(section_type, section_type)
    
    def _refine_content(self, content: str) -> str:
        """
        강의 대본 내용을 교재용 서술문으로 정제
        
        - 불필요한 강사 멘트 제거
        - 구어체를 문어체로 변환
        - 반복/강조 표현 정리
        - 학습 흐름 유지
        """
        if not content:
            return ""
        
        # 불필요한 패턴 제거
        patterns_to_remove = [
            r'여러분[,]?\s*',  # "여러분,"
            r'알겠지\?',
            r'알겠어\?',
            r'됐지\?',
            r'됐죠\?',
            r'맞죠\?',
            r'맞지\?',
            r'그렇지\?',
            r'그렇죠\?',
            r'오케이',
            r'좋아',
            r'자,\s*',  # "자,"
            r'그래서요[,]?\s*',
            r'그런데요[,]?\s*',
            r'그런데\s*',
            r'그러니까\s*',
            r'그래서\s*',
            r'그렇다면\s*',
            r'그러면\s*',
            r'그럼\s*',
            r'이제\s*',
            r'이렇게\s*',
            r'이런\s*',
            r'이거\s*',
            r'저거\s*',
            r'그거\s*',
            r'얘들아[,]?\s*',
            r'선생님[,]?\s*',
            r'제가\s*',
            r'저는\s*',
            r'저희는\s*',
            r'우리는\s*',
            r'우리\s*',
        ]
        
        refined = content
        for pattern in patterns_to_remove:
            refined = re.sub(pattern, '', refined, flags=re.IGNORECASE)
        
        # 문장 정리
        # "~거든요" → "~입니다"
        refined = re.sub(r'거든요', '입니다', refined)
        refined = re.sub(r'거든', '입니다', refined)
        
        # "~잖아요" → "~입니다"
        refined = re.sub(r'잖아요', '입니다', refined)
        refined = re.sub(r'잖아', '입니다', refined)
        
        # "~해요" → "~합니다"
        refined = re.sub(r'([가-힣])해요', r'\1합니다', refined)
        
        # "~해" → "~합니다" (문장 끝)
        refined = re.sub(r'([가-힣])해\.', r'\1합니다.', refined)
        
        # 불필요한 공백 정리
        refined = re.sub(r'\s+', ' ', refined)
        refined = re.sub(r'\s+([.!?])', r'\1', refined)
        
        # 문장 시작 대문자화
        sentences = re.split(r'([.!?]\s*)', refined)
        refined = ''
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                if i == 0 or (i > 0 and sentences[i-1] in ['. ', '! ', '? ']):
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 0 else sentence
                refined += sentence
        
        return refined.strip()
    
    def _extract_lesson_number_from_filename(self, filename: str) -> Optional[int]:
        """파일명에서 레슨 번호 추출"""
        # "01강", "1강", "01강_" 패턴
        patterns = [
            r'(\d+)\s*강',
            r'[^0-9](\d{2})강',
            r'^(\d{2})강',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1))
        
        return None


def process_lecture_scripts_directory(
    scripts_dir: Path,
    output_dir: Path,
    subject: str,
    file_pattern: str = "*.hwp"
) -> List[Dict[str, Any]]:
    """
    강의 대본 디렉토리를 일괄 처리
    
    Args:
        scripts_dir: 강의 대본 디렉토리
        output_dir: 출력 디렉토리
        subject: 과목명
        file_pattern: 파일 패턴
        
    Returns:
        처리된 레슨 목록
    """
    pipeline = LectureToJSONPipeline(subject=subject)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # 파일 목록 가져오기
    files = sorted(scripts_dir.glob(file_pattern))
    
    for file_path in files:
        try:
            # 강의 대본 처리
            json_data = pipeline.process_lecture_file(file_path)
            
            # JSON 파일로 저장
            lesson_id = json_data.get('lessonId', 'unknown')
            output_path = output_dir / f"{lesson_id}.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            results.append({
                'file': str(file_path),
                'lessonId': lesson_id,
                'output': str(output_path),
                'sections': len(json_data.get('sections', [])),
                'units': sum(len(s.get('units', [])) for s in json_data.get('sections', []))
            })
            
            print(f"[처리 완료] {file_path.name} → {output_path.name}")
            
        except Exception as e:
            print(f"[오류] {file_path.name}: {e}")
            continue
    
    return results
