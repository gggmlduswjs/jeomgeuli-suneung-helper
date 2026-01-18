"""
PDF 텍스트 파싱 서비스
텍스트에서 강/단원 패턴 인식 및 Units 생성
"""
import re
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.db.models import Book, Lesson, Unit, UnitType, ParseStatus
from app.services.pdf_extract import extract_text_from_pdf, get_extracted_text
from app.core.config import settings


def parse_lessons_and_units(
    book_id: str,
    db: Session,
) -> bool:
    """
    PDF 텍스트를 파싱하여 Lessons와 Units 생성
    
    Args:
        book_id: 교재 ID
        db: 데이터베이스 세션
    
    Returns:
        성공 여부
    """
    try:
        # 교재 조회
        book = db.query(Book).filter(Book.book_id == book_id).first()
        if not book:
            return False
        
        # 파싱 상태 업데이트
        book.parse_status = ParseStatus.PROCESSING
        db.commit()
        
        # PDF에서 텍스트 추출
        pdf_path = Path(book.file_path)
        if not pdf_path.exists():
            error_msg = f"PDF 파일을 찾을 수 없습니다: {pdf_path}"
            print(f"[pdf_parse] {error_msg}")
            book.parse_status = ParseStatus.FAILED
            db.commit()
            return False
        
        text = get_extracted_text(book_id)
        if not text:
            print(f"[pdf_parse] 캐시된 텍스트 없음, PDF에서 추출 시도: {pdf_path}")
            text = extract_text_from_pdf(pdf_path)
        
        if not text:
            error_msg = f"PDF에서 텍스트를 추출할 수 없습니다: {pdf_path}"
            print(f"[pdf_parse] {error_msg}")
            book.parse_status = ParseStatus.FAILED
            db.commit()
            return False
        
        print(f"[pdf_parse] 텍스트 추출 성공: {len(text)} 문자")
        
        # 강 패턴 인식 (예: "01강", "02강", "1강", "2강" 등)
        lesson_pattern = re.compile(r'(\d+)\s*강\s*[:\-_]?\s*(.+?)(?=\d+\s*강|$)', re.MULTILINE | re.DOTALL)
        matches = list(lesson_pattern.finditer(text))
        
        if not matches:
            print(f"[pdf_parse] 기본 강 패턴 매칭 실패, 대체 패턴 시도")
            # 대체 패턴 시도
            lesson_pattern = re.compile(r'(\d+)\s*강', re.MULTILINE)
            matches = list(lesson_pattern.finditer(text))
        
        if not matches:
            print(f"[pdf_parse] 기본 강 패턴 매칭 실패, 대체 패턴 시도")
            
            # 다른 패턴들 시도
            alt_patterns = [
                (r'(\d+)\s*단원', '단원'),
                (r'Chapter\s*(\d+)', 'Chapter'),
                (r'제\s*(\d+)\s*장', '제X장'),
                (r'(\d+)\s*장', 'X장'),
            ]
            
            for pattern, name in alt_patterns:
                alt_matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
                if alt_matches:
                    print(f"[pdf_parse] 대체 패턴 발견: {name} ({len(alt_matches)}개)")
                    matches = alt_matches
                    break
            
            # 패턴을 전혀 찾지 못한 경우, 전체 텍스트를 하나의 강으로 생성
            if not matches:
                print(f"[pdf_parse] 모든 패턴 매칭 실패, 전체 텍스트를 하나의 강으로 생성")
                # 텍스트 샘플 출력 (디버깅용)
                text_sample = text[:500] if len(text) > 500 else text
                print(f"[pdf_parse] 텍스트 샘플 (처음 500자):\n{text_sample}")
                
                # 전체 텍스트를 하나의 강으로 처리하기 위해 가상의 match 생성
                class DummyMatch:
                    def group(self, i=1):
                        return '1' if i == 1 else '전체'
                    def groups(self):
                        return ('1', '전체')
                    def start(self):
                        return 0
                    def end(self):
                        return 0
                
                matches = [DummyMatch()]
        
        print(f"[pdf_parse] 강 패턴 매칭 성공: {len(matches)}개")
        
        lessons_data = []
        for i, match in enumerate(matches):
            lesson_num = int(match.group(1))
            lesson_title = match.group(2).strip() if len(match.groups()) > 1 else f"{lesson_num:02d}강"
            
            # 다음 매칭까지의 텍스트 추출
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            lesson_content = text[start_pos:end_pos].strip()
            
            lessons_data.append({
                "index": lesson_num,
                "title": lesson_title[:200],  # 제목 길이 제한
                "content": lesson_content,
            })
        
        if not lessons_data:
            error_msg = "강 데이터가 생성되지 않았습니다."
            print(f"[pdf_parse] {error_msg}")
            book.parse_status = ParseStatus.FAILED
            db.commit()
            return False
        
        print(f"[pdf_parse] {len(lessons_data)}개 강 생성 시작")
        
        # Lessons 및 Units 생성
        for lesson_data in lessons_data:
            lesson_id = f"ls_{book_id}_{lesson_data['index']:02d}"
            
            # Lesson 생성 또는 업데이트
            lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
            if not lesson:
                lesson = Lesson(
                    lesson_id=lesson_id,
                    book_id=book_id,
                    index=lesson_data['index'],
                    title=lesson_data['title'],
                )
                db.add(lesson)
                db.flush()
            
            # Units 파싱 (간단한 패턴 기반)
            units = _parse_units_from_lesson_content(lesson_data['content'], lesson_id, db)
            
            for unit_data in units:
                unit = db.query(Unit).filter(Unit.unit_id == unit_data['unit_id']).first()
                if not unit:
                    unit = Unit(**unit_data)
                    db.add(unit)
        
        db.commit()
        
        # 파싱 완료
        book.parse_status = ParseStatus.DONE
        db.commit()
        
        return True
    except Exception as e:
        print(f"[pdf_parse] Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
        
        # 파싱 실패
        book = db.query(Book).filter(Book.book_id == book_id).first()
        if book:
            book.parse_status = ParseStatus.FAILED
            db.commit()
        
        return False


def _parse_units_from_lesson_content(
    content: str,
    lesson_id: str,
    db: Session,
) -> List[Dict]:
    """
    강 내용에서 Units 추출
    
    Args:
        content: 강 내용 텍스트
        lesson_id: 강 ID
        db: 데이터베이스 세션
    
    Returns:
        Units 데이터 리스트
    """
    units = []
    order = 1
    
    # 간단한 패턴 기반 파싱
    # 1. 개념 섹션 찾기 (예: "핵심 포인트", "개념", "정리" 등)
    concept_patterns = [
        r'핵심\s*포인트',
        r'개념\s*정리',
        r'핵심\s*개념',
    ]
    
    # 2. 작품/지문 찾기 (예: "[작품명]", "작품:", "지문:" 등)
    passage_patterns = [
        r'\[([^\]]+)\]',  # [작품명]
        r'작품\s*[:：]',
        r'지문\s*[:：]',
    ]
    
    # 3. 문제 찾기 (예: "문제 1번", "1번 문제", "①", "②" 등)
    question_patterns = [
        r'문제\s*(\d+)\s*번',
        r'(\d+)\s*번\s*문제',
        r'[①-⑤]',
    ]
    
    # 간단한 구현: 내용을 문단으로 나누고 타입 추정
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    for para in paragraphs[:20]:  # 최대 20개 단위
        if len(para) < 10:  # 너무 짧으면 스킵
            continue
        
        unit_type = UnitType.CONCEPT_CORE
        title = para[:50]  # 첫 50자
        
        # 타입 추정
        if any(re.search(pattern, para, re.IGNORECASE) for pattern in question_patterns):
            unit_type = UnitType.QUESTION
            # 문제 지문과 선택지 추출 시도
            question_stem = para
            choices = []
            answer = None
            
            # 선택지 패턴 찾기
            choice_matches = re.findall(r'[①-⑤]\s*(.+?)(?=[①-⑤]|$)', para)
            if choice_matches:
                choices = [f"{chr(0x2460 + i)} {choice.strip()}" for i, choice in enumerate(choice_matches[:5])]
            
            unit_id = f"un_{lesson_id}_{order:03d}"
            units.append({
                "unit_id": unit_id,
                "lesson_id": lesson_id,
                "type": unit_type,
                "title": title,
                "order": order,
                "content_text": None,
                "question_stem": question_stem,
                "question_choices": json.dumps(choices, ensure_ascii=False) if choices else None,
                "question_answer": answer,
            })
        elif any(re.search(pattern, para, re.IGNORECASE) for pattern in passage_patterns):
            unit_type = UnitType.PASSAGE
            unit_id = f"un_{lesson_id}_{order:03d}"
            units.append({
                "unit_id": unit_id,
                "lesson_id": lesson_id,
                "type": unit_type,
                "title": title,
                "order": order,
                "content_text": para,
                "question_stem": None,
                "question_choices": None,
                "question_answer": None,
            })
        else:
            # 기본적으로 개념으로 처리
            unit_id = f"un_{lesson_id}_{order:03d}"
            units.append({
                "unit_id": unit_id,
                "lesson_id": lesson_id,
                "type": unit_type,
                "title": title,
                "order": order,
                "content_text": para,
                "question_stem": None,
                "question_choices": None,
                "question_answer": None,
            })
        
        order += 1
    
    return units
