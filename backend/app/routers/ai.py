"""
AI 강의 선생님 API
문학 및 일반 AI 기능 통합
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import os

from app.db.session import get_db
from app.db.models import Lesson, Unit, UnitType

# OpenAI API 사용
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ML 기반 유사도 계산 서비스 (선택적)
try:
    from app.utils.ml_content_similarity import get_similarity_service, get_keyword_extractor
    ML_AVAILABLE = True
except (ImportError, Exception) as e:
    # torch/sentence_transformers 관련 에러도 무시 (선택적 의존성)
    ML_AVAILABLE = False
    def get_similarity_service():
        return None
    def get_keyword_extractor():
        return None

# AILectureTeacher (삭제된 모듈 대체용)
try:
    from app.services.ai_lecture_teacher import AILectureTeacher
except ImportError:
    class AILectureTeacher:
        def __init__(self, lecture_script: str = "", subject: str = "literature"):
            self.lecture_script = lecture_script
            self.subject = subject
        
        async def teach_unit(self, unit_content: str, unit_type: str) -> str:
            raise HTTPException(status_code=501, detail="AI 강의가 지원되지 않습니다.")
        
        async def answer_question(self, question: str, unit_content: str = "") -> str:
            raise HTTPException(status_code=501, detail="AI 질문 답변이 지원되지 않습니다.")
        
        async def teach_sequentially(self) -> dict:
            raise HTTPException(status_code=501, detail="AI 순차 수업이 지원되지 않습니다.")
        
        async def get_next_topic(self, current_position: int = 0) -> dict:
            raise HTTPException(status_code=501, detail="AI 다음 주제가 지원되지 않습니다.")

router = APIRouter()


def get_openai_client():
    """OpenAI 클라이언트 생성"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")
    return openai.OpenAI(api_key=api_key)


@router.post("/ai/teach/unit/{unit_id}")
async def ai_teach_unit(
    unit_id: str,
    db: Session = Depends(get_db)
):
    """
    Unit 내용을 AI가 강의 대본 기반으로 설명

    Args:
        unit_id: Unit ID

    Returns:
        AI 설명 텍스트
    """
    unit = db.query(Unit).filter(Unit.unit_id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="학습 단위를 찾을 수 없습니다.")

    # 1순위: Unit에 저장된 AI 설명 사용
    if unit.ai_explanation:
        return {
            "unit_id": unit_id,
            "explanation": unit.ai_explanation,
            "unit_type": unit.type.value,
            "source": "stored"
        }

    # 2순위: 레슨의 강의 대본 기반 LLM 호출
    lesson = db.query(Lesson).filter(Lesson.lesson_id == unit.lesson_id).first()
    subject = lesson.book.subject.value.lower() if lesson and lesson.book else 'literature'
    
    # Unit 타입에 따라 설명
    unit_content = unit.content_text or unit.question_stem or unit.title or ''
    
    # 강의 대본이 있으면 사용, 없으면 Unit 내용만으로 설명 생성 시도
    if lesson and hasattr(lesson, 'lecture_script_text') and lesson.lecture_script_text:
        # 강의 대본 기반 설명 생성
        try:
            teacher = AILectureTeacher(
                lecture_script=lesson.lecture_script_text,
                subject=subject
            )
            
            explanation = await teacher.teach_unit(
                unit_content=unit_content,
                unit_type=unit.type.value,
                unit_title=unit.title
            )

            return {
                "unit_id": unit_id,
                "explanation": explanation,
                "unit_type": unit.type.value,
                "source": "llm_lecture"
            }
        except Exception as e:
            print(f"[ai] 강의 대본 기반 설명 생성 실패: {e}")
            # 실패하면 Unit 내용만으로 시도
    
    # 3순위: 강의 대본 없이 Unit 내용만으로 설명 생성 시도
    if unit_content and OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Unit 타입에 따른 프롬프트
            if unit.type == UnitType.QUESTION:
                prompt = f"""다음 문제를 학생에게 설명해주세요. 이해하기 쉽고 친절하게 설명해주세요.

문제: {unit.title}
내용: {unit_content}

설명:"""
            else:
                prompt = f"""다음 학습 내용을 학생에게 설명해주세요. 핵심 개념을 명확하게 설명해주세요.

제목: {unit.title}
내용: {unit_content}

설명:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 친절하고 이해하기 쉬운 설명을 제공하는 선생님입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            explanation = response.choices[0].message.content.strip()
            
            return {
                "unit_id": unit_id,
                "explanation": explanation,
                "unit_type": unit.type.value,
                "source": "llm_direct"
            }
        except Exception as e:
            print(f"[ai] Unit 내용 기반 설명 생성 실패: {e}")
    
    # 최종: 기본 설명 반환 (더 유용한 메시지)
    if unit_content:
        return {
            "unit_id": unit_id,
            "explanation": f"{unit.title}에 대한 설명입니다. {unit_content[:100]}...",
            "unit_type": unit.type.value,
            "source": "content_fallback"
        }
    else:
        return {
            "unit_id": unit_id,
            "explanation": "이 학습 단위에 대한 상세한 설명이 준비되지 않았습니다. 강의 대본이나 AI 설명 기능을 활성화하면 더 자세한 설명을 제공할 수 있습니다.",
            "unit_type": unit.type.value,
            "source": "default"
        }


@router.post("/ai/answer")
async def ai_answer_question(
    question: str = Body(..., embed=True),
    unit_id: Optional[str] = Body(None, embed=True),
    lesson_id: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """
    사용자 질문에 AI가 강의 대본 기반으로 답변
    강의 대본이 없으면 Unit 내용만으로 답변 시도
    
    Args:
        question: 사용자 질문
        unit_id: 현재 Unit ID (선택)
        lesson_id: 현재 Lesson ID (선택)
        
    Returns:
        AI 답변 텍스트
    """
    # 강의 대본 가져오기
    lecture_script = ""
    subject = "literature"
    unit_content = None
    unit_title = None
    
    if unit_id:
        unit = db.query(Unit).filter(Unit.unit_id == unit_id).first()
        if unit:
            unit_content = unit.content_text or unit.question_stem or unit.title or ''
            unit_title = unit.title
            lesson = db.query(Lesson).filter(Lesson.lesson_id == unit.lesson_id).first()
            if lesson:
                if lesson.lecture_script_text:
                    lecture_script = lesson.lecture_script_text
                subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    elif lesson_id:
        lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
        if lesson:
            if lesson.lecture_script_text:
                lecture_script = lesson.lecture_script_text
            subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    
    # 1순위: 강의 대본이 있으면 강의 대본 기반으로 답변
    if lecture_script:
        try:
            teacher = AILectureTeacher(
                lecture_script=lecture_script,
                subject=subject
            )
            
            answer = await teacher.answer_question(
                question=question,
                unit_content=unit_content
            )
            
            return {
                "question": question,
                "answer": answer
            }
        except Exception as e:
            print(f"[ai] 강의 대본 기반 답변 생성 실패: {e}")
            # 실패하면 fallback으로 진행
    
    # 2순위: 강의 대본이 없거나 실패한 경우, Unit 내용만으로 답변
    if unit_content and OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Unit 내용을 컨텍스트로 사용
            context_text = f"학습 내용:\n제목: {unit_title}\n내용: {unit_content[:1000]}" if unit_title and unit_content else ""
            
            prompt = f"""학생이 다음 질문을 했습니다. 학습 내용을 바탕으로 친절하고 이해하기 쉽게 답변해주세요.

{context_text}

질문: {question}

답변:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 친절하고 이해하기 쉬운 설명을 제공하는 선생님입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                "question": question,
                "answer": answer
            }
        except Exception as e:
            print(f"[ai] Unit 내용 기반 답변 생성 실패: {e}")
    
    # 3순위: 컨텍스트 없이 일반적인 답변
    if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
        try:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""학생이 다음 질문을 했습니다. 친절하고 이해하기 쉽게 답변해주세요.

질문: {question}

답변:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 친절하고 이해하기 쉬운 설명을 제공하는 선생님입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                "question": question,
                "answer": answer
            }
        except Exception as e:
            print(f"[ai] 일반 답변 생성 실패: {e}")
    
    # 최종 fallback: 기본 메시지
    return {
        "question": question,
        "answer": "죄송합니다. 현재 AI 답변 기능을 사용할 수 없습니다. OpenAI API 키가 설정되어 있는지 확인해주세요."
    }


@router.post("/ai/teach/{lesson_id}")
async def ai_teach_lesson(
    lesson_id: str,
    mode: str = "sequential",  # "sequential" or "interactive"
    question: Optional[str] = Body(None, embed=True),  # 대화형 모드일 때
    db: Session = Depends(get_db)
):
    """
    AI가 강의 대본을 기반으로 수업 진행
    
    Args:
        lesson_id: 레슨 ID
        mode: "sequential" (순차적) 또는 "interactive" (대화형)
        question: 대화형 모드일 때 사용자 질문
        
    Returns:
        AI 수업 응답
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="레슨을 찾을 수 없습니다.")
    
    if not lesson.lecture_script_text:
        raise HTTPException(status_code=400, detail="강의 대본이 없습니다.")
    
    # AI 강의 선생님 초기화
    subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    teacher = AILectureTeacher(
        lecture_script=lesson.lecture_script_text,
        subject=subject
    )
    
    try:
        if mode == "sequential":
            # 순차적 수업 진행
            response = await teacher.teach_sequentially()
        else:
            # 대화형 수업 (질문 기반)
            if not question:
                raise HTTPException(status_code=400, detail="질문이 필요합니다.")
            response = await teacher.answer_question(question)
        
        return {
            "lesson_id": lesson_id,
            "response": response,
            "mode": mode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 수업 진행 실패: {str(e)}")


@router.post("/ai/teach/{lesson_id}/next")
async def ai_get_next_topic(
    lesson_id: str,
    position: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    강의 대본에서 다음 주제 가져오기
    
    Args:
        lesson_id: 레슨 ID
        position: 현재 위치 (청크 인덱스)
        
    Returns:
        다음 주제 설명
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="레슨을 찾을 수 없습니다.")
    
    if not lesson.lecture_script_text:
        raise HTTPException(status_code=400, detail="강의 대본이 없습니다.")
    
    # AI 강의 선생님 초기화
    subject = lesson.book.subject.value.lower() if lesson.book else 'literature'
    teacher = AILectureTeacher(
        lecture_script=lesson.lecture_script_text,
        subject=subject
    )
    
    try:
        response = await teacher.get_next_topic(current_position=position)
        
        return {
            "lesson_id": lesson_id,
            "position": position,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다음 주제 가져오기 실패: {str(e)}")


# ============================================================================
# 문학 AI 기능 (literature_ai.py에서 통합)
# ============================================================================

@router.post("/literature/ai/explain-concept")
async def explain_concept(
    concept_title: str = Body(..., embed=True),
    concept_content: list = Body(..., embed=True),
    subject: str = Body("literature", embed=True)
) -> Dict[str, Any]:
    """
    개념 설명을 AI가 깔끔하게 정리
    
    Args:
        concept_title: 개념 제목
        concept_content: 개념 내용 (리스트)
        subject: 과목 (기본값: literature)
    
    Returns:
        정리된 개념 설명
    """
    if not OPENAI_AVAILABLE:
        raise HTTPException(status_code=501, detail="OpenAI가 설치되지 않았습니다.")
    
    try:
        client = get_openai_client()
        
        # 개념 내용 합치기
        content_text = "\n".join(concept_content)
        
        prompt = f"""다음 문학 개념을 학생이 이해하기 쉽게 깔끔하게 정리해주세요.

제목: {concept_title}

내용:
{content_text}

요구사항:
1. 핵심 내용을 명확하게 설명
2. 예시를 들어서 이해하기 쉽게
3. 간결하고 깔끔하게 (200자 이내)
4. 학생이 직접 읽을 수 있도록 자연스러운 말투

정리된 설명:"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 문학 교사입니다. 학생이 이해하기 쉽게 개념을 설명해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        explanation = response.choices[0].message.content.strip()
        
        return {
            "concept_title": concept_title,
            "original_content": concept_content,
            "ai_explanation": explanation,
            "subject": subject
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 설명 생성 실패: {str(e)}")


@router.post("/literature/ai/explain-content")
async def explain_content(
    content_title: str = Body(..., embed=True),
    content_text: list = Body(..., embed=True),
    subject: str = Body("literature", embed=True)
) -> Dict[str, Any]:
    """
    본문(작품) 설명을 AI가 깔끔하게 정리
    
    Args:
        content_title: 본문 제목
        content_text: 본문 내용 (리스트)
        subject: 과목
    
    Returns:
        정리된 본문 설명
    """
    if not OPENAI_AVAILABLE:
        raise HTTPException(status_code=501, detail="OpenAI가 설치되지 않았습니다.")
    
    try:
        client = get_openai_client()
        
        # 본문 내용 합치기
        text = "\n".join(content_text)
        
        prompt = f"""다음 문학 작품을 학생이 이해하기 쉽게 깔끔하게 설명해주세요.

제목: {content_title}

작품 내용:
{text}

요구사항:
1. 작품의 핵심 내용을 명확하게 설명
2. 작품의 특징과 의미를 간결하게
3. 학생이 이해하기 쉽게 (300자 이내)
4. 자연스러운 말투

정리된 설명:"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 문학 교사입니다. 학생이 이해하기 쉽게 작품을 설명해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        explanation = response.choices[0].message.content.strip()
        
        return {
            "content_title": content_title,
            "original_text": content_text,
            "ai_explanation": explanation,
            "subject": subject
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 설명 생성 실패: {str(e)}")


@router.post("/literature/ai/explain-problem")
async def explain_problem(
    problem_id: str = Body(..., embed=True),
    question_text: str = Body(..., embed=True),
    choices: Dict[str, str] = Body(..., embed=True),
    passage: Optional[list] = Body(None, embed=True),
    subject: str = Body("literature", embed=True)
) -> Dict[str, Any]:
    """
    문제 설명을 AI가 깔끔하게 정리
    
    Args:
        problem_id: 문제 ID
        question_text: 문제 질문
        choices: 선택지
        passage: 지문 (선택)
        subject: 과목
    
    Returns:
        정리된 문제 설명 및 해설
    """
    if not OPENAI_AVAILABLE:
        raise HTTPException(status_code=501, detail="OpenAI가 설치되지 않았습니다.")
    
    try:
        client = get_openai_client()
        
        # 지문 합치기
        passage_text = "\n".join(passage) if passage else ""
        
        # 선택지 포맷팅
        choices_text = "\n".join([f"{k}번: {v}" for k, v in choices.items()])
        
        passage_section = f"지문:\n{passage_text}\n" if passage_text else ""

        prompt = f"""다음 문학 문제를 학생이 이해하기 쉽게 설명해주세요.

문제: {question_text}

{passage_section}
선택지:
{choices_text}

요구사항:
1. 문제의 핵심을 명확하게 설명
2. 각 선택지의 의미를 간단히 설명
3. 학생이 이해하기 쉽게 (200자 이내)
4. 자연스러운 말투

정리된 설명:"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 문학 교사입니다. 학생이 이해하기 쉽게 문제를 설명해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        explanation = response.choices[0].message.content.strip()
        
        return {
            "problem_id": problem_id,
            "question_text": question_text,
            "choices": choices,
            "passage": passage,
            "ai_explanation": explanation,
            "subject": subject
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 설명 생성 실패: {str(e)}")


@router.post("/literature/ai/find-similar-content")
async def find_similar_content(
    query_text: str = Body(..., embed=True),
    candidate_texts: list = Body(..., embed=True),
    top_k: int = Body(5, embed=True),
    min_similarity: float = Body(0.3, embed=True),
    subject: str = Body("literature", embed=True)
) -> Dict[str, Any]:
    """
    유사 콘텐츠 찾기 (ML 기반)
    
    Hugging Face Transformers를 사용한 문장 임베딩 기반 유사도 계산
    
    Args:
        query_text: 쿼리 텍스트 (찾고자 하는 콘텐츠)
        candidate_texts: 후보 텍스트 리스트
        top_k: 상위 K개 결과 반환
        min_similarity: 최소 유사도 임계값 (0.0 ~ 1.0)
        subject: 과목
    
    Returns:
        유사 콘텐츠 리스트
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="ML 서비스가 사용 불가능합니다. sentence-transformers를 설치하세요."
        )
    
    try:
        similarity_service = get_similarity_service()
        
        if not candidate_texts:
            return {
                "query_text": query_text,
                "similar_contents": [],
                "top_k": top_k,
                "min_similarity": min_similarity,
                "subject": subject
            }
        
        # 유사 콘텐츠 찾기
        similar_contents = similarity_service.find_similar_content(
            query_text=query_text,
            candidate_texts=candidate_texts,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        return {
            "query_text": query_text,
            "similar_contents": similar_contents,
            "top_k": top_k,
            "min_similarity": min_similarity,
            "total_candidates": len(candidate_texts),
            "found_count": len(similar_contents),
            "subject": subject
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유사 콘텐츠 찾기 실패: {str(e)}")


@router.post("/literature/ai/extract-keywords-tfidf")
async def extract_keywords_tfidf(
    texts: list = Body(..., embed=True),
    top_k: int = Body(10, embed=True),
    subject: str = Body("literature", embed=True)
) -> Dict[str, Any]:
    """
    TF-IDF 기반 키워드 추출
    
    Scikit-learn을 사용한 의미 있는 키워드 추출
    
    Args:
        texts: 텍스트 리스트
        top_k: 상위 K개 키워드
        subject: 과목
    
    Returns:
        키워드 리스트 (TF-IDF 점수 포함)
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="ML 서비스가 사용 불가능합니다. scikit-learn을 설치하세요."
        )
    
    try:
        keyword_extractor = get_keyword_extractor()
        
        if not texts:
            return {
                "keywords": [],
                "top_k": top_k,
                "subject": subject
            }
        
        # 키워드 추출
        keywords = keyword_extractor.extract_keywords(
            texts=texts,
            top_k=top_k
        )
        
        return {
            "keywords": keywords,
            "top_k": top_k,
            "total_texts": len(texts),
            "subject": subject
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"키워드 추출 실패: {str(e)}")


@router.post("/literature/ai/compute-similarity")
async def compute_similarity(
    text1: str = Body(..., embed=True),
    text2: str = Body(..., embed=True),
    subject: str = Body("literature", embed=True)
) -> Dict[str, Any]:
    """
    두 텍스트 간의 유사도 계산
    
    Args:
        text1: 첫 번째 텍스트
        text2: 두 번째 텍스트
        subject: 과목
    
    Returns:
        유사도 점수 (0.0 ~ 1.0)
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="ML 서비스가 사용 불가능합니다. sentence-transformers를 설치하세요."
        )
    
    try:
        similarity_service = get_similarity_service()
        
        # 유사도 계산
        results = similarity_service.compute_similarity(
            query_text=text1,
            candidate_texts=[text2]
        )
        
        if not results:
            similarity_score = 0.0
        else:
            similarity_score = results[0]["similarity"]
        
        return {
            "text1": text1,
            "text2": text2,
            "similarity": similarity_score,
            "subject": subject
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유사도 계산 실패: {str(e)}")


@router.get("/literature/ai/cache-stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    임베딩 캐시 통계 조회
    
    Returns:
        캐시 통계 정보 (히트율, 캐시 크기 등)
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="ML 서비스가 사용 불가능합니다."
        )
    
    try:
        similarity_service = get_similarity_service()
        stats = similarity_service.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캐시 통계 조회 실패: {str(e)}")


@router.delete("/literature/ai/cache")
async def clear_cache(
    expired_only: bool = Body(True, embed=True)
) -> Dict[str, Any]:
    """
    임베딩 캐시 정리
    
    Args:
        expired_only: 만료된 캐시만 삭제 (True) 또는 전체 삭제 (False)
    
    Returns:
        삭제 결과
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="ML 서비스가 사용 불가능합니다."
        )
    
    try:
        similarity_service = get_similarity_service()
        similarity_service.clear_cache(expired_only=expired_only)
        return {
            "success": True,
            "message": f"{'만료된 캐시만' if expired_only else '전체 캐시'} 삭제 완료",
            "expired_only": expired_only
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캐시 정리 실패: {str(e)}")
