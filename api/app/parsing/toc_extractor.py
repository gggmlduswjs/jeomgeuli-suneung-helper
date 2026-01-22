"""
목차(Table of Contents) 자동 추출기
PDF의 목차 페이지에서 강의 구조를 자동으로 파악
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TOCExtractor:
    """목차 자동 추출 및 강의 구조 파악"""

    def __init__(self):
        self.patterns = {
            # 패턴 1: "1강 | 제목"
            'lecture_with_bar': r'^(\d+)강\s*[|]\s*(.+)',

            # 패턴 2: "01 제목 (작가) 페이지"
            'numbered_with_page': r'^(\d{2})\s+(.+?)\s+(\d{3})$',

            # 패턴 3: ">>> 섹션명"
            'section_marker': r'^>>>\s*(.+)',

            # 패턴 4: "N강" (단독)
            'lecture_simple': r'^(\d+)강\s+(.+)',
        }

    def extract_from_pdf(
        self,
        pdf_path: str,
        toc_pages: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        PDF에서 목차 자동 추출

        Args:
            pdf_path: PDF 파일 경로
            toc_pages: 목차 페이지 번호 리스트 (None이면 자동 감지)

        Returns:
            강의 목록 [{num, title, page, section}, ...]
        """
        if toc_pages is None:
            toc_pages = self._detect_toc_pages(pdf_path)

        logger.info(f"[TOC] 목차 페이지: {toc_pages}")

        # pdfplumber로 텍스트 추출
        import pdfplumber
        lectures = []
        current_section = None
        lecture_counter = 0

        with pdfplumber.open(pdf_path) as pdf:
            for page_num in toc_pages:
                if page_num >= len(pdf.pages):
                    continue

                page = pdf.pages[page_num]
                text = page.extract_text()

                if not text:
                    continue

                lines = text.split('\n')

                for line in lines:
                    line = line.strip()

                    # 섹션 마커 체크
                    section_match = re.match(self.patterns['section_marker'], line)
                    if section_match:
                        current_section = section_match.group(1).strip()
                        logger.info(f"[TOC] 섹션 발견: {current_section}")
                        continue

                    # 패턴 1: "N강 | 제목"
                    match = re.match(self.patterns['lecture_with_bar'], line)
                    if match:
                        num = int(match.group(1))
                        title = match.group(2).strip()

                        # 페이지 번호 추출
                        page_match = re.search(r'(\d{3})$', line)
                        page_no = int(page_match.group(1)) if page_match else None

                        # 제목 정리
                        title = re.sub(r'\s+\d{3}$', '', title).strip()

                        lectures.append({
                            'num': num,
                            'title': f'{num}강 | {title}',
                            'page': page_no,
                            'section': current_section
                        })
                        lecture_counter = num
                        continue

                    # 패턴 2: "01 제목 페이지" (부제 강의)
                    match = re.match(self.patterns['numbered_with_page'], line)
                    if match:
                        sub_num = int(match.group(1))
                        title = match.group(2).strip()
                        page_no = int(match.group(3))

                        # 전체 강의 번호 계산
                        lecture_num = lecture_counter + sub_num

                        lectures.append({
                            'num': lecture_num,
                            'title': f'{sub_num:02d} {title}',
                            'page': page_no,
                            'section': current_section
                        })

        logger.info(f"[TOC] 총 {len(lectures)}개 강의 추출")

        return lectures

    def _detect_toc_pages(self, pdf_path: str) -> List[int]:
        """
        목차 페이지 자동 감지

        휴리스틱:
        - 보통 2-7페이지 사이
        - "목차", "차례", "Contents" 키워드
        - "강", "장", "Chapter" 키워드가 많음
        """
        import pdfplumber

        toc_candidates = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(2, min(8, len(pdf.pages))):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""

                # 목차 키워드 체크
                score = 0
                if re.search(r'목차|차례|Contents', text, re.IGNORECASE):
                    score += 10

                # 강의 패턴 개수
                lecture_count = len(re.findall(r'\d+강', text))
                score += lecture_count

                if score > 5:
                    toc_candidates.append(page_num)

        # 기본값
        if not toc_candidates:
            toc_candidates = [2, 3, 4, 5, 6]

        return toc_candidates

    def save_mapping(self, book_id: str, lectures: List[Dict[str, Any]]):
        """강의 매핑을 파일로 저장 (캐시)"""
        cache_dir = Path(f"data/cache/lecture_maps")
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / f"{book_id}.json"

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(lectures, f, ensure_ascii=False, indent=2)

        logger.info(f"[TOC] 강의 매핑 저장: {cache_file}")

    def load_mapping(self, book_id: str) -> Optional[List[Dict[str, Any]]]:
        """저장된 강의 매핑 로드"""
        cache_file = Path(f"data/cache/lecture_maps/{book_id}.json")

        if not cache_file.exists():
            return None

        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)


def extract_toc_enhanced(pdf_path: str) -> List[Dict[str, Any]]:
    """
    개선된 목차 추출 (수능특강 문학 전용 튜닝)

    수능특강 문학 특징:
    - 1-9강: "N강 | 제목" 형식
    - 10강~: ">>> 섹션명" 다음에 "01 작품 페이지" 형식
    """
    import pdfplumber

    lectures = []
    current_section = None
    base_lecture_num = 9  # 1-9강 이후 시작

    with pdfplumber.open(pdf_path) as pdf:
        # 목차 페이지 3-7
        for page_num in range(2, 7):
            if page_num >= len(pdf.pages):
                continue

            page = pdf.pages[page_num]
            text = page.extract_text() or ""
            lines = text.split('\n')

            for line in lines:
                line = line.strip()

                # 1-9강 패턴
                match = re.match(r'^(\d+)강\s*[|]\s*(.+)', line)
                if match:
                    num = int(match.group(1))
                    title = match.group(2).strip()

                    # 페이지 번호
                    page_match = re.search(r'(\d{3})$', line)
                    page_no = int(page_match.group(1)) if page_match else None

                    lectures.append({
                        'num': num,
                        'title': f'{num}강 | {title}',
                        'page': page_no,
                        'section': '교과서 개념 학습'
                    })

                    if num > base_lecture_num:
                        base_lecture_num = num
                    continue

                # 섹션 마커
                if line.startswith('>>>'):
                    current_section = line.replace('>>>', '').strip()
                    continue

                # 10강 이후 패턴: "01 작품 페이지"
                match = re.match(r'^(\d{2})\s+(.+?)\s+(\d{3})$', line)
                if match and current_section:
                    sub_num = int(match.group(1))
                    title = match.group(2).strip()
                    page_no = int(match.group(3))

                    lecture_num = base_lecture_num + sub_num

                    lectures.append({
                        'num': lecture_num,
                        'title': f'{sub_num:02d} {title}',
                        'page': page_no,
                        'section': current_section
                    })

    return lectures
