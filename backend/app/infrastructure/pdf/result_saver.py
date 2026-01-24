"""
결과 저장기
파싱 결과를 JSON 파일로 저장
"""
import json
import logging
from pathlib import Path
from typing import List

from app.infrastructure.pdf.types import LectureInfo, JSONDict

logger = logging.getLogger(__name__)


class ResultSaver:
    """파싱 결과 저장기"""
    
    def __init__(self, subject: str, data_dir: Path, book_id: str = None):
        """
        Args:
            subject: 과목명
            data_dir: 데이터 디렉토리 경로 (기본 경로)
            book_id: 교재 ID (None이면 과목별, 지정하면 교재별)
        """
        self.subject = subject
        self.book_id = book_id
        
        # 교재별 디렉토리 구조: data/{subject}/{book_id}/
        if book_id:
            self.data_dir = Path(data_dir) / subject / book_id
        else:
            # 하위 호환성: 기존 방식 (과목별)
            self.data_dir = Path(data_dir) / subject
        
        self.lectures_dir = self.data_dir / "lectures"
        self.problems_dir = self.data_dir / "problems"
        
        # 디렉토리 생성
        self.lectures_dir.mkdir(parents=True, exist_ok=True)
        self.problems_dir.mkdir(parents=True, exist_ok=True)
    
    def clear(self):
        """
        기존 데이터 삭제 (새 PDF 업로드 시 사용)
        """
        import shutil
        
        logger.info(f"기존 데이터 삭제 시작: {self.data_dir}")
        
        # lectures 디렉토리 삭제 및 재생성
        if self.lectures_dir.exists():
            shutil.rmtree(self.lectures_dir)
            logger.info(f"강의 디렉토리 삭제: {self.lectures_dir}")
        self.lectures_dir.mkdir(parents=True, exist_ok=True)
        
        # problems 디렉토리 삭제 및 재생성
        if self.problems_dir.exists():
            shutil.rmtree(self.problems_dir)
            logger.info(f"문제 디렉토리 삭제: {self.problems_dir}")
        self.problems_dir.mkdir(parents=True, exist_ok=True)
        
        # content 디렉토리도 삭제 (있는 경우)
        content_dir = self.data_dir / "content"
        if content_dir.exists():
            shutil.rmtree(content_dir)
            logger.info(f"본문 디렉토리 삭제: {content_dir}")
        
        # 이미지 디렉토리도 삭제 (있는 경우)
        for img_dir_name in ["concepts_images", "content_images", "problems_images"]:
            img_dir = self.data_dir / img_dir_name
            if img_dir.exists():
                shutil.rmtree(img_dir)
                logger.info(f"이미지 디렉토리 삭제: {img_dir}")
        
        logger.info("기존 데이터 삭제 완료")
    
    def save(
        self,
        lectures: List[LectureInfo],
        lecture_contents: List[JSONDict],
        problems: List[JSONDict]
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
    
    def _save_lectures_list(self, lectures: List[LectureInfo]):
        """강의 목록 저장 (기존 데이터는 이미 clear()에서 삭제됨)"""
        lectures_json_path = self.lectures_dir / "lectures.json"
        
        # 새 강의 목록 생성 (기존 데이터는 이미 삭제되었으므로 병합 불필요)
        lecture_list = [
            {"lecture_id": l['lecture_id'], "title": l['title']}
            for l in lectures
        ]
        
        # 정렬
        lecture_list.sort(key=lambda x: x.get('lecture_id', 0))
        
        # 저장
        with open(lectures_json_path, 'w', encoding='utf-8') as f:
            json.dump(lecture_list, f, ensure_ascii=False, indent=2)
        
        logger.info(f"강의 목록 저장: {len(lecture_list)}개")
    
    def _save_lecture_contents(
        self,
        lecture_contents: List[JSONDict],
        problems: List[JSONDict]
    ):
        """강의 콘텐츠 저장 (processing 모듈에서 이미 처리된 섹션 사용)"""
        saved_count = 0
        
        for content in lecture_contents:
            lecture_id = content['lecture_id']
            lecture_file = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
            
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
        
        logger.info(f"{saved_count}개 강의 저장 완료")
