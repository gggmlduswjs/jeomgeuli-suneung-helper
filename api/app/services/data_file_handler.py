"""
데이터 파일 읽기/쓰기 유틸리티
api/data 디렉토리의 JSON 파일들을 읽고 쓰는 기능을 중앙화
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.config import settings
from app.services.script_editor import ScriptEditor


# 데이터 디렉토리 경로 (모든 JSON 파일을 하나의 폴더에)
DATA_DIR = settings.API_DIR / "data"


def ensure_data_dir():
    """데이터 디렉토리 생성"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# 디렉토리 생성
ensure_data_dir()


# ==================== 읽기 함수 ====================

def load_unit_structure(subject: str, lesson_number: int = 1) -> Optional[List[Dict[str, Any]]]:
    """
    단위 구조 JSON 파일 읽기
    
    Args:
        subject: 과목명 (korean, math, english 등)
        lesson_number: 강 번호 (기본값: 1)
    
    Returns:
        단위 구조 리스트 또는 None
    """
    filename = f"{subject}_{lesson_number}_unit_structure.json"
    filepath = DATA_DIR / filename
    
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] 단위 구조 파일 읽기 실패: {filepath} - {e}")
        return None


def load_lecture_script_json(subject: str, lesson_number: int = 1) -> Optional[Dict[str, Any]]:
    """
    강의 대본 JSON 파일 읽기
    
    Args:
        subject: 과목명 (korean, math, english 등)
        lesson_number: 강 번호 (기본값: 1)
    
    Returns:
        강의 대본 JSON 또는 None
    """
    filename = f"{subject}_{lesson_number}_script.json"
    filepath = DATA_DIR / filename
    
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] 강의 대본 JSON 파일 읽기 실패: {filepath} - {e}")
        return None


def load_block_json(subject: str, lesson_number: int = 1) -> Optional[Dict[str, Any]]:
    """
    블록 JSON 파일 읽기
    
    Args:
        subject: 과목명 (korean, math, english 등)
        lesson_number: 강 번호 (기본값: 1)
    
    Returns:
        블록 JSON 또는 None
    """
    filename = f"{subject}_{lesson_number}_blocks.json"
    filepath = DATA_DIR / filename
    
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] 블록 JSON 파일 읽기 실패: {filepath} - {e}")
        return None


def load_unit_regions(subject: str, lesson_number: int = 1) -> Optional[List[Dict[str, Any]]]:
    """
    단위 영역 JSON 파일 읽기
    
    Args:
        subject: 과목명 (korean, math, english 등)
        lesson_number: 강 번호 (기본값: 1)
    
    Returns:
        단위 영역 리스트 또는 None
    """
    filename = f"{subject}_{lesson_number}_regions.json"
    filepath = DATA_DIR / filename
    
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] 단위 영역 파일 읽기 실패: {filepath} - {e}")
        return None


def load_json_file(filepath: Path) -> Optional[Any]:
    """
    일반 JSON 파일 읽기
    
    Args:
        filepath: JSON 파일 경로
    
    Returns:
        JSON 데이터 또는 None
    """
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] JSON 파일 읽기 실패: {filepath} - {e}")
        return None


# ==================== 쓰기 함수 ====================

def save_unit_structure(subject: str, lesson_number: int, data: List[Dict[str, Any]]) -> bool:
    """
    단위 구조 JSON 파일 저장
    
    Args:
        subject: 과목명
        lesson_number: 강 번호
        data: 단위 구조 리스트
    
    Returns:
        성공 여부
    """
    filename = f"{subject}_{lesson_number}_unit_structure.json"
    filepath = DATA_DIR / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] 단위 구조 저장: {filepath}")
        return True
    except Exception as e:
        print(f"[ERROR] 단위 구조 저장 실패: {filepath} - {e}")
        return False


def save_lecture_script_json(
    subject: str, 
    lesson_number: int, 
    data: Dict[str, Any],
    auto_edit: bool = True,
    use_ai: bool = True
) -> bool:
    """
    강의 대본 JSON 파일 저장
    
    Args:
        subject: 과목명
        lesson_number: 강 번호
        data: 강의 대본 JSON 데이터
        auto_edit: 자동 편집 여부 (기본값: True)
        use_ai: AI 기반 편집 사용 여부 (기본값: True, API 키가 없으면 자동으로 False)
    
    Returns:
        성공 여부
    """
    filename = f"{subject}_{lesson_number}_script.json"
    filepath = DATA_DIR / filename
    
    try:
        # 자동 편집 옵션이 켜져 있으면 편집
        if auto_edit:
            editor = ScriptEditor(use_ai=use_ai)
            data = editor.edit_script_json(data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] 강의 대본 JSON 저장: {filepath}")
        return True
    except Exception as e:
        print(f"[ERROR] 강의 대본 JSON 저장 실패: {filepath} - {e}")
        return False


def save_block_json(
    subject: str, 
    lesson_number: int, 
    data: Dict[str, Any],
    auto_edit: bool = True,
    use_ai: bool = True
) -> bool:
    """
    블록 JSON 파일 저장
    
    Args:
        subject: 과목명
        lesson_number: 강 번호
        data: 블록 JSON 데이터
        auto_edit: 자동 편집 여부 (기본값: True)
        use_ai: AI 기반 편집 사용 여부 (기본값: True, API 키가 없으면 자동으로 False)
    
    Returns:
        성공 여부
    """
    filename = f"{subject}_{lesson_number}_blocks.json"
    filepath = DATA_DIR / filename
    
    try:
        # 자동 편집 옵션이 켜져 있으면 편집
        if auto_edit:
            editor = ScriptEditor(use_ai=use_ai)
            data = editor.edit_blocks_json(data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] 블록 JSON 저장: {filepath}")
        return True
    except Exception as e:
        print(f"[ERROR] 블록 JSON 저장 실패: {filepath} - {e}")
        return False


def save_unit_regions(subject: str, lesson_number: int, data: List[Dict[str, Any]]) -> bool:
    """
    단위 영역 JSON 파일 저장
    
    Args:
        subject: 과목명
        lesson_number: 강 번호
        data: 단위 영역 리스트
    
    Returns:
        성공 여부
    """
    filename = f"{subject}_{lesson_number}_regions.json"
    filepath = DATA_DIR / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] 단위 영역 저장: {filepath}")
        return True
    except Exception as e:
        print(f"[ERROR] 단위 영역 저장 실패: {filepath} - {e}")
        return False


def save_json_file(filepath: Path, data: Any) -> bool:
    """
    일반 JSON 파일 저장
    
    Args:
        filepath: JSON 파일 경로
        data: 저장할 데이터
    
    Returns:
        성공 여부
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] JSON 파일 저장: {filepath}")
        return True
    except Exception as e:
        print(f"[ERROR] JSON 파일 저장 실패: {filepath} - {e}")
        return False


def save_curriculum_json(curriculum_id: str, curriculum_data: Dict[str, Any], subject: Optional[str] = None) -> bool:
    """
    커리큘럼 JSON 파일 저장 (data/curricula/ 폴더)
    
    Args:
        curriculum_id: 커리큘럼 ID
        curriculum_data: 커리큘럼 데이터
        subject: 과목명 (선택)
    
    Returns:
        성공 여부
    """
    # 과목별 폴더명 매핑
    subject_map = {
        'korean': 'korean',
        'literature': 'korean',  # 문학도 korean 폴더에
        'math': 'math1',
        'math1': 'math1',
        'english': 'english',
    }
    
    # 과목명 결정
    subject_name = subject or curriculum_data.get('subject', 'general')
    subject_name = subject_name.lower()
    folder_name = subject_map.get(subject_name, 'general')
    
    # 저장 디렉토리 생성 (과목별 폴더)
    json_dir = settings.DATA_DIR / "curricula" / folder_name
    json_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON 파일 경로
    json_path = json_dir / f"{curriculum_id}.json"
    
    # 저장할 데이터 구조
    json_data = {
        "curriculum_id": curriculum_id,
        "subject": curriculum_data.get('subject'),
        "total_lessons": curriculum_data.get('total_lessons', 0),
        "total_units": curriculum_data.get('total_units', 0),
        "created_at": datetime.utcnow().isoformat(),
        "lessons": []
    }
    
    # 레슨별 데이터 구조화
    for lesson_data in curriculum_data.get('lessons', []):
        lesson_json = {
            "lesson_number": lesson_data.get('lesson_number', 0),
            "title": lesson_data.get('title', ''),
            "sections": lesson_data.get('sections', []),
            "pdf_references": lesson_data.get('pdf_references', []),
            "dependencies": lesson_data.get('dependencies', []),
            "estimated_time": lesson_data.get('estimated_time', 0),
            "learning_units": []
        }
        
        # 학습 단위 데이터
        for unit_data in lesson_data.get('learning_units', []):
            unit_json = {
                "unit_index": unit_data.get('unit_index', 0),
                "section_type": unit_data.get('section_type', 'general'),
                "section_name": unit_data.get('section_name', unit_data.get('section_type', 'general')),
                "content": unit_data.get('content', ''),
                "key_points": unit_data.get('key_points', []),
                "pdf_references": unit_data.get('pdf_references', []),
                "break_points": unit_data.get('break_points', [])
            }
            lesson_json["learning_units"].append(unit_json)
        
        json_data["lessons"].append(lesson_json)
    
    # 학습 경로 및 연결 정보
    json_data["learning_path"] = curriculum_data.get('learning_path', [])
    json_data["connections"] = curriculum_data.get('connections', [])
    
    # 학습 흐름 정보 (이미 생성되어 있으면 사용)
    if 'learning_flow' in curriculum_data:
        json_data["learning_flow"] = curriculum_data['learning_flow']
    
    # JSON 파일로 저장
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"[Curriculum] JSON saved to: {json_path}")
        return True
    except Exception as e:
        print(f"[ERROR] 커리큘럼 JSON 저장 실패: {json_path} - {e}")
        return False
