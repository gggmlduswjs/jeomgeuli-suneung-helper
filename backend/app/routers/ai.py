"""
AI 튜터 API 라우터
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from sqlalchemy.orm import Session
from app.utils.ai_utils import get_openai_client, check_openai_available
from app.infrastructure.database.session import get_db

# Lazy import for GenAIProcessor to avoid Python 3.12 + Pydantic v1 compatibility issues
def _get_genai_processor():
    """Lazy import GenAIProcessor (only when actually used)"""
    from app.infrastructure.ai.genai import GenAIProcessor
    return GenAIProcessor

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


class AIQuestionRequest(BaseModel):
    """AI 질문 요청"""
    question: str
    context: Optional[str] = None
    page_num: Optional[int] = None
    unit_id: Optional[str] = None
    lesson_id: Optional[str] = None


class AIAnswerResponse(BaseModel):
    """AI 답변 응답"""
    answer: str
    confidence: float = 1.0


@router.post("/ask", response_model=AIAnswerResponse)
async def ask_ai(
    request: AIQuestionRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    AI 튜터에게 질문하기

    Args:
        request: 질문 + 컨텍스트 (페이지 텍스트 또는 unit_id/lesson_id)
        db: 데이터베이스 세션

    Returns:
        AI 답변
    """
    try:
        question = request.question
        context = request.context or ""
        page_num = request.page_num
        
        # unit_id가 제공되면 해당 unit의 내용을 context로 사용
        if request.unit_id and not context:
            from app.infrastructure.database.models import Unit
            unit = db.query(Unit).filter(Unit.unit_id == request.unit_id).first()
            if unit:
                context = unit.content_text or unit.braille_text or ""
                if unit.title:
                    context = f"제목: {unit.title}\n\n{context}"
        
        # lesson_id만 제공된 경우 (unit_id가 없을 때)
        elif request.lesson_id and not context and not request.unit_id:
            from app.infrastructure.database.models import Lesson
            lesson = db.query(Lesson).filter(Lesson.lesson_id == request.lesson_id).first()
            if lesson:
                context = lesson.description or lesson.title or ""

        # OpenAI API 사용 가능 여부 확인
        if not check_openai_available():
            # OpenAI가 없으면 기본 응답
            answer = f"""안녕하세요! 질문해주셔서 감사합니다.

질문: {question}

{'페이지 텍스트가 제공되었습니다.' if context else '페이지 텍스트가 없습니다.'}

OpenAI API 키를 설정하면 더 자세한 설명을 제공할 수 있습니다.
현재는 기본 응답만 제공됩니다."""
            
            return AIAnswerResponse(
                answer=answer,
                confidence=0.5
            )

        # OpenAI API 호출
        client = get_openai_client()
        
        # 프롬프트 구성 (Chain-of-Thought 적용)
        system_prompt = """당신은 학생들을 도와주는 친절한 AI 튜터입니다. 
제공된 학습 자료의 내용을 바탕으로 학생의 질문에 명확하고 이해하기 쉽게 답변해주세요.
답변은 교육적이고 도움이 되도록 작성해주세요.

**답변 방식 (Chain-of-Thought):**
복잡한 질문의 경우 다음 단계를 따라 답변하세요:
1. 문제 이해: 질문이 무엇을 묻는지 파악
2. 핵심 개념 분석: 관련된 주요 개념이나 원리 식별
3. 단계별 설명: 논리적 순서로 단계별로 설명
4. 결론 및 요약: 핵심 내용을 간단히 정리

각 단계를 명확히 구분하여 학생이 이해하기 쉽게 작성해주세요."""

        user_prompt = f"""질문: {question}

"""
        
        if context:
            user_prompt += f"""다음은 학습 자료의 내용입니다:

{context}

위 내용을 바탕으로 질문에 답변해주세요. 복잡한 질문이라면 단계별로 생각하는 과정을 보여주세요:
1. 먼저 질문의 핵심을 파악하고
2. 관련된 개념이나 원리를 분석한 후
3. 단계별로 설명하고
4. 마지막으로 요약해주세요."""
        else:
            user_prompt += """일반적인 지식을 바탕으로 질문에 답변해주세요. 
복잡한 질문이라면 단계별로 생각하는 과정을 보여주세요:
1. 먼저 질문의 핵심을 파악하고
2. 관련된 개념이나 원리를 분석한 후
3. 단계별로 설명하고
4. 마지막으로 요약해주세요."""

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 빠르고 저렴한 모델
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        answer = response.choices[0].message.content.strip()

        return AIAnswerResponse(
            answer=answer,
            confidence=0.9
        )

    except Exception as e:
        logger.error(f"[ask_ai] AI 질문 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI 응답 생성 실패: {str(e)}"
        )


class RAGRecommendationRequest(BaseModel):
    """RAG 추천 요청"""
    query: str
    unit_id: Optional[str] = None
    lesson_id: Optional[str] = None
    content_type: Optional[str] = None  # "concept", "problem", "passage", "all"
    top_k: int = 5
    min_score: float = 0.3


class RAGRecommendationItem(BaseModel):
    """RAG 추천 항목"""
    text: str
    metadata: Dict[str, Any]
    score: float


class RAGRecommendationResponse(BaseModel):
    """RAG 추천 응답"""
    query: str
    recommendations: List[RAGRecommendationItem]
    scores: List[float]
    content_type: str


@router.post("/recommend", response_model=RAGRecommendationResponse)
async def get_rag_recommendations(request: RAGRecommendationRequest = Body(...)):
    """
    RAG 기반 유사 콘텐츠 추천
    
    Args:
        request: 추천 요청 (질문, 단원 ID, 콘텐츠 타입 등)
    
    Returns:
        유사한 개념/문제/본문 추천 리스트
    """
    try:
        # GenAIProcessor에서 RAG 추천기 가져오기 (lazy import)
        try:
            GenAIProcessor = _get_genai_processor()
            ai_processor = GenAIProcessor(
                enable_recommendations=True,
                vector_db_path=None  # 메모리 기반 (필요시 경로 지정)
            )
            recommender = ai_processor.rag_recommender
        except Exception as init_error:
            logger.error(f"[get_rag_recommendations] GenAIProcessor 초기화 실패: {init_error}", exc_info=True)
            # RAG 시스템이 사용 불가능한 경우 빈 결과 반환
            return RAGRecommendationResponse(
                query=request.query,
                recommendations=[],
                scores=[],
                content_type=request.content_type or "all"
            )
        
        if not recommender:
            logger.warning("[get_rag_recommendations] RAG 추천 시스템이 초기화되지 않았습니다.")
            return RAGRecommendationResponse(
                query=request.query,
                recommendations=[],
                scores=[],
                content_type=request.content_type or "all"
            )
        
        # Vector DB가 비어있으면 빈 결과 반환
        if not hasattr(recommender, 'vector_db') or not recommender.vector_db:
            logger.warning("[get_rag_recommendations] Vector DB가 비어있습니다.")
            return RAGRecommendationResponse(
                query=request.query,
                recommendations=[],
                scores=[],
                content_type=request.content_type or "all"
            )
        
        # 콘텐츠 타입 필터
        filter_metadata = {}
        if request.content_type and request.content_type != "all":
            filter_metadata["type"] = request.content_type
        
        # 추천 검색
        try:
            result = recommender.search(
                query=request.query,
                top_k=request.top_k,
                filter_metadata=filter_metadata if filter_metadata else None
            )
        except Exception as search_error:
            logger.error(f"[get_rag_recommendations] 검색 실패: {search_error}", exc_info=True)
            return RAGRecommendationResponse(
                query=request.query,
                recommendations=[],
                scores=[],
                content_type=request.content_type or "all"
            )
        
        # 점수 필터링 및 응답 형식 변환
        filtered_recommendations = []
        filtered_scores = []
        
        if result and hasattr(result, 'recommendations') and hasattr(result, 'scores'):
            for rec, score in zip(result.recommendations, result.scores):
                if score >= request.min_score:
                    filtered_recommendations.append(
                        RAGRecommendationItem(
                            text=rec.get("text", "") if isinstance(rec, dict) else str(rec),
                            metadata=rec.get("metadata", {}) if isinstance(rec, dict) else {},
                            score=float(score)
                        )
                    )
                    filtered_scores.append(float(score))
        
        return RAGRecommendationResponse(
            query=request.query,
            recommendations=filtered_recommendations,
            scores=filtered_scores,
            content_type=request.content_type or "all"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[get_rag_recommendations] RAG 추천 실패: {e}", exc_info=True)
        # 에러 발생 시 빈 결과 반환 (시스템이 계속 작동하도록)
        return RAGRecommendationResponse(
            query=request.query,
            recommendations=[],
            scores=[],
            content_type=request.content_type or "all"
        )


@router.post("/recommend/initialize")
async def initialize_rag_system(
    lesson_id: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """
    RAG 시스템 초기화 (Vector DB 구축)
    
    특정 강의의 개념/문제/본문을 Vector DB에 추가
    """
    try:
        from app.infrastructure.database.models import Lesson
        
        if not lesson_id:
            raise HTTPException(
                status_code=400,
                detail="lesson_id가 필요합니다."
            )
        
        # DB에서 강의와 단원 가져오기
        lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
        if not lesson:
            raise HTTPException(
                status_code=404,
                detail=f"강의를 찾을 수 없습니다: {lesson_id}"
            )
        
        units = lesson.units if lesson.units else []
        
        # 타입별로 분류
        concepts = []
        problems = []
        passages = []
        
        for unit in units:
            unit_type = unit.type.value if hasattr(unit.type, 'value') else str(unit.type)
            unit_id = unit.unit_id
            title = unit.title or ''
            content_text = unit.content_text or unit.braille_text or ''
            
            if unit_type in ['CONCEPT_CORE', 'CONCEPT_FORM', 'CONCEPT_CONTENT', 'CONCEPT_SUMMARY']:
                if content_text:
                    concepts.append({
                        'id': unit_id,
                        'title': title,
                        'content': content_text,
                        'metadata': {
                            'lesson_id': lesson_id,
                            'unit_id': unit_id,
                        }
                    })
            elif unit_type == 'QUESTION':
                question_text = ''
                if unit.question:
                    # question이 JSON 문자열인 경우 파싱
                    if isinstance(unit.question, str):
                        try:
                            import json
                            question_data = json.loads(unit.question)
                            question_text = question_data.get('stem', '') if isinstance(question_data, dict) else ''
                        except:
                            question_text = unit.question
                    elif isinstance(unit.question, dict):
                        question_text = unit.question.get('stem', '')
                
                if not question_text:
                    question_text = content_text
                
                if question_text:
                    problems.append({
                        'id': unit_id,
                        'question_text': question_text,
                        'metadata': {
                            'lesson_id': lesson_id,
                            'unit_id': unit_id,
                        }
                    })
            elif unit_type == 'PASSAGE':
                if content_text:
                    passages.append({
                        'id': unit_id,
                        'content': content_text,
                        'metadata': {
                            'lesson_id': lesson_id,
                            'unit_id': unit_id,
                        }
                    })
        
        # RAG 추천기에 추가 (lazy import)
        GenAIProcessor = _get_genai_processor()
        ai_processor = GenAIProcessor(
            enable_recommendations=True,
            vector_db_path=None  # 메모리 기반 (필요시 경로 지정)
        )
        recommender = ai_processor.rag_recommender
        
        added_count = 0
        if concepts:
            recommender.add_concepts(concepts, text_field='content')
            added_count += len(concepts)
            logger.info(f"[initialize_rag_system] 개념 {len(concepts)}개 추가")
        
        if problems:
            recommender.add_problems(problems, text_field='question_text')
            added_count += len(problems)
            logger.info(f"[initialize_rag_system] 문제 {len(problems)}개 추가")
        
        if passages:
            # RAGContentRecommender에 add_passages 메서드가 있는지 확인 필요
            # 없으면 add_concepts와 유사하게 구현하거나 add_documents 사용
            recommender.add_documents(
                [p['content'] for p in passages],
                [{'type': 'passage', 'passage_id': p['id'], **p['metadata']} for p in passages]
            )
            added_count += len(passages)
            logger.info(f"[initialize_rag_system] 본문 {len(passages)}개 추가")
        
        return {
            "status": "success",
            "message": f"RAG 시스템 초기화 완료: {added_count}개 항목 추가",
            "concepts": len(concepts),
            "problems": len(problems),
            "passages": len(passages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[initialize_rag_system] 초기화 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"RAG 시스템 초기화 실패: {str(e)}"
        )
