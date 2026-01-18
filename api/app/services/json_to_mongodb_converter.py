"""
기존 JSON 데이터를 MongoDB 레슨 문서 형식으로 변환
"""
from typing import Dict, Any, List
from datetime import datetime
from app.db.mongodb_models import (
    BlockType, LessonBlock, LearningIntent, AudioRange,
    UserAwareness, UIBehavior, Lesson, LessonMetadata
)


def map_unit_type_to_block_type(unit_type: str) -> BlockType:
    """Unit type을 Block type으로 매핑"""
    mapping = {
        'intro': BlockType.ORIENTATION,
        'concept': BlockType.APPRECIATION_FRAME,
        'definition': BlockType.LEARNING_GOAL,
        'example': BlockType.WORK_ANALYSIS,
        'notation': BlockType.LEARNING_GOAL,
        'problem_intro': BlockType.PROBLEM_APPLICATION,
        'summary': BlockType.SUMMARY,
        'outro': BlockType.CLOSING_MESSAGE,
    }
    return mapping.get(unit_type, BlockType.ORIENTATION)


def get_braille_signal(block_type: BlockType) -> str:
    """블록 타입에 따른 점자 패턴"""
    signals = {
        BlockType.ORIENTATION: "●○○",
        BlockType.LEARNING_GOAL: "●●○",
        BlockType.EXAM_STRUCTURE: "●●●",
        BlockType.APPRECIATION_FRAME: "○●○",
        BlockType.WORK_ANALYSIS: "○●●",
        BlockType.PROBLEM_APPLICATION: "○○●",
        BlockType.SUMMARY: "●○●",
        BlockType.CLOSING_MESSAGE: "○○○",
    }
    return signals.get(block_type, "●○○")


def get_awareness_message(block_type: BlockType, section_title: str) -> str:
    """블록 타입에 따른 사용자 인지 메시지"""
    messages = {
        BlockType.ORIENTATION: "강의가 시작되었습니다",
        BlockType.LEARNING_GOAL: "학습 목표를 확인합니다",
        BlockType.EXAM_STRUCTURE: "시험 출제 구조를 학습합니다",
        BlockType.APPRECIATION_FRAME: "감상 프레임을 학습합니다",
        BlockType.WORK_ANALYSIS: "작품 분석을 시작합니다",
        BlockType.PROBLEM_APPLICATION: "문제 풀이를 시작합니다",
        BlockType.SUMMARY: "강의 요약을 확인합니다",
        BlockType.CLOSING_MESSAGE: "강의가 종료되었습니다",
    }
    return messages.get(block_type, "학습을 계속합니다")


def convert_lesson_json_to_mongodb(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 JSON 구조를 MongoDB 레슨 문서로 변환
    
    Args:
        json_data: 기존 parsed JSON 데이터
        
    Returns:
        MongoDB 레슨 문서 형식
    """
    blocks = []
    block_order = 1
    
    # 섹션과 유닛을 블록으로 변환
    for section in json_data.get('sections', []):
        section_title = section.get('title', '')
        
        for unit in section.get('units', []):
            unit_type = unit.get('type', 'intro')
            block_type = map_unit_type_to_block_type(unit_type)
            
            # 블록 생성
            block = {
                "blockId": unit.get('unitId', f"{json_data.get('lessonId')}_b{block_order:03d}"),
                "type": block_type.value,
                "order": block_order,
                "learningIntent": {
                    "title": section_title or _extract_title_from_content(unit.get('content', '')),
                    "description": _extract_description(unit.get('content', ''))
                },
                "brailleSignal": get_braille_signal(block_type),
                "audioRange": {
                    "start": "00:00:00",  # 실제 타임스탬프는 별도 처리 필요
                    "end": "00:00:00"
                },
                "userAwareness": {
                    "message": get_awareness_message(block_type, section_title),
                    "context": section_title
                },
                "uiBehavior": {
                    "autoPlay": unit_type != 'problem_intro',
                    "bookmarkable": True,
                    "reviewable": True,
                    "problemMode": unit_type == 'problem_intro'
                },
                "content": _build_block_content(block_type, unit, section_title)
            }
            
            blocks.append(block)
            block_order += 1
    
    # 레슨 문서 생성
    lesson_doc = {
        "lessonId": json_data.get('lessonId', ''),
        "subject": json_data.get('subject', 'korean'),
        "title": json_data.get('title', ''),
        "order": json_data.get('order', 1),
        "metadata": {
            "year": 2026,
            "curriculum": "수능특강",
            "estimatedDuration": _estimate_duration(blocks),  # 블록 수 기반 추정
            "difficulty": "basic"
        },
        "blocks": blocks,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    return lesson_doc


def _extract_title_from_content(content: str) -> str:
    """내용에서 제목 추출 시도"""
    if not content:
        return ""
    
    # 첫 문장이나 첫 50자를 제목으로 사용
    first_sentence = content.split('.')[0].strip()
    if len(first_sentence) > 50:
        return first_sentence[:50] + "..."
    return first_sentence


def _extract_description(content: str) -> str:
    """내용에서 설명 추출"""
    if not content:
        return ""
    
    # 첫 100자를 설명으로 사용
    if len(content) > 100:
        return content[:100] + "..."
    return content


def _build_block_content(block_type: BlockType, unit: Dict[str, Any], section_title: str) -> Dict[str, Any]:
    """블록 타입에 따른 content 구조 생성"""
    base_content = {
        "script": unit.get('content', '')
    }
    
    if block_type == BlockType.ORIENTATION:
        return {
            **base_content,
            "keyPoints": unit.get('key_points', [])
        }
    
    elif block_type == BlockType.LEARNING_GOAL:
        # 내용에서 목표 추출 시도
        goals = []
        content = unit.get('content', '')
        if '목표' in content or '배울' in content:
            # 간단한 추출 로직
            sentences = content.split('.')
            for sentence in sentences[:3]:
                if any(keyword in sentence for keyword in ['목표', '배울', '이해', '파악']):
                    goals.append(sentence.strip())
        
        return {
            **base_content,
            "goals": goals if goals else [section_title]
        }
    
    elif block_type == BlockType.PROBLEM_APPLICATION:
        # 문제 번호 추출 시도
        problem_number = 1
        content = unit.get('content', '')
        import re
        match = re.search(r'(\d+)\s*번', content)
        if match:
            problem_number = int(match.group(1))
        
        return {
            **base_content,
            "problemNumber": problem_number,
            "question": _extract_question(content),
            "choices": _extract_choices(content),
            "correctAnswer": 0,  # 실제 정답은 별도 처리 필요
            "explanation": content,
            "thinkingProcess": []
        }
    
    elif block_type == BlockType.SUMMARY:
        return {
            **base_content,
            "keyPoints": unit.get('key_points', []),
            "connections": []
        }
    
    else:
        return base_content


def _extract_question(content: str) -> str:
    """내용에서 문제 추출"""
    # "문제" 다음 문장을 문제로 간주
    import re
    match = re.search(r'문제[^.]*\.\s*([^.]{10,200})', content)
    if match:
        return match.group(1).strip()
    return content[:200] if len(content) > 200 else content


def _extract_choices(content: str) -> List[str]:
    """내용에서 선지 추출"""
    # ①②③④⑤ 패턴 찾기
    import re
    choices = []
    pattern = r'[①②③④⑤]\s*([^①②③④⑤]{10,200})'
    matches = re.finditer(pattern, content)
    for match in matches:
        choices.append(match.group(1).strip())
    return choices if choices else []


def _estimate_duration(blocks: List[Dict[str, Any]]) -> int:
    """블록 수를 기반으로 예상 시간 추정 (초 단위)"""
    # 블록당 평균 5분 가정
    base_time = len(blocks) * 300
    
    # 문제 블록은 추가 시간
    problem_blocks = sum(1 for b in blocks if b.get('type') == BlockType.PROBLEM_APPLICATION.value)
    base_time += problem_blocks * 300
    
    return base_time
