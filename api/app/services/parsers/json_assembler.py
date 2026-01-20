"""
JSON Assembler
중간 구조 → 최종 강의 JSON 변환
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from .intermediate_schema import IntermediateDocument, IntermediateBlock, BlockType

logger = logging.getLogger(__name__)


class JSONAssembler:
    """중간 구조를 최종 JSON으로 변환"""

    def __init__(self):
        pass

    def assemble_lecture_json(
        self,
        doc: IntermediateDocument,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        특정 강의의 최종 JSON 생성

        Args:
            doc: 중간 문서
            lecture_id: 강의 ID

        Returns:
            {
                "subject": str,
                "lecture_id": int,
                "title": str,
                "sections": [...],
                "problems": [...]
            }
        """
        # 강의 정보 찾기
        lecture_info = next(
            (l for l in doc.lectures if l.lecture_id == lecture_id),
            None
        )

        if not lecture_info:
            logger.warning(f"강의 {lecture_id}를 찾을 수 없음")
            return {}

        # 강의 블록들 가져오기
        blocks = doc.get_lecture_blocks(lecture_id)

        # sections 생성 (concept + passage)
        sections = []

        for block in blocks:
            if block.block_type == BlockType.CONCEPT:
                section = self._create_concept_section(block)
                if section:
                    sections.append(section)

            elif block.block_type == BlockType.PASSAGE:
                section = self._create_passage_section(block)
                if section:
                    sections.append(section)

        # problems 생성 (question 블록의 번호만)
        problems = []
        for block in blocks:
            if block.block_type == BlockType.QUESTION:
                question_id = block.metadata.question_id
                if question_id:
                    problems.append(question_id)

        # 최종 JSON 조립
        lecture_json = {
            "subject": doc.subject,
            "lecture_id": lecture_id,
            "title": lecture_info.title,
            "sections": sections,
            "problems": problems
        }

        return lecture_json

    def assemble_problem_json(
        self,
        doc: IntermediateDocument,
        question_block: IntermediateBlock
    ) -> Dict[str, Any]:
        """
        문제 JSON 생성

        Args:
            doc: 중간 문서
            question_block: 문제 블록

        Returns:
            {
                "problem_id": str,
                "page": int,
                "content": [...],
                "has_example": bool
            }
        """
        if question_block.block_type != BlockType.QUESTION:
            logger.warning(f"블록 {question_block.block_id}는 문제가 아님")
            return {}

        # 문제 내용 추출
        content = [line.text for line in question_block.raw_lines]

        # 보기 포함 여부 확인 (간단히 텍스트 검색)
        full_text = question_block.get_text()
        has_example = any(
            marker in full_text
            for marker in ["< 보기 >", "「보기」", "[보기]"]
        )

        problem_json = {
            "problem_id": question_block.metadata.question_id or "",
            "page": question_block.page,
            "content": content,
            "has_example": has_example
        }

        return problem_json

    def assemble_all_lectures(
        self,
        doc: IntermediateDocument
    ) -> List[Dict[str, Any]]:
        """
        모든 강의 JSON 생성

        Returns:
            강의 JSON 리스트
        """
        all_lectures = []

        for lecture_info in doc.lectures:
            lecture_json = self.assemble_lecture_json(doc, lecture_info.lecture_id)
            if lecture_json:
                all_lectures.append(lecture_json)

        return all_lectures

    def assemble_all_problems(
        self,
        doc: IntermediateDocument
    ) -> List[Dict[str, Any]]:
        """
        모든 문제 JSON 생성

        Returns:
            문제 JSON 리스트
        """
        all_problems = []

        for page in doc.pages:
            for block in page.blocks:
                if block.block_type == BlockType.QUESTION:
                    problem_json = self.assemble_problem_json(doc, block)
                    if problem_json:
                        all_problems.append(problem_json)

        return all_problems

    def _create_concept_section(self, block: IntermediateBlock) -> Optional[Dict[str, Any]]:
        """개념 블록 → section 변환"""
        if not block.raw_lines:
            return None

        return {
            "title": block.metadata.title or "개념",
            "content": [line.text for line in block.raw_lines],
            "page": block.page
        }

    def _create_passage_section(self, block: IntermediateBlock) -> Optional[Dict[str, Any]]:
        """작품 블록 → section 변환"""
        if not block.raw_lines:
            return None

        # 제목: "작가 - 「작품」"
        title = block.metadata.title
        if not title and block.metadata.author and block.metadata.work_title:
            title = f"{block.metadata.author} - 「{block.metadata.work_title}」"
        elif not title:
            title = "작품"

        return {
            "title": title,
            "content": [line.text for line in block.raw_lines],
            "page": block.page
        }

    def save_lectures_json(
        self,
        doc: IntermediateDocument,
        output_dir: Path
    ):
        """
        강의 JSON 파일들 저장

        생성 파일:
        - lectures.json: 강의 목록
        - lecture_01.json, lecture_02.json, ...: 개별 강의
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. 강의 목록 JSON
        lectures_list = []
        for lecture_info in doc.lectures:
            lectures_list.append({
                "lecture_id": lecture_info.lecture_id,
                "title": lecture_info.title,
                "start_page": lecture_info.start_page,
                "end_page": lecture_info.end_page
            })

        lectures_json_path = output_dir / "lectures.json"
        with open(lectures_json_path, 'w', encoding='utf-8') as f:
            json.dump(lectures_list, f, ensure_ascii=False, indent=2)
        logger.info(f"강의 목록 저장: {lectures_json_path}")

        # 2. 개별 강의 JSON
        for lecture_info in doc.lectures:
            lecture_json = self.assemble_lecture_json(doc, lecture_info.lecture_id)

            if lecture_json:
                lecture_file = output_dir / f"lecture_{lecture_info.lecture_id:02d}.json"
                with open(lecture_file, 'w', encoding='utf-8') as f:
                    json.dump(lecture_json, f, ensure_ascii=False, indent=2)
                logger.info(f"강의 저장: {lecture_file}")

    def save_problems_json(
        self,
        doc: IntermediateDocument,
        output_dir: Path
    ):
        """
        문제 JSON 파일들 저장

        생성 파일:
        - problem_01.json, problem_02.json, ...
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for page in doc.pages:
            for block in page.blocks:
                if block.block_type == BlockType.QUESTION:
                    problem_json = self.assemble_problem_json(doc, block)

                    if problem_json and problem_json.get('problem_id'):
                        problem_id = problem_json['problem_id']
                        problem_file = output_dir / f"problem_{problem_id}.json"

                        with open(problem_file, 'w', encoding='utf-8') as f:
                            json.dump(problem_json, f, ensure_ascii=False, indent=2)

                        logger.debug(f"문제 저장: {problem_file}")

        logger.info(f"문제 JSON 저장 완료: {output_dir}")

    def save_all(
        self,
        doc: IntermediateDocument,
        lectures_dir: Path,
        problems_dir: Path
    ):
        """
        모든 JSON 파일 저장

        Args:
            doc: 중간 문서
            lectures_dir: 강의 JSON 출력 디렉토리
            problems_dir: 문제 JSON 출력 디렉토리
        """
        # 강의 JSON 저장
        self.save_lectures_json(doc, lectures_dir)

        # 문제 JSON 저장
        self.save_problems_json(doc, problems_dir)

        logger.info("모든 JSON 파일 저장 완료")
