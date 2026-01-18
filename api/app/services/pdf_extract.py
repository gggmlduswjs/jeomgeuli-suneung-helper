"""
PDF 텍스트 추출 서비스
"""
import pdfplumber
from pathlib import Path
from typing import Optional
from app.core.config import settings


def extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
    """
    PDF에서 텍스트 추출 (개선된 버전)
    
    Args:
        pdf_path: PDF 파일 경로
    
    Returns:
        추출된 텍스트 또는 None
    """
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 레이아웃 정보를 고려한 텍스트 추출
                # layout=True: 레이아웃 정보를 고려하여 더 정확한 추출
                # x_tolerance, y_tolerance: 단어 간격 허용 범위
                page_text = page.extract_text(
                    layout=True,
                    x_tolerance=3,
                    y_tolerance=3
                )
                
                if page_text:
                    # 페이지별 텍스트 정리
                    cleaned_text = _clean_extracted_text(page_text, page_num)
                    text += cleaned_text + "\n\n"
        
        # 전체 텍스트 후처리
        text = _post_process_text(text)
        
        # 추출된 텍스트를 캐시에 저장
        if text:
            cache_path = settings.EXTRACTED_DIR / f"{pdf_path.stem}.txt"
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(text)
        
        return text if text else None
    except Exception as e:
        print(f"[pdf_extract] Error extracting text from PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def _clean_extracted_text(text: str, page_num: int) -> str:
    """페이지별 텍스트 정리"""
    import re
    
    # 페이지 번호 패턴 제거 (예: "책1.indb 1 24. 12. 30. 오후 4:40")
    text = re.sub(r'책\d+\.indb\s+\d+.*?\n', '', text)
    text = re.sub(r'^\d+\s+24\.\s+\d+\.\s+\d+\.\s+.*?\n', '', text, flags=re.MULTILINE)
    
    # 불필요한 반복 패턴 제거 (예: "25008-0001" 반복)
    text = re.sub(r'25008-\d{4}\s*\n', '', text)
    
    # 연속된 줄바꿈 정리 (3개 이상 -> 2개)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 한 글자씩 줄바꿈된 경우 합치기 (예: "이\n책의\n차례" -> "이 책의 차례")
    # 단, 실제 문단 구분은 유지
    lines = text.split('\n')
    cleaned_lines = []
    prev_line = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            if prev_line:
                cleaned_lines.append(prev_line)
                cleaned_lines.append("")
                prev_line = ""
            continue
        
        # 한 글자 또는 매우 짧은 줄인 경우 다음 줄과 합치기
        if len(line) <= 2 and prev_line:
            prev_line += line
        elif prev_line and not _is_sentence_end(prev_line):
            # 문장 끝이 아니면 합치기
            prev_line += " " + line
        else:
            if prev_line:
                cleaned_lines.append(prev_line)
            prev_line = line
    
    if prev_line:
        cleaned_lines.append(prev_line)
    
    return '\n'.join(cleaned_lines)


def _is_sentence_end(text: str) -> bool:
    """문장 끝인지 확인"""
    import re
    # 마침표, 물음표, 느낌표로 끝나는지 확인
    return bool(re.search(r'[.!?。！？]\s*$', text))


def _post_process_text(text: str) -> str:
    """전체 텍스트 후처리"""
    import re
    
    # 연속된 공백 정리
    text = re.sub(r' +', ' ', text)
    
    # 연속된 줄바꿈 정리 (4개 이상 -> 2개)
    text = re.sub(r'\n{4,}', '\n\n', text)
    
    # 페이지 번호나 메타데이터 패턴 제거
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    
    # 제어 문자만 제거 (수학 기호는 유지)
    # 제어 문자(줄바꿈, 탭 제외) 제거
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


def get_extracted_text(book_id: str) -> Optional[str]:
    """
    캐시된 추출 텍스트 조회
    
    Args:
        book_id: 교재 ID
    
    Returns:
        추출된 텍스트 또는 None
    """
    cache_path = settings.EXTRACTED_DIR / f"{book_id}.txt"
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    return None
