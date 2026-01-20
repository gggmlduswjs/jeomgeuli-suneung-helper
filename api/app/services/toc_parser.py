"""
목차(TOC) 파서
PDF 목차 페이지를 파싱하여 섹션 구조와 페이지 번호 추출
"""
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TOCParser:
    """
    목차 파서
    
    목차 구조 예시:
    - 1부 교과서 개념 학습
      - 1강 | 시의 표현과 형식 (009)
      - 2강 | 시의 내용 (012)
    - 2부 적용 학습
      - >>> 고전 시가
        - 01 모죽지랑가 (044)
    """
    
    # 강 번호 패턴 (더 유연하게)
    LESSON_PATTERN = re.compile(r'(\d+)\s*강\s*[|]?\s*(.+?)\s+(\d{2,3})')
    
    # 섹션 패턴 (>>> 고전 시가 등)
    SECTION_PATTERN = re.compile(r'>>>\s*([가-힣\s]+)')
    
    # 항목 패턴 (01 모죽지랑가 (득오) 044)
    ITEM_PATTERN = re.compile(r'(\d{2})\s+(.+?)\s+(\d{3})')
    
    # 회 패턴 (1회 [01~04] ... 296)
    ROUND_PATTERN = re.compile(r'(\d+)\s*회\s*\[?\s*(\d{2})\s*[~-]\s*(\d{2})\s*\]?\s*(.+?)\s+(\d{3})')
    
    def parse_toc_text(self, toc_text: str) -> Dict[str, Any]:
        """
        목차 텍스트 파싱
        
        Args:
            toc_text: 목차 텍스트
        
        Returns:
            {
                "parts": [
                    {
                        "part_name": "1부 교과서 개념 학습",
                        "lessons": [
                            {"lesson_number": 1, "title": "시의 표현과 형식", "page": 9}
                        ]
                    }
                ],
                "sections": [
                    {
                        "section_name": "고전 시가",
                        "items": [
                            {"item_number": 1, "title": "모죽지랑가", "page": 44}
                        ]
                    }
                ],
                "rounds": [
                    {
                        "round_number": 1,
                        "problems": [
                            {"range": "01~04", "title": "청백운", "page": 296}
                        ]
                    }
                ]
            }
        """
        result = {
            "parts": [],
            "sections": [],
            "rounds": []
        }
        
        lines = toc_text.split('\n')
        current_part = None
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 1부, 2부 패턴 (더 유연하게)
            part_match = re.search(r'(\d+)\s*부\s*(.+?)(?:\s+\d+\s*부|$)', line)
            if not part_match:
                # "1부 교과서 개념 학습" 같은 패턴
                part_match = re.search(r'(\d+)\s*부\s*([가-힣\s]+)', line)
            
            if part_match:
                part_num = int(part_match.group(1))
                part_name = part_match.group(2).strip()
                current_part = {
                    "part_number": part_num,
                    "part_name": part_name,
                    "lessons": []
                }
                result["parts"].append(current_part)
                continue
            
            # 강 패턴 (1강 | 시의 표현과 형식 ... 009)
            lesson_match = self.LESSON_PATTERN.search(line)
            if lesson_match:
                lesson_num = int(lesson_match.group(1))
                title = lesson_match.group(2).strip()
                page_str = lesson_match.group(3)
                page = int(page_str)
                
                # current_part가 없으면 자동 생성
                if not current_part:
                    current_part = {
                        "part_number": 1,
                        "part_name": "교과서 개념 학습",
                        "lessons": []
                    }
                    result["parts"].append(current_part)
                
                current_part["lessons"].append({
                    "lesson_number": lesson_num,
                    "title": title,
                    "page": page
                })
                continue
            
            # 섹션 패턴 (>>> 고전 시가)
            section_match = self.SECTION_PATTERN.search(line)
            if section_match:
                section_name = section_match.group(1).strip()
                current_section = {
                    "section_name": section_name,
                    "items": []
                }
                result["sections"].append(current_section)
                continue
            
            # 항목 패턴 (01 모죽지랑가(득오) / 화왕가(이익) 044)
            if current_section:
                # 여러 작품이 / 로 구분된 경우 처리
                item_parts = line.split('/')
                page_match = re.search(r'(\d{3})\s*$', line)
                if page_match:
                    page = int(page_match.group(1))
                    
                    for item_part in item_parts:
                        item_match = re.search(r'(\d{2})\s+(.+?)(?:\s*\(|$)', item_part)
                        if item_match:
                            item_num = int(item_match.group(1))
                            title = item_match.group(2).strip()
                            
                            current_section["items"].append({
                                "item_number": item_num,
                                "title": title,
                                "page": page
                            })
            
            # 회 패턴 (1회 [01~04] 청백운 (작자 미상) 296)
            round_match = self.ROUND_PATTERN.search(line)
            if round_match:
                round_num = int(round_match.group(1))
                start_problem = int(round_match.group(2))
                end_problem = int(round_match.group(3))
                title = round_match.group(4).strip()
                page = int(round_match.group(5))
                
                # 해당 회 찾기 또는 생성
                round_obj = next(
                    (r for r in result["rounds"] if r["round_number"] == round_num),
                    None
                )
                if not round_obj:
                    round_obj = {
                        "round_number": round_num,
                        "problems": []
                    }
                    result["rounds"].append(round_obj)
                
                round_obj["problems"].append({
                    "range": f"{round_match.group(2)}~{round_match.group(3)}",
                    "start": start_problem,
                    "end": end_problem,
                    "title": title,
                    "page": page
                })
        
        return result
    
    def find_toc_page(self, pdf_path: Path, max_pages: int = 20) -> Optional[List[int]]:
        """
        PDF에서 목차 페이지 찾기 (여러 페이지 지원)
        
        Args:
            pdf_path: PDF 파일 경로
            max_pages: 검색할 최대 페이지 수
        
        Returns:
            목차 페이지 번호 리스트 (1-based) 또는 None
        """
        try:
            import pdfplumber
            
            toc_pages = []
            toc_keywords = [
                # 부/파트 관련
                "1부", "2부", "부 교과서", "부 적용",
                "교과서 개념 학습", "적용 학습",
                # 목차 표시
                "목차", "차례", "INDEX", "CONTENTS",
                # 강 번호 패턴
                r"\d+\s*강\s*[|]",  # "1강 |", "2강 |"
                # 섹션 패턴
                ">>> 고전", ">>> 현대", ">>> 소설",
                # 페이지 번호 패턴 (목차에 자주 나타남)
                r"\d{3}\s*$",  # "009", "012" 등
            ]
            
            with pdfplumber.open(pdf_path) as pdf:
                # 처음 N페이지에서 목차 찾기
                search_range = range(1, min(max_pages + 1, len(pdf.pages) + 1))
                
                for page_num in search_range:
                    page = pdf.pages[page_num - 1]
                    text = page.extract_text() or ""
                    
                    if not text.strip():
                        continue
                    
                    # 키워드 매칭 점수 계산
                    score = 0
                    matched_keywords = []
                    
                    # 문자열 키워드 확인
                    for keyword in toc_keywords[:6]:  # 문자열 키워드만
                        if keyword in text:
                            score += 2
                            matched_keywords.append(keyword)
                    
                    # 정규식 패턴 확인
                    import re
                    for pattern in toc_keywords[6:]:
                        if re.search(pattern, text):
                            score += 1
                    
                    # 목차 특징: 강 번호와 페이지 번호가 함께 나타남
                    has_lesson_pattern = bool(re.search(r'\d+\s*강\s*[|]', text))
                    has_page_numbers = bool(re.search(r'\d{3}\s*$', text, re.MULTILINE))
                    
                    if has_lesson_pattern and has_page_numbers:
                        score += 5
                    
                    # 점수가 3 이상이면 목차 페이지로 판단
                    if score >= 3:
                        toc_pages.append(page_num)
                        logger.info(f"목차 페이지 발견: {page_num} (점수: {score}, 키워드: {matched_keywords})")
            
            return toc_pages if toc_pages else None
        except Exception as e:
            logger.error(f"목차 페이지 찾기 실패: {e}")
        
        return None
    
    def extract_toc_from_pdf(self, pdf_path: Path, use_ocr: bool = False) -> Optional[Dict[str, Any]]:
        """
        PDF에서 목차 추출 (여러 페이지 지원)
        
        Args:
            pdf_path: PDF 파일 경로
            use_ocr: OCR 사용 여부 (이미지 기반 목차용)
        
        Returns:
            파싱된 목차 구조 또는 None
        """
        toc_pages = self.find_toc_page(pdf_path)
        if not toc_pages:
            logger.warning("목차 페이지를 찾을 수 없습니다.")
            # OCR 시도 (선택적)
            if use_ocr:
                return self._extract_toc_with_ocr(pdf_path)
            return None
        
        try:
            import pdfplumber
            
            # 여러 페이지 목차 텍스트 합치기
            all_toc_text = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for toc_page_num in toc_pages:
                    page = pdf.pages[toc_page_num - 1]
                    page_text = page.extract_text() or ""
                    
                    if page_text:
                        all_toc_text.append(page_text)
            
            if not all_toc_text:
                logger.warning("목차 텍스트를 추출할 수 없습니다.")
                if use_ocr:
                    return self._extract_toc_with_ocr(pdf_path)
                return None
            
            # 모든 페이지 텍스트 합치기
            combined_toc_text = "\n".join(all_toc_text)
            
            # 목차 파싱
            parsed = self.parse_toc_text(combined_toc_text)
            
            # 결과 검증
            has_parts = len(parsed.get('parts', [])) > 0
            has_sections = len(parsed.get('sections', [])) > 0
            has_rounds = len(parsed.get('rounds', [])) > 0
            
            if not (has_parts or has_sections or has_rounds):
                logger.warning("목차 파싱 결과가 비어있습니다. OCR 시도...")
                if use_ocr:
                    return self._extract_toc_with_ocr(pdf_path)
                return None
            
            logger.info(f"목차 파싱 완료: {len(parsed.get('parts', []))}개 부, "
                      f"{len(parsed.get('sections', []))}개 섹션, "
                      f"{len(parsed.get('rounds', []))}개 회")
            
            return parsed
        except Exception as e:
            logger.error(f"목차 추출 실패: {e}")
            if use_ocr:
                return self._extract_toc_with_ocr(pdf_path)
            return None
    
    def _extract_toc_with_ocr(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """
        OCR을 사용하여 목차 추출 (이미지 기반 목차용)
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            파싱된 목차 구조 또는 None
        """
        try:
            import pytesseract
            from pdf2image import convert_from_path
            from pytesseract import Output
            
            # 처음 5페이지를 OCR로 스캔
            images = convert_from_path(
                pdf_path,
                dpi=300,
                first_page=1,
                last_page=min(5, 10)
            )
            
            all_toc_text = []
            for page_num, image in enumerate(images, 1):
                try:
                    # OCR로 텍스트 추출
                    ocr_data = pytesseract.image_to_data(
                        image,
                        lang='kor+eng',
                        output_type=Output.DICT
                    )
                    
                    # 텍스트 합치기
                    page_text = ' '.join([
                        text for text in ocr_data['text']
                        if text.strip() and int(ocr_data['conf'][ocr_data['text'].index(text)]) > 30
                    ])
                    
                    # 목차 키워드 확인
                    if any(kw in page_text for kw in ["1부", "2부", "강", ">>>"]):
                        all_toc_text.append(page_text)
                        logger.info(f"OCR로 목차 페이지 발견: {page_num}")
                except Exception as e:
                    logger.debug(f"페이지 {page_num} OCR 실패: {e}")
                    continue
            
            if not all_toc_text:
                return None
            
            combined_text = "\n".join(all_toc_text)
            parsed = self.parse_toc_text(combined_text)
            
            return parsed if (parsed.get('parts') or parsed.get('sections')) else None
        except Exception as e:
            logger.debug(f"OCR 기반 목차 추출 실패: {e}")
            return None
