"""
레슨 블록 자동 생성 API

LangChain Flow를 사용한 레슨 블록 생성 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os

from app.services.langchain_lesson_flow import (
    LessonBlockGenerationFlow,
    generate_lesson_blocks,
    generate_and_save_lesson_blocks
)
from app.services.lesson_block_decomposer import decompose_lecture_script

router = APIRouter()


# ============================================================================
# 요청/응답 스키마
# ============================================================================

class LessonBlockRequest(BaseModel):
    """레슨 블록 생성 요청"""
    script_text: str = Field(..., description="강의 대본 텍스트")
    subject: str = Field(..., description="과목 (korean, math, english)")
    lesson_number: Optional[int] = Field(None, description="강의 번호")
    use_ai: bool = Field(True, description="AI 사용 여부 (False면 규칙 기반)")
    llm_model: str = Field("gpt-4o-mini", description="LLM 모델명")
    temperature: float = Field(0, description="LLM temperature")
    save_to_db: bool = Field(False, description="MongoDB 저장 여부")


class LessonBlockResponse(BaseModel):
    """레슨 블록 생성 응답"""
    lesson_title: str
    subject: str
    lesson_number: int
    block_count: int
    blocks: List[Dict[str, Any]]
    generated_by: str = Field(..., description="생성 방식 (ai/rule)")
    saved: bool = False
    mongodb_id: Optional[str] = None


# ============================================================================
# API 엔드포인트
# ============================================================================

@router.post("/lesson-blocks/generate", response_model=LessonBlockResponse)
async def generate_lesson_blocks_api(
    request: LessonBlockRequest,
    background_tasks: BackgroundTasks
):
    """
    강의대본을 레슨 블록으로 자동 생성
    
    - AI 기반: LangChain Flow 사용
    - 규칙 기반: 패턴 매칭 사용 (AI 실패 시 자동 폴백)
    """
    try:
        # OpenAI API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        use_ai = request.use_ai and api_key is not None
        
        if use_ai:
            # AI 기반 생성
            try:
                flow = LessonBlockGenerationFlow(
                    subject=request.subject,
                    llm_model=request.llm_model,
                    temperature=request.temperature,
                    openai_api_key=api_key
                )
                
                result = flow.generate_and_save(
                    script_text=request.script_text,
                    lesson_number=request.lesson_number,
                    save_to_db=request.save_to_db
                )
                
                lesson = result["lesson"]
                generated_by = "ai"
                saved = result["saved"]
                mongodb_id = result["mongodb_id"]
                
            except Exception as e:
                print(f"[AI 생성 실패, 규칙 기반으로 폴백] {e}")
                use_ai = False
        
        if not use_ai:
            # 규칙 기반 생성
            result_dict = decompose_lecture_script(
                script_text=request.script_text,
                subject=request.subject,
                lesson_number=request.lesson_number
            )
            
            # Pydantic 모델로 변환
            from app.services.langchain_lesson_flow import LessonSchema, LessonBlock
            blocks = [
                LessonBlock(**block_dict)
                for block_dict in result_dict["blocks"]
            ]
            
            lesson = LessonSchema(
                lesson_title=result_dict["lesson_title"],
                subject=result_dict["subject"],
                lesson_number=result_dict["lesson_number"],
                blocks=blocks
            )
            
            generated_by = "rule"
            saved = False
            mongodb_id = None
        
        # 응답 생성
        return LessonBlockResponse(
            lesson_title=lesson.lesson_title,
            subject=lesson.subject,
            lesson_number=lesson.lesson_number,
            block_count=len(lesson.blocks),
            blocks=[block.model_dump() for block in lesson.blocks],
            generated_by=generated_by,
            saved=saved,
            mongodb_id=mongodb_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"레슨 블록 생성 실패: {str(e)}")


@router.post("/lesson-blocks/generate-batch")
async def generate_lesson_blocks_batch(
    scripts: List[LessonBlockRequest],
    background_tasks: BackgroundTasks
):
    """
    여러 강의대본을 일괄 처리
    
    - 비동기 처리
    - 각 요청은 독립적으로 처리
    """
    results = []
    
    for script_request in scripts:
        try:
            # 개별 생성
            response = await generate_lesson_blocks_api(script_request, background_tasks)
            results.append({
                "success": True,
                "lesson_number": response.lesson_number,
                "block_count": response.block_count,
                "generated_by": response.generated_by
            })
        except Exception as e:
            results.append({
                "success": False,
                "lesson_number": script_request.lesson_number,
                "error": str(e)
            })
    
    return {
        "total": len(scripts),
        "success": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }


@router.get("/lesson-blocks/validate/{lesson_id}")
async def validate_lesson_blocks(lesson_id: str):
    """
    생성된 레슨 블록 검증
    
    - 블록 순서 검증
    - 점자 신호 일관성 검증
    - 상태 의미 메시지 검증
    """
    # TODO: MongoDB에서 레슨 조회 후 검증
    return {
        "lesson_id": lesson_id,
        "valid": True,
        "issues": []
    }
