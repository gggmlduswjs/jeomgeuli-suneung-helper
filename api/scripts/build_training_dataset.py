"""
학습 데이터셋 자동 구축 스크립트
실제 강의 대본(텍스트)도 활용 가능
"""
import sys
from pathlib import Path
import json
import re
from datetime import datetime

# api 디렉토리를 Python 경로에 추가 (app 모듈을 찾기 위해)
api_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(api_dir))

# 프로젝트 루트 경로 (데이터 파일 경로용)
project_root = api_dir.parent

from app.services.hwp_extract import extract_text_from_hwp, extract_structure_from_hwp, extract_lesson_info_from_filename
from app.services.pdf_extract import extract_text_from_pdf
from app.services.braille_convert import text_to_braille


def parse_lecture_script(script_text: str) -> dict:
    """실제 강의 대본 파싱
    
    예시: 수능특강 문학 1강 대본
    """
    sections = []
    
    # 섹션별 패턴 매칭
    patterns = {
        "intro": r"\[인트로\]",
        "concept": r"\[개념 설명",
        "work_analysis": r"\[작품 분석",
        "problem": r"\[문제 풀이",
        "practice": r"\[기출 탈탈",
        "summary": r"\[한 판에 담판\]"
    }
    
    # 말하는 단위로 분할
    speech_units = split_by_speech_unit(script_text)
    
    for unit in speech_units:
        section_type = detect_section_type(unit, patterns)
        sections.append({
            "type": section_type,
            "content": unit,
            "braille": text_to_braille(unit),
            "length": len(unit)
        })
    
    return {
        "sections": sections,
        "total_length": len(script_text),
        "speech_units_count": len(speech_units)
    }


def split_by_speech_unit(text: str) -> list:
    """말하는 단위로 분할 (실제 대본 기반)
    
    - 문장 단위 (마침표, 물음표, 느낌표)
    - 자연스러운 끊김 지점
    - 적절한 길이 (50-200자)
    """
    # 문장 단위 분할
    sentences = re.split(r'[.!?]\s+', text)
    
    units = []
    current_unit = ""
    
    for sentence in sentences:
        if len(current_unit) + len(sentence) < 150:  # 적절한 길이
            current_unit += sentence + ". "
        else:
            if current_unit:
                units.append(current_unit.strip())
            current_unit = sentence + ". "
    
    if current_unit:
        units.append(current_unit.strip())
    
    return units


def detect_section_type(unit: str, patterns: dict) -> str:
    """섹션 타입 감지"""
    for section_type, pattern in patterns.items():
        if re.search(pattern, unit, re.IGNORECASE):
            return section_type
    return "general"


def extract_lesson_number(filename: str) -> int:
    """파일명에서 강 번호 추출"""
    match = re.search(r'(\d+)강', filename)
    if match:
        return int(match.group(1))
    return 0


def extract_category(filename: str) -> str:
    """파일명에서 카테고리 추출"""
    match = re.search(r'\[([^\]]+)\]', filename)
    if match:
        return match.group(1)
    return ""


def extract_subject_from_filename(filename: str) -> str:
    """파일명에서 과목 추출"""
    if '문학' in filename:
        return '문학'
    elif '수학' in filename or '수1' in filename or '수2' in filename:
        return '수학'
    elif '영어' in filename:
        return '영어'
    return '기타'


def extract_subject_from_folder_name(folder_name: str) -> str:
    """폴더명에서 과목 추출"""
    if '문학' in folder_name:
        return '문학'
    elif '수학' in folder_name or '수1' in folder_name or '수2' in folder_name:
        return '수학'
    elif '영어' in folder_name:
        return '영어'
    elif '독서' in folder_name:
        return '독서'
    elif '화법' in folder_name or '작문' in folder_name:
        return '화법과작문'
    return '기타'


def build_braille_dataset(
    hwp_dir: Path = None,
    pdf_dir: Path = None,
    output_path: Path = None
):
    """점자 변환 학습 데이터셋 구축"""
    if hwp_dir is None:
        hwp_dir = project_root / "data" / "lecture_scripts"
    if pdf_dir is None:
        pdf_dir = project_root / "data" / "pdfs"
    if output_path is None:
        output_path = project_root / "data" / "datasets" / "braille_dataset.json"
    
    dataset = {
        "dataset_version": "1.0",
        "created_at": datetime.now().isoformat(),
        "items": []
    }
    
    # 한글 파일 처리 (과목별 폴더 구조 지원)
    if hwp_dir.exists():
        # 과목별 폴더 탐색
        subject_folders = [d for d in hwp_dir.iterdir() if d.is_dir()]
        
        if subject_folders:
            # 과목별 폴더가 있는 경우
            for subject_folder in subject_folders:
                subject_name = subject_folder.name
                hwp_files = list(subject_folder.glob("*.hwp"))
                print(f"Processing subject folder: {subject_name} ({len(hwp_files)} files)")
                
                for idx, hwp_file in enumerate(hwp_files, 1):
                    print(f"  [{idx}/{len(hwp_files)}] Processing HWP: {hwp_file.name}")
                    try:
                        text = extract_text_from_hwp(hwp_file)
                        if not text:
                            print(f"    ⚠️  텍스트 추출 실패")
                            continue
                    
                        structure = extract_structure_from_hwp(hwp_file)
                        braille = text_to_braille(text)
                        
                        # 강 번호 추출 (파일명에서)
                        lesson_num = extract_lesson_number(hwp_file.name)
                        category = extract_category(hwp_file.name)
                        
                        # 과목명 추출 (폴더명에서)
                        subject = extract_subject_from_folder_name(subject_name)
                        
                        dataset["items"].append({
                            "id": f"item_{len(dataset['items']):03d}",
                            "source": "hwp",
                            "source_file": f"{subject_name}/{hwp_file.name}",
                            "subject_folder": subject_name,
                            "lesson_number": lesson_num,
                            "category": category,
                            "text": text,
                            "braille": braille,
                            "context": {
                                "subject": subject,
                                "year": 2026,
                                "difficulty": "고3_기본",
                                "topic": category
                            },
                            "metadata": {
                                "char_count": len(text),
                                "braille_cell_count": len(braille.split()) if braille else 0,
                                "extracted_at": datetime.now().isoformat()
                            }
                        })
                        print(f"    ✅ 완료 ({len(text)} 문자)")
                    except Exception as e:
                        print(f"    ❌ 에러 발생: {e}")
                        continue
        else:
            # 루트에 직접 파일이 있는 경우 (레거시 지원)
            for hwp_file in hwp_dir.glob("*.hwp"):
                print(f"Processing HWP: {hwp_file.name}")
                text = extract_text_from_hwp(hwp_file)
                if not text:
                    continue
                
                structure = extract_structure_from_hwp(hwp_file)
                braille = text_to_braille(text)
                
                lesson_num = extract_lesson_number(hwp_file.name)
                category = extract_category(hwp_file.name)
                
                dataset["items"].append({
                    "id": f"item_{len(dataset['items']):03d}",
                    "source": "hwp",
                    "source_file": hwp_file.name,
                    "lesson_number": lesson_num,
                    "category": category,
                    "text": text,
                    "braille": braille,
                    "context": {
                        "subject": extract_subject_from_filename(hwp_file.name),
                        "year": 2026,
                        "difficulty": "고3_기본",
                        "topic": category
                    },
                    "metadata": {
                        "char_count": len(text),
                        "braille_cell_count": len(braille.split()) if braille else 0,
                        "extracted_at": datetime.now().isoformat()
                    }
                })
    
    # PDF 파일 처리
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        total_pdfs = len(pdf_files)
        print(f"\nProcessing {total_pdfs} PDF files...")
        
        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"  [{idx}/{total_pdfs}] Processing PDF: {pdf_file.name} ({(pdf_file.stat().st_size / (1024*1024)):.2f} MB)")
            try:
                text = extract_text_from_pdf(pdf_file)
                if not text:
                    print(f"    ⚠️  텍스트 추출 실패 또는 빈 파일")
                    continue
                
                print(f"    ✓ 텍스트 추출 완료 ({len(text)} 문자)")
                braille = text_to_braille(text)
                print(f"    ✓ 점자 변환 완료")
                
                dataset["items"].append({
                    "id": f"item_{len(dataset['items']):03d}",
                    "source": "pdf",
                    "source_file": pdf_file.name,
                    "text": text,
                    "braille": braille,
                    "context": {
                        "subject": extract_subject_from_filename(pdf_file.name),
                        "year": 2026
                    },
                    "metadata": {
                        "char_count": len(text),
                        "braille_cell_count": len(braille.split()) if braille else 0,
                        "extracted_at": datetime.now().isoformat()
                    }
                })
                print(f"    ✅ 완료")
            except Exception as e:
                print(f"    ❌ 에러 발생: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # JSON으로 저장
    print(f"\n{'='*60}")
    print(f"데이터셋 구축 완료!")
    print(f"  - 총 항목 수: {len(dataset['items'])}")
    print(f"  - 저장 경로: {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  - 파일 저장 중...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    file_size = output_path.stat().st_size / (1024*1024)
    print(f"  - 파일 크기: {file_size:.2f} MB")
    print(f"{'='*60}")
    
    return dataset


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="점자 변환 학습 데이터셋 구축")
    parser.add_argument("--hwp-dir", type=Path, help="한글 파일 디렉토리")
    parser.add_argument("--pdf-dir", type=Path, help="PDF 파일 디렉토리")
    parser.add_argument("--output", type=Path, help="출력 파일 경로")
    
    args = parser.parse_args()
    
    build_braille_dataset(
        hwp_dir=args.hwp_dir,
        pdf_dir=args.pdf_dir,
        output_path=args.output
    )
