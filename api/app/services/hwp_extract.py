"""
한글 파일 텍스트 추출 서비스
"""
import re
from pathlib import Path
from typing import Optional, Dict, List

try:
    import olefile
    HAS_OLEFILE = True
except ImportError:
    HAS_OLEFILE = False
    try:
        import pyhwp
        HAS_PYHWP = True
    except ImportError:
        HAS_PYHWP = False


def extract_text_from_hwp(hwp_path: Path) -> Optional[str]:
    """한글 파일에서 텍스트 추출"""
    if not hwp_path.exists():
        return None
    
    try:
        if HAS_OLEFILE:
            # olefile을 사용한 기본 텍스트 추출
            # Path 객체를 문자열로 변환
            hwp_path_str = str(hwp_path)
            
            # HWP 파일인지 확인
            if not olefile.isOleFile(hwp_path_str):
                print(f"[hwp_extract] 파일이 OLE 형식이 아닙니다: {hwp_path}")
                return None
            
            with olefile.OleFileIO(hwp_path_str) as ole:
                # HWP 파일 구조에서 텍스트 추출
                text = ""
                
                # 여러 스트림 시도
                stream_names = ['BodyText', 'Section0', 'PrvText', 'DocInfo']
                
                for stream_name in stream_names:
                    try:
                        if ole.exists(stream_name):
                            stream = ole.openstream(stream_name)
                            data = stream.read()
                            
                            # UTF-16, UTF-8, CP949 등 여러 인코딩 시도
                            for encoding in ['utf-16-le', 'utf-16-be', 'utf-8', 'cp949', 'euc-kr']:
                                try:
                                    decoded = data.decode(encoding, errors='ignore')
                                    # 인쇄 가능한 문자만 필터링
                                    printable = ''.join(c for c in decoded if c.isprintable() or c.isspace())
                                    if len(printable) > 100:  # 의미있는 텍스트가 있는지 확인
                                        text += printable + "\n"
                                        break
                                except (UnicodeDecodeError, UnicodeError):
                                    continue
                    except Exception as e:
                        continue
                
                # 모든 스트림에서 텍스트 추출 시도
                if not text:
                    try:
                        for stream_name in ole.listdir():
                            if isinstance(stream_name, tuple):
                                stream_name = '/'.join(stream_name)
                            try:
                                if ole.exists(stream_name):
                                    stream = ole.openstream(stream_name)
                                    data = stream.read()
                                    # 작은 스트림만 시도 (너무 크면 건너뛰기)
                                    if len(data) < 100000:  # 100KB 이하만
                                        for encoding in ['utf-16-le', 'utf-8', 'cp949']:
                                            try:
                                                decoded = data.decode(encoding, errors='ignore')
                                                printable = ''.join(c for c in decoded if c.isprintable() or c.isspace())
                                                if len(printable) > 50:
                                                    text += printable + "\n"
                                                    break
                                            except:
                                                continue
                            except:
                                continue
                    except:
                        pass
                
                return text.strip() if text.strip() else None
        elif HAS_PYHWP:
            # pyhwp 사용
            from pyhwp import hwp5
            doc = hwp5.open(hwp_path)
            text = ""
            for section in doc.body.sections:
                for paragraph in section.paragraphs:
                    for char in paragraph.chars:
                        if hasattr(char, 'text'):
                            text += char.text
            return text if text else None
        else:
            print("[hwp_extract] 한글 파일 파싱 라이브러리가 설치되지 않았습니다. pyhwp 또는 olefile을 설치해주세요.")
            return None
    except Exception as e:
        print(f"[hwp_extract] Error extracting text from HWP: {e}")
        return None


def extract_lesson_info_from_filename(filename: str) -> Dict:
    """파일명에서 강의 정보 추출
    
    예: "01강_[교과서_개념]_1_2_(고3_기본).hwp"
    -> {
        "lesson_number": 1,
        "category": "교과서_개념",
        "subcategory": "1_2",
        "difficulty": "고3_기본"
    }
    """
    # 파일명에서 확장자 제거
    filename_no_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # 패턴: "01강_[교과서_개념]_1_2_(고3_기본)"
    pattern = r'(\d+)강_\[([^\]]+)\]_([^_]+(?:_[^_]+)*)_\(([^)]+)\)'
    match = re.match(pattern, filename_no_ext)
    if match:
        return {
            "lesson_number": int(match.group(1)),
            "category": match.group(2),
            "subcategory": match.group(3),
            "difficulty": match.group(4)
        }
    return {}


def extract_structure_from_hwp(hwp_path: Path) -> Dict:
    """한글 파일에서 강 구조 추출
    
    구조:
    - 개념 설명
    - 꼭 집어 핵심 포인트
    - 문제 1번, 2번, 3번
    - 기출 탈탈 털어 쏙쏙 뽑아
    """
    text = extract_text_from_hwp(hwp_path)
    if not text:
        return {}
    
    structure = {
        "concept_explanations": [],
        "key_points": [],
        "problems": [],
        "practice_section": ""
    }
    
    # 패턴 매칭으로 구조 추출
    # "개념 설명" 섹션 찾기
    concept_pattern = r'개념\s*설명[:\-]?\s*(.+?)(?=꼭|문제|기출|$)'
    concept_matches = re.finditer(concept_pattern, text, re.DOTALL)
    for match in concept_matches:
        structure["concept_explanations"].append(match.group(1).strip())
    
    # "꼭 집어 핵심 포인트" 섹션 찾기
    keypoint_pattern = r'꼭\s*집어\s*핵심\s*포인트[:\-]?\s*(.+?)(?=문제|기출|$)'
    keypoint_matches = re.finditer(keypoint_pattern, text, re.DOTALL)
    for match in keypoint_matches:
        structure["key_points"].append(match.group(1).strip())
    
    # "문제 N번" 찾기
    problem_pattern = r'문제\s*(\d+)\s*번[:\-]?\s*(.+?)(?=문제\s*\d+|기출|$)'
    problem_matches = re.finditer(problem_pattern, text, re.DOTALL)
    for match in problem_matches:
        structure["problems"].append({
            "number": int(match.group(1)),
            "content": match.group(2).strip()
        })
    
    # "기출 탈탈 털어 쏙쏙 뽑아" 섹션 찾기
    practice_pattern = r'기출\s*탈탈\s*털어\s*쏙쏙\s*뽑아[:\-]?\s*(.+?)(?=한\s*판에|$)'
    practice_match = re.search(practice_pattern, text, re.DOTALL)
    if practice_match:
        structure["practice_section"] = practice_match.group(1).strip()
    
    return structure
