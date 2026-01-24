"""
문학 학습용 AI 강의 API
[DEPRECATED] 이 파일의 기능은 ai.py로 통합되었습니다.
호환성을 위해 유지되지만, 새로운 기능은 ai.py에 추가하세요.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional, Dict, Any
from pathlib import Path
import json
import os

router = APIRouter()

# OpenAI API 사용
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 데이터 경로
LITERATURE_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "literature"
LECTURES_DIR = LITERATURE_DATA_DIR / "lectures"
PROBLEMS_DIR = LITERATURE_DATA_DIR / "problems"


def get_openai_client():
    """OpenAI 클라이언트 생성"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")
    return openai.OpenAI(api_key=api_key)


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


# ML 기반 유사도 계산 서비스 (선택적)
try:
    from app.services.ml_content_similarity import get_similarity_service, get_keyword_extractor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    # ML 서비스는 선택적 의존성이므로 경고 없이 무시
    def get_similarity_service():
        return None
    def get_keyword_extractor():
        return None


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
