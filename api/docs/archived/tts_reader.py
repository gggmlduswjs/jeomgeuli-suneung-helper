"""
TTS 읽기 모듈
JSON의 content를 그대로 읽는다 (요약, 재작성, 변형 금지)
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TTSReader:
    """
    TTS 읽기 클래스
    
    원칙:
    - JSON의 content를 그대로 읽는다
    - 요약, 재작성, 변형 금지
    - 접근성(시각장애인)을 최우선으로 한다
    """
    
    def __init__(self, subject: str):
        """
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
        """
        self.subject = subject
        self.data_dir = Path(__file__).parent.parent.parent / "data" / subject
        self.lectures_dir = self.data_dir / "lectures"
    
    def read_lecture(self, lecture_id: int) -> List[str]:
        """
        강의 본문 읽기
        
        Args:
            lecture_id: 강의 ID
        
        Returns:
            읽을 텍스트 리스트 (sections → content 순서)
        """
        lecture_path = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
        
        if not lecture_path.exists():
            raise FileNotFoundError(f"강의 파일을 찾을 수 없습니다: {lecture_path}")
        
        with open(lecture_path, 'r', encoding='utf-8') as f:
            lecture_data = json.load(f)
        
        # sections → content 순서대로 읽기
        texts = []
        for section in lecture_data.get('sections', []):
            for content_text in section.get('content', []):
                if content_text.strip():
                    texts.append(content_text)
        
        return texts
    
    def read_section(self, lecture_id: int, section_title: str) -> List[str]:
        """
        특정 섹션만 읽기
        
        Args:
            lecture_id: 강의 ID
            section_title: 섹션 제목
        
        Returns:
            읽을 텍스트 리스트
        """
        lecture_path = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
        
        if not lecture_path.exists():
            raise FileNotFoundError(f"강의 파일을 찾을 수 없습니다: {lecture_path}")
        
        with open(lecture_path, 'r', encoding='utf-8') as f:
            lecture_data = json.load(f)
        
        texts = []
        for section in lecture_data.get('sections', []):
            if section.get('title') == section_title:
                for content_text in section.get('content', []):
                    if content_text.strip():
                        texts.append(content_text)
                break
        
        return texts
    
    def read_problem(self, problem_id: str) -> List[str]:
        """
        문제 읽기
        
        Args:
            problem_id: 문제 ID (예: "01")
        
        Returns:
            읽을 텍스트 리스트 (passage + question)
        """
        problems_dir = self.data_dir / "problems"
        problem_path = problems_dir / f"problem_{problem_id}.json"
        
        if not problem_path.exists():
            raise FileNotFoundError(f"문제 파일을 찾을 수 없습니다: {problem_path}")
        
        with open(problem_path, 'r', encoding='utf-8') as f:
            problem_data = json.load(f)
        
        texts = []
        # passage 읽기
        for content_text in problem_data.get('content', []):
            if content_text.strip():
                texts.append(content_text)
        
        return texts
