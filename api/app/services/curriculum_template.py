"""
커리큘럼 템플릿 시스템
교재별 커리큘럼 템플릿 정의 및 의존성 규칙 관리
"""
import re
from typing import Dict, List, Any, Optional
from app.db.models import Subject


class CurriculumTemplate:
    """교재별 커리큘럼 템플릿"""
    
    LITERATURE_TEMPLATE = {
        'structure': [
            {'type': 'textbook_concept', 'order': 1, 'required': True, 'name': '교과서 개념'},
            {'type': 'classical_poetry', 'order': 2, 'required': True, 'name': '고전시가'},
            {'type': 'modern_poetry', 'order': 3, 'required': True, 'name': '현대시'},
            {'type': 'classical_prose', 'order': 4, 'required': True, 'name': '고전 산문'},
            {'type': 'modern_novel', 'order': 5, 'required': True, 'name': '현대 소설'},
            {'type': 'drama_essay', 'order': 6, 'required': True, 'name': '극 수필'},
            {'type': 'genre_complex', 'order': 7, 'required': True, 'name': '갈래 복합'},
            {'type': 'practice_1', 'order': 8, 'required': False, 'name': '실전 1회'},
            {'type': 'practice_2', 'order': 9, 'required': False, 'name': '실전 2회'},
        ],
        'dependencies': {
            'classical_poetry': ['textbook_concept'],
            'modern_poetry': ['textbook_concept'],
            'classical_prose': ['textbook_concept'],
            'modern_novel': ['textbook_concept'],
            'drama_essay': ['textbook_concept'],
            'genre_complex': ['classical_poetry', 'modern_poetry', 'classical_prose', 'modern_novel'],
            'practice_1': ['genre_complex'],
            'practice_2': ['practice_1'],
        }
    }
    
    MATH1_TEMPLATE = {
        'structure': [
            {'type': 'concept_review', 'order': 1, 'required': True, 'name': '개념정리'},
            {'type': 'example', 'order': 2, 'required': True, 'name': '예제'},
            {'type': 'exercise', 'order': 3, 'required': True, 'name': '유제'},
            {'type': 'level1', 'order': 4, 'required': False, 'name': 'LEVEL1'},
            {'type': 'level2', 'order': 5, 'required': False, 'name': 'LEVEL2'},
            {'type': 'level3', 'order': 6, 'required': False, 'name': 'LEVEL3'},
        ],
        'dependencies': {
            'example': ['concept_review'],
            'exercise': ['example'],
            'level1': ['exercise'],
            'level2': ['level1'],
            'level3': ['level2'],
        }
    }
    
    ENGLISH_TEMPLATE = {
        'structure': [
            {'type': 'purpose', 'order': 1, 'required': True, 'name': '글의 목적 파악'},
            {'type': 'mood', 'order': 2, 'required': False, 'name': '심경 분위기 파악'},
            {'type': 'main_idea', 'order': 3, 'required': False, 'name': '요지 파악'},
            {'type': 'argument', 'order': 4, 'required': False, 'name': '주장 파악'},
            {'type': 'implication', 'order': 5, 'required': False, 'name': '함축적 의미 파악'},
            {'type': 'topic', 'order': 6, 'required': False, 'name': '주제 파악'},
            {'type': 'chart', 'order': 7, 'required': False, 'name': '도표'},
            {'type': 'consistency', 'order': 8, 'required': False, 'name': '내용 일치 불일치'},
            {'type': 'grammar', 'order': 9, 'required': False, 'name': '어법'},
            {'type': 'vocabulary', 'order': 10, 'required': False, 'name': '어휘'},
            {'type': 'blank_inference', 'order': 11, 'required': False, 'name': '빈칸 내용 추론'},
            {'type': 'irrelevant_sentence', 'order': 12, 'required': False, 'name': '흐름에 무관한 문장 찾기'},
            {'type': 'sentence_order', 'order': 13, 'required': False, 'name': '문단 내 글의 순서 파악'},
            {'type': 'sentence_position', 'order': 14, 'required': False, 'name': '문장 위치'},
            {'type': 'sentence_placement', 'order': 15, 'required': False, 'name': '주어진 문장의 적합한 위치'},
            {'type': 'paragraph_summary', 'order': 16, 'required': False, 'name': '문단 요약하기'},
            {'type': 'long_reading', 'order': 17, 'required': False, 'name': '장문 독해'},
        ],
        'dependencies': {
            'mood': ['purpose'],
            'main_idea': ['purpose'],
            'argument': ['main_idea'],
            'long_reading': ['purpose', 'main_idea', 'topic'],
        }
    }
    
    @classmethod
    def get_template(cls, subject: Subject) -> Dict[str, Any]:
        """
        과목별 템플릿 반환
        
        Args:
            subject: Subject enum
            
        Returns:
            템플릿 딕셔너리
        """
        subject_map = {
            Subject.KOREAN: cls.LITERATURE_TEMPLATE,
            Subject.MATH: cls.MATH1_TEMPLATE,
            Subject.ENGLISH: cls.ENGLISH_TEMPLATE,
        }
        
        return subject_map.get(subject, cls.LITERATURE_TEMPLATE)
    
    @classmethod
    def get_dependencies(cls, subject: Subject, lesson_type: str) -> List[str]:
        """
        특정 레슨 타입의 의존성 반환
        
        Args:
            subject: Subject enum
            lesson_type: 레슨 타입 (예: 'classical_poetry')
            
        Returns:
            의존성 레슨 타입 리스트
        """
        template = cls.get_template(subject)
        return template.get('dependencies', {}).get(lesson_type, [])


class AutoCurriculumBuilder:
    """커리큘럼 자동 빌더"""
    
    def __init__(self, subject: Subject):
        """
        Args:
            subject: Subject enum
        """
        self.subject = subject
        self.template = CurriculumTemplate.get_template(subject)
        from app.services.curriculum_generator import CurriculumGenerator
        
        # subject를 문자열로 변환
        subject_str = subject.value.lower()
        if subject_str == 'korean':
            subject_str = 'literature'
        elif subject_str == 'math':
            subject_str = 'math1'
        
        self.generator = CurriculumGenerator(subject=subject_str)
        
    def build_curriculum(self, hwp_files: List[Any], pdf_path: Optional[Any] = None) -> Dict[str, Any]:
        """
        전체 커리큘럼 자동 생성
        
        Args:
            hwp_files: 강의대본 HWP 파일 리스트 (Path 객체 또는 경로 문자열)
            pdf_path: 수능특강 PDF 파일 (선택)
            
        Returns:
            {
                'subject': 'literature',
                'lessons': [...],
                'learning_path': [...],
                'connections': [...]
            }
        """
        from pathlib import Path
        
        # Path 객체로 변환
        hwp_paths = [Path(f) if isinstance(f, str) else f for f in hwp_files]
        if pdf_path:
            pdf_path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
        
        lessons = []
        
        # 1. 각 강의대본 분석
        for hwp_file in sorted(hwp_paths):
            if not hwp_file.exists():
                continue
                
            analysis = self.generator.analyze_lecture_script(hwp_file)
            
            lesson = {
                'lesson_number': analysis['lesson_number'],
                'title': self._extract_lesson_title(analysis, hwp_file),
                'learning_units': analysis['learning_units'],
                'sections': analysis['sections'],
                'pdf_references': analysis['pdf_references'],
                'dependencies': self._identify_dependencies(analysis),
                'estimated_time': self._estimate_time(analysis),
            }
            
            lessons.append(lesson)
        
        # 2. 학습 경로 생성 (의존성 기반)
        learning_path = self._create_learning_path(lessons)
        
        # 3. 유기적 연결 구조 생성
        connections = self._create_connections(lessons)
        
        return {
            'subject': self.subject.value.lower(),
            'lessons': lessons,
            'learning_path': learning_path,
            'connections': connections,
            'total_lessons': len(lessons),
            'total_units': sum(len(l['learning_units']) for l in lessons)
        }
    
    def _extract_lesson_title(self, analysis: Dict, hwp_path: Any) -> str:
        """레슨 제목 추출 (파일명 기반)"""
        from pathlib import Path
        from app.services.hwp_extract import extract_lesson_info_from_filename
        
        lesson_number = analysis.get('lesson_number', 0)
        
        # 파일명에서 추출 시도
        if isinstance(hwp_path, Path):
            filename = hwp_path.name
            
            # 파일명 패턴 분석
            # 예: "01강_[교과서_개념]_1_2_(고3_기본).hwp"
            #     "06강_[고전_시가]_02_03_04_(고3_기본).hwp"
            
            # 카테고리 추출
            category_match = re.search(r'\[([^\]]+)\]', filename)
            if category_match:
                category = category_match.group(1)
                # 카테고리 정리
                category = category.replace('_', ' ')
                
                # 번호 추출 (예: "1_2", "02_03_04")
                number_match = re.search(r'\]_(\d+(?:_\d+)*)', filename)
                if number_match:
                    numbers = number_match.group(1).replace('_', ', ')
                    return f"{lesson_number}강 [{category}] {numbers}"
                else:
                    return f"{lesson_number}강 [{category}]"
            
            # 기본 파일명에서 제목 추출
            lesson_info = extract_lesson_info_from_filename(filename)
            if lesson_info.get('title'):
                return f"{lesson_number}강 {lesson_info['title']}"
        
        # 섹션에서 추출
        sections = analysis.get('sections', [])
        if sections:
            first_section = sections[0]
            if first_section.get('type') == 'ot':
                # OT 섹션에서 제목 찾기
                content = first_section.get('content', '')
                # "수능특강 문학" 같은 패턴 찾기
                title_match = re.search(r'수능특강\s*([가-힣]+)', content)
                if title_match:
                    return f"{lesson_number}강 {title_match.group(1)}"
        
        # 기본값
        return f"{lesson_number}강"
    
    def _identify_dependencies(self, analysis: Dict) -> List[int]:
        """
        레슨 의존성 식별
        
        템플릿의 의존성 규칙을 기반으로 의존성 확인
        """
        dependencies = []
        lesson_number = analysis.get('lesson_number', 0)
        
        # 섹션 타입 확인
        sections = analysis.get('sections', [])
        if not sections:
            return dependencies
        
        # 첫 번째 주요 섹션 타입 확인
        main_section_type = None
        for section in sections:
            section_type = section.get('type', '')
            if section_type != 'ot' and section_type != 'general':
                main_section_type = section_type
                break
        
        if main_section_type:
            # 템플릿에서 의존성 확인
            deps = CurriculumTemplate.get_dependencies(self.subject, main_section_type)
            if deps:
                # 의존성 레슨 번호 찾기 (간단한 구현)
                # 실제로는 이전 레슨들을 확인해야 함
                pass
        
        return dependencies
    
    def _estimate_time(self, analysis: Dict) -> int:
        """
        예상 학습 시간 추정 (분 단위)
        
        학습 단위 수를 기반으로 추정
        """
        learning_units = analysis.get('learning_units', [])
        # 단위당 평균 5분 가정
        base_time = len(learning_units) * 5
        
        # 섹션 타입에 따라 조정
        sections = analysis.get('sections', [])
        for section in sections:
            section_type = section.get('type', '')
            if section_type == 'problem' or section_type == 'example':
                base_time += 3  # 문제/예제는 추가 시간
            elif section_type == 'summary':
                base_time += 2  # 정리는 추가 시간
        
        return max(30, base_time)  # 최소 30분
    
    def _create_learning_path(self, lessons: List[Dict]) -> List[Dict]:
        """
        학습 경로 생성 (의존성 기반)
        
        의존성을 고려하여 학습 순서 결정
        """
        learning_path = []
        completed = set()
        
        # 의존성이 없는 레슨부터 시작
        while len(completed) < len(lessons):
            progress_made = False
            
            for lesson in lessons:
                lesson_num = lesson.get('lesson_number', 0)
                if lesson_num in completed:
                    continue
                
                # 의존성 확인
                dependencies = lesson.get('dependencies', [])
                if all(dep in completed for dep in dependencies):
                    learning_path.append({
                        'lesson': lesson_num,
                        'order': len(learning_path) + 1,
                        'title': lesson.get('title', f'{lesson_num}강')
                    })
                    completed.add(lesson_num)
                    progress_made = True
            
            # 순환 의존성 방지
            if not progress_made:
                # 의존성이 없는 레슨을 강제로 추가
                for lesson in lessons:
                    lesson_num = lesson.get('lesson_number', 0)
                    if lesson_num not in completed:
                        learning_path.append({
                            'lesson': lesson_num,
                            'order': len(learning_path) + 1,
                            'title': lesson.get('title', f'{lesson_num}강')
                        })
                        completed.add(lesson_num)
                        break
        
        return learning_path
    
    def _create_connections(self, lessons: List[Dict]) -> List[Dict]:
        """
        레슨 간 유기적 연결 구조 생성
        
        - 이전 레슨에서 언급된 개념
        - 다음 레슨에서 활용할 내용
        - 관련 문제/예제 연결
        """
        connections = []
        
        for i, lesson in enumerate(lessons):
            lesson_num = lesson.get('lesson_number', 0)
            
            # 다음 레슨과의 연결
            if i + 1 < len(lessons):
                next_lesson = lessons[i + 1]
                next_lesson_num = next_lesson.get('lesson_number', 0)
                
                # 공통 키워드 찾기
                common_keywords = self._find_common_keywords(lesson, next_lesson)
                
                if common_keywords:
                    connections.append({
                        'from_lesson': lesson_num,
                        'to_lesson': next_lesson_num,
                        'type': 'sequential',
                        'keywords': common_keywords
                    })
        
        return connections
    
    def _find_common_keywords(self, lesson1: Dict, lesson2: Dict) -> List[str]:
        """두 레슨 간 공통 키워드 찾기"""
        import re
        
        # 키워드 추출 (간단한 구현)
        keywords1 = set()
        keywords2 = set()
        
        # 학습 단위에서 키워드 추출
        for unit in lesson1.get('learning_units', []):
            content = unit.get('content', '')
            # 한글 단어 추출 (2글자 이상)
            words = re.findall(r'[가-힣]{2,}', content)
            keywords1.update(words[:10])  # 최대 10개
        
        for unit in lesson2.get('learning_units', []):
            content = unit.get('content', '')
            words = re.findall(r'[가-힣]{2,}', content)
            keywords2.update(words[:10])
        
        # 공통 키워드
        common = keywords1 & keywords2
        return list(common)[:5]  # 최대 5개
