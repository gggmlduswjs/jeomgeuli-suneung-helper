"""
결과 저장기
파싱 결과를 JSON 파일로 저장
"""
import json
import logging
import shutil
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
        self.ocr_data_dir = self.data_dir / "ocr_data"

        # 디렉토리 생성
        self.lectures_dir.mkdir(parents=True, exist_ok=True)
        self.problems_dir.mkdir(parents=True, exist_ok=True)
        self.ocr_data_dir.mkdir(parents=True, exist_ok=True)
    
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
        
        # 이미지 디렉토리는 삭제하지 않음 (unified_parser가 이미 생성함)
        # for img_dir_name in ["concepts_images", "content_images", "problems_images"]:
        #     img_dir = self.data_dir / img_dir_name
        #     if img_dir.exists():
        #         shutil.rmtree(img_dir)
        #         logger.info(f"이미지 디렉토리 삭제: {img_dir}")
        
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
                    "bbox": section.get('bbox', []),  # bbox 추가 (이미지 크롭용)
                    "content": section.get('content', [])  # 이미 매칭된 content 사용
                })
            
            # 강의에 속한 문제 찾기 (페이지 범위 기반, 중복 제거)
            lecture_problems = []
            seen_problems = set()  # (page, problem_id) 튜플로 중복 체크
            start_page = content.get('start_page', 0)
            end_page = content.get('end_page', 0)

            logger.debug(f"[ResultSaver] 강의 {lecture_id}: 페이지 범위 {start_page}~{end_page}")

            if start_page > 0 and end_page > 0:
                for problem in problems:
                    problem_page = problem.get('page', 0)
                    if start_page <= problem_page <= end_page:
                        problem_id = problem.get('problem_id', '')
                        if problem_id:
                            # 페이지+문제ID로 중복 체크
                            problem_key = (problem_page, problem_id)
                            if problem_key not in seen_problems:
                                lecture_problems.append(problem)  # 전체 problem 객체 추가
                                seen_problems.add(problem_key)
                                logger.debug(f"[ResultSaver]   문제 추가: {problem_id} (page {problem_page})")
                    elif problem_page > 0:  # 디버깅: 범위 밖의 문제 로그
                        logger.debug(f"[ResultSaver]   문제 제외: {problem.get('problem_id', '')} (page {problem_page}, 범위 밖)")
            
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

    def save_ocr_data(self, ocr_data: List[JSONDict]):
        """
        OCR 데이터를 페이지별 JSON 파일로 저장

        Args:
            ocr_data: OCR 추출 결과 (페이지별 리스트)
        """
        if not ocr_data:
            logger.warning("OCR 데이터가 비어있어 저장하지 않습니다.")
            return

        saved_count = 0
        for page_data in ocr_data:
            page_num = page_data.get('page_num', 0)
            if page_num <= 0:
                logger.warning(f"유효하지 않은 페이지 번호: {page_num}, 건너뜁니다.")
                continue

            # 파일명: page_001.json, page_002.json, ...
            ocr_file = self.ocr_data_dir / f"page_{page_num:03d}.json"

            with open(ocr_file, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False, indent=2)

            saved_count += 1

        logger.info(f"OCR 데이터 저장 완료: {saved_count}개 페이지 -> {self.ocr_data_dir}")

    def copy_original_pdf(self, pdf_path: Path):
        """
        원본 PDF 파일을 교재 디렉토리에 복사

        Args:
            pdf_path: 원본 PDF 파일 경로
        """
        if not pdf_path or not Path(pdf_path).exists():
            logger.warning(f"원본 PDF 파일을 찾을 수 없습니다: {pdf_path}")
            return

        dest_path = self.data_dir / "original.pdf"

        try:
            shutil.copy2(pdf_path, dest_path)
            logger.info(f"원본 PDF 복사 완료: {pdf_path} -> {dest_path}")
        except Exception as e:
            logger.error(f"원본 PDF 복사 실패: {e}")
            raise
