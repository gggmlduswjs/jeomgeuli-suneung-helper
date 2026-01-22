"""
결과 저장기
파싱 결과를 JSON 파일로 저장
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ResultSaver:
    """파싱 결과 저장기"""
    
    def __init__(self, subject: str, data_dir: Path):
        """
        Args:
            subject: 과목명
            data_dir: 데이터 디렉토리 경로
        """
        self.subject = subject
        self.data_dir = Path(data_dir)
        self.lectures_dir = self.data_dir / "lectures"
        self.problems_dir = self.data_dir / "problems"
        
        # 디렉토리 생성
        self.lectures_dir.mkdir(parents=True, exist_ok=True)
        self.problems_dir.mkdir(parents=True, exist_ok=True)
    
    def save(
        self,
        lectures: List[Dict[str, Any]],
        lecture_contents: List[Dict[str, Any]],
        problems: List[Dict[str, Any]]
    ):
        """
        결과를 JSON 파일로 저장
        
        Args:
            lectures: 강의 목록
            lecture_contents: 강의 콘텐츠 리스트 (각 섹션에 content가 이미 매칭되어 있음)
            problems: 문제 리스트
        """
        # 1. lectures.json 저장
        self._save_lectures_list(lectures)
        
        # 2. lecture_XX.json 저장 (섹션별 content 포함)
        self._save_lecture_contents(lecture_contents, problems)
        
        # 3. problem_XX.json 저장 (필요시)
        # self._save_problems(problems)
    
    def _save_lectures_list(self, lectures: List[Dict[str, Any]]):
        """강의 목록 저장"""
        lectures_json_path = self.lectures_dir / "lectures.json"
        
        # 기존 파일 로드
        existing_lectures = []
        if lectures_json_path.exists():
            try:
                with open(lectures_json_path, 'r', encoding='utf-8') as f:
                    existing_lectures = json.load(f)
            except Exception as e:
                logger.warning(f"기존 강의 목록 로드 실패: {e}")
        
        # 기존 강의 ID 집합
        existing_ids = {l.get('lecture_id', 0) for l in existing_lectures}
        
        # 새 강의만 추가
        new_lectures = [
            {"lecture_id": l['lecture_id'], "title": l['title']}
            for l in lectures
            if l['lecture_id'] not in existing_ids
        ]
        
        # 병합 및 정렬
        all_lectures = existing_lectures + new_lectures
        all_lectures.sort(key=lambda x: x.get('lecture_id', 0))
        
        # 저장
        with open(lectures_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_lectures, f, ensure_ascii=False, indent=2)
        
        logger.info(f"강의 목록 저장: {len(all_lectures)}개 (기존: {len(existing_lectures)}, 새: {len(new_lectures)})")
    
    def _save_lecture_contents(
        self, 
        lecture_contents: List[Dict[str, Any]],
        problems: List[Dict[str, Any]]
    ):
        """강의 콘텐츠 저장 (processing 모듈에서 이미 처리된 섹션 사용)"""
        # 기존 강의 ID 집합 (증분 파싱용)
        existing_lecture_ids = set()
        lectures_json_path = self.lectures_dir / "lectures.json"
        if lectures_json_path.exists():
            try:
                with open(lectures_json_path, 'r', encoding='utf-8') as f:
                    existing_lectures = json.load(f)
                    existing_lecture_ids = {l.get('lecture_id', 0) for l in existing_lectures}
            except Exception as e:
                logger.warning(f"기존 강의 목록 로드 실패: {e}")
        
        saved_count = 0
        skipped_count = 0
        
        for content in lecture_contents:
            lecture_id = content['lecture_id']
            lecture_file = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
            
            # 증분 파싱: 기존 파일이 있고 기존 강의 목록에 있으면 건너뛰기
            if lecture_file.exists() and lecture_id in existing_lecture_ids:
                logger.debug(f"강의 {lecture_id}는 이미 저장됨 - 건너뜀")
                skipped_count += 1
                continue
            
            # 섹션 데이터 (processing 모듈에서 이미 content가 매칭되어 있음)
            sections = content.get('sections', [])
            
            # 각 섹션이 올바른 형식인지 확인
            formatted_sections = []
            for section in sections:
                formatted_sections.append({
                    "title": section.get('title', ''),
                    "type": section.get('type', 'concept'),
                    "page": section.get('page', 0),
                    "content": section.get('content', [])  # 이미 매칭된 content 사용
                })
            
            # 강의에 속한 문제 찾기 (페이지 범위 기반)
            lecture_problems = []
            start_page = content.get('start_page', 0)
            end_page = content.get('end_page', 0)
            
            if start_page > 0 and end_page > 0:
                for problem in problems:
                    problem_page = problem.get('page', 0)
                    if start_page <= problem_page <= end_page:
                        problem_id = problem.get('problem_id', '')
                        if problem_id:
                            lecture_problems.append(problem_id)
            
            # JSON 구조 생성
            lecture_data = {
                "subject": self.subject,
                "lecture_id": lecture_id,
                "title": content['title'],
                "sections": formatted_sections,
                "problems": lecture_problems
            }
            
            # 저장
            with open(lecture_file, 'w', encoding='utf-8') as f:
                json.dump(lecture_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"강의 {lecture_id} 저장: {lecture_file} ({len(formatted_sections)}개 섹션, {len(lecture_problems)}개 문제)")
            saved_count += 1
        
        if skipped_count > 0:
            logger.info(f"증분 파싱: {skipped_count}개 강의 건너뜀 (이미 저장됨)")
        if saved_count > 0:
            logger.info(f"{saved_count}개 새 강의 저장 완료")
