"""
수학Ⅰ 과목 파싱 전략
"""
import re
import logging
from typing import List, Dict, Any, Optional

from .base_strategy import BaseParsingStrategy
from ..utils import group_texts_by_line, matches_patterns

logger = logging.getLogger(__name__)


class Math1ParsingStrategy(BaseParsingStrategy):
    """수학Ⅰ 과목 파싱 전략"""

    def extract_lectures(self, all_ocr_data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        수학Ⅰ 단원 목록 자동 생성

        수학 구조:
        - 단원(Unit): "1단원 지수함수와 로그함수"
        - 개념(Concept): "1. 지수함수", "(가) 지수함수"
        - 예제(Example): "예제 1"
        - 유제(Exercise): "유제 1"
        - 문제(Problem): "1.", "2."
        """
        units = []
        unit_id = 1
        patterns = config.get('lecture_title_patterns', [])

        # OCR 데이터 디버깅
        if all_ocr_data and len(all_ocr_data) > 0:
            first_page_ocr = all_ocr_data[0]
            first_page_texts = [t.strip() for t in first_page_ocr.get('text', []) if t.strip()]
            if first_page_texts:
                print(f"    [디버그] 첫 페이지 OCR 단어 샘플 (상위 20개):")
                for i, text in enumerate(first_page_texts[:20], 1):
                    print(f"      {i}. {text[:60]}")

        # 각 페이지에서 단원 제목 찾기
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])

            if not texts or len([t for t in texts if t.strip()]) == 0:
                continue

            # y좌표 기준으로 같은 줄의 단어들을 그룹화
            lines = group_texts_by_line(texts, tops, lefts, widths, heights)

            # 페이지 상단 영역 체크 (상단 30%)
            page_top_threshold = None
            if lines and len(lines) > 0 and len(lines[0]) > 0:
                first_line_y = lines[0][0]['top']
                if lines and len(lines[-1]) > 0:
                    last_line = lines[-1]
                    estimated_page_height = last_line[-1]['top'] + last_line[-1]['height']
                    page_top_threshold = first_line_y + (estimated_page_height * 0.3)

            # 평균 폰트 크기 계산
            if lines:
                total_height = sum(word['height'] for line in lines[:10] for word in line[:3])
                total_words = sum(len(line[:3]) for line in lines[:10])
                if total_words > 0:
                    avg_height = total_height / min(30, total_words)
                    min_title_height = avg_height * 1.0
                else:
                    min_title_height = 0
            else:
                min_title_height = 0

            for line in lines:
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()

                if not line_text or len(line_text) < 5:
                    continue

                # 페이지 상단 영역 체크
                line_y = line[0]['top']
                if page_top_threshold and line_y > page_top_threshold:
                    continue

                # 큰 폰트 체크
                line_height = max(word['height'] for word in line)
                if min_title_height > 0 and line_height < min_title_height * 0.9:
                    continue

                # 패턴 매칭
                if matches_patterns(line_text, patterns):
                    first_word = line[0]
                    last_word = line[-1]

                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)

                    units.append({
                        "lecture_id": unit_id,
                        "title": line_text,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
                    unit_id += 1
                    print(f"    ✓ 단원 발견: {line_text[:50]} (페이지 {page_num})")

        if not units:
            print(f"    ⚠️ 단원을 찾을 수 없습니다.")
            print(f"    사용된 패턴: {patterns}")

        return units

    def extract_problems(
        self,
        all_ocr_data: List[Dict[str, Any]],
        config: Dict[str, Any],
        existing_problem_keys: Optional[set] = None
    ) -> List[Dict[str, Any]]:
        """
        수학Ⅰ 문제 추출

        수학 문제 특징:
        - 문제 번호: "1.", "2." 형식
        - 수식이 많음 (이미지로 처리 필요)
        - 선택지: "①", "②", "③", "④", "⑤" 또는 "1)", "2)", "3)", "4)", "5)"
        """
        problems = []
        problem_id = 1
        pattern = config.get('problem_number_pattern', r'^\d+\.')

        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])

            if not texts:
                continue

            lines = group_texts_by_line(texts, tops, lefts, widths, heights)

            # 문제 번호가 있는 줄 찾기
            problem_starts = []
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()

                # 문제 번호 패턴 매칭 ("1.", "2." 등)
                if re.match(pattern, line_text):
                    problem_starts.append({
                        "number": line_text,
                        "line_idx": line_idx,
                        "y": line[0]['top']
                    })

            # 각 문제 영역 추출
            for j, problem_start in enumerate(problem_starts):
                start_line_idx = problem_start['line_idx']
                end_line_idx = problem_starts[j + 1]['line_idx'] if j + 1 < len(problem_starts) else len(lines)

                # 문제 영역의 모든 줄 추출
                problem_lines = lines[start_line_idx:end_line_idx]

                # 전체 텍스트 추출
                full_text = " ".join([" ".join([word['text'] for word in line]) for line in problem_lines])

                # 선택지 추출 (①~⑤ 또는 1)~5) 형식)
                choices = {}
                choice_patterns = [
                    r'[①②③④⑤]\s*(.+?)(?=[①②③④⑤]|$)',
                    r'(\d+)\)\s*(.+?)(?=\d+\)|$)',
                ]

                for pattern in choice_patterns:
                    matches = re.finditer(pattern, full_text)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            choice_num = match.group(1) if match.group(1) else str(len(choices) + 1)
                            choice_text = match.group(2).strip()
                            if choice_text:
                                choices[choice_num] = choice_text

                # 문제 질문 추출 (문제 번호 다음부터 선택지 전까지)
                question_match = re.search(r'^\d+\.\s*(.+?)(?=[①②③④⑤]|\d+\)|$)', full_text, re.DOTALL)
                question_text = question_match.group(1).strip() if question_match else ""

                # bbox 계산
                all_words = [word for line in problem_lines for word in line]
                if all_words:
                    left = min(w['left'] for w in all_words)
                    top = min(w['top'] for w in all_words)
                    right = max(w['left'] + w['width'] for w in all_words)
                    bottom = max(w['top'] + w['height'] for w in all_words)

                    problem = {
                        "problem_id": f"{problem_id:02d}",
                        "page": page_num,
                        "content": [full_text],  # 수학은 전체를 하나의 텍스트로
                        "choices": choices if choices else {},
                        "question_text": question_text,
                        "full_text": full_text
                    }

                    # 증분 파싱: 이미 파싱된 문제는 건너뛰기
                    problem_key = f"{page_num:02d}_{problem_id:02d}"
                    if existing_problem_keys and problem_key in existing_problem_keys:
                        print(f"    ⏭️ [문제 {problem_id}] 이미 파싱됨 (페이지 {page_num}) - 건너뜀")
                        problem_id += 1
                        continue

                    problems.append(problem)
                    problem_id += 1

        return problems
