# RAG 기반 추천 시스템 구현 계획

> **목적**: 문서에 명시된 "해결책 2: RAG 기반 추천 시스템" 완전 구현  
> **현재 상태**: `RAGContentRecommender` 클래스만 존재, API/UI 미구현

---

## 📋 구현 단계

### 1단계: 백엔드 API 엔드포인트 추가
### 2단계: 프론트엔드 컴포넌트 생성
### 3단계: UI 통합 (UnitViewer 또는 적절한 위치)
### 4단계: 데이터 초기화 (Vector DB 구축)

---

## 1단계: 백엔드 API 엔드포인트

### 1.1 API 라우터에 엔드포인트 추가

**파일**: `backend/app/routers/ai.py`

```python
from typing import List, Optional
from pydantic import BaseModel
from app.infrastructure.ai.genai.rag_recommender import RAGContentRecommender, build_recommendation_system
from app.infrastructure.ai.genai import AIService

# 기존 코드...

class RAGRecommendationRequest(BaseModel):
    """RAG 추천 요청"""
    query: str
    unit_id: Optional[str] = None
    lesson_id: Optional[str] = None
    content_type: Optional[str] = None  # "concept", "problem", "passage", "all"
    top_k: int = 5
    min_score: float = 0.3


class RAGRecommendationResponse(BaseModel):
    """RAG 추천 응답"""
    query: str
    recommendations: List[dict]
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
        # AIService에서 RAG 추천기 가져오기
        ai_service = AIService()
        recommender = ai_service.rag_recommender
        
        if not recommender:
            raise HTTPException(
                status_code=503,
                detail="RAG 추천 시스템이 초기화되지 않았습니다."
            )
        
        # 콘텐츠 타입 필터
        filter_metadata = {}
        if request.content_type and request.content_type != "all":
            filter_metadata["type"] = request.content_type
        
        # 추천 검색
        result = recommender.search(
            query=request.query,
            top_k=request.top_k,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        # 점수 필터링
        filtered_recommendations = []
        filtered_scores = []
        
        for rec, score in zip(result.recommendations, result.scores):
            if score >= request.min_score:
                filtered_recommendations.append(rec)
                filtered_scores.append(score)
        
        return RAGRecommendationResponse(
            query=request.query,
            recommendations=filtered_recommendations,
            scores=filtered_scores,
            content_type=request.content_type or "all"
        )
        
    except Exception as e:
        logger.error(f"[get_rag_recommendations] RAG 추천 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RAG 추천 생성 실패: {str(e)}"
        )


@router.post("/recommend/initialize")
async def initialize_rag_system(lesson_id: Optional[str] = None):
    """
    RAG 시스템 초기화 (Vector DB 구축)
    
    특정 강의의 개념/문제/본문을 Vector DB에 추가
    """
    try:
        # TODO: lesson_id로부터 개념/문제/본문 데이터 가져오기
        # from app.services.curriculum_service import get_lesson_units
        
        # units = get_lesson_units(lesson_id)
        # concepts = [u for u in units if u.type in ['CONCEPT_CORE', 'CONCEPT_FORM', 'CONCEPT_CONTENT']]
        # problems = [u for u in units if u.type == 'QUESTION']
        # passages = [u for u in units if u.type == 'PASSAGE']
        
        # ai_service = AIService()
        # recommender = ai_service.rag_recommender
        
        # recommender.add_concepts(concepts)
        # recommender.add_problems(problems)
        # recommender.add_passages(passages)
        
        return {"status": "success", "message": "RAG 시스템 초기화 완료"}
        
    except Exception as e:
        logger.error(f"[initialize_rag_system] 초기화 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RAG 시스템 초기화 실패: {str(e)}"
        )
```

---

## 2단계: 프론트엔드 컴포넌트

### 2.1 API 서비스 추가

**파일**: `frontend/src/services/ai.ts` (새로 생성 또는 기존 파일에 추가)

```typescript
import api from './api/client';

export interface RAGRecommendationRequest {
  query: string;
  unit_id?: string;
  lesson_id?: string;
  content_type?: 'concept' | 'problem' | 'passage' | 'all';
  top_k?: number;
  min_score?: number;
}

export interface RAGRecommendation {
  text: string;
  metadata: {
    type: string;
    concept_id?: string;
    problem_id?: string;
    passage_id?: string;
    title?: string;
    [key: string]: any;
  };
  score: number;
}

export interface RAGRecommendationResponse {
  query: string;
  recommendations: RAGRecommendation[];
  scores: number[];
  content_type: string;
}

export const aiAPI = {
  /**
   * RAG 기반 유사 콘텐츠 추천
   */
  async getRecommendations(
    request: RAGRecommendationRequest
  ): Promise<RAGRecommendationResponse> {
    return api.post<RAGRecommendationResponse>('/ai/recommend', request);
  },

  /**
   * RAG 시스템 초기화
   */
  async initializeRAG(lessonId?: string): Promise<{ status: string; message: string }> {
    return api.post('/ai/recommend/initialize', { lesson_id: lessonId });
  },
};
```

### 2.2 추천 컴포넌트 생성

**파일**: `frontend/src/components/ai/RAGRecommendationCard.tsx`

```typescript
/**
 * RAG 기반 추천 카드 컴포넌트
 * 유사한 개념/문제/본문 추천 표시
 */
import { useState, useEffect } from 'react';
import { aiAPI, RAGRecommendationRequest, RAGRecommendation } from '../../services/ai';
import { useTTS } from '../../hooks/useTTS';

interface RAGRecommendationCardProps {
  query: string;
  unitId?: string;
  lessonId?: string;
  contentType?: 'concept' | 'problem' | 'passage' | 'all';
  onSelect?: (recommendation: RAGRecommendation) => void;
}

export default function RAGRecommendationCard({
  query,
  unitId,
  lessonId,
  contentType = 'all',
  onSelect,
}: RAGRecommendationCardProps) {
  const [recommendations, setRecommendations] = useState<RAGRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const { speak } = useTTS();

  useEffect(() => {
    if (!query.trim() || !isExpanded) {
      setRecommendations([]);
      return;
    }

    setLoading(true);
    setError(null);

    const request: RAGRecommendationRequest = {
      query,
      unit_id: unitId,
      lesson_id: lessonId,
      content_type: contentType,
      top_k: 5,
      min_score: 0.3,
    };

    aiAPI
      .getRecommendations(request)
      .then((response) => {
        setRecommendations(response.recommendations);
        if (response.recommendations.length === 0) {
          speak('유사한 콘텐츠를 찾지 못했습니다.');
        } else {
          speak(`${response.recommendations.length}개의 유사한 콘텐츠를 찾았습니다.`);
        }
      })
      .catch((err) => {
        console.error('[RAGRecommendationCard] 추천 실패:', err);
        setError('추천을 불러오는 중 오류가 발생했습니다.');
        speak('추천을 불러오는 중 오류가 발생했습니다.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [query, unitId, lessonId, contentType, isExpanded, speak]);

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'concept':
        return '개념';
      case 'problem':
        return '문제';
      case 'passage':
        return '본문';
      default:
        return '콘텐츠';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'concept':
        return 'bg-blue-50 border-blue-300 text-blue-700';
      case 'problem':
        return 'bg-green-50 border-green-300 text-green-700';
      case 'passage':
        return 'bg-purple-50 border-purple-300 text-purple-700';
      default:
        return 'bg-gray-50 border-gray-300 text-gray-700';
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 flex items-center justify-between hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">🔍</span>
          <h4 className="font-semibold text-sm">유사 콘텐츠 추천</h4>
        </div>
        <span className="text-xs text-muted-foreground">
          {isExpanded ? '▼' : '▶'}
        </span>
      </button>

      {isExpanded && (
        <div className="px-3 pb-3 space-y-2 border-t">
          {loading && (
            <div className="text-sm text-muted-foreground py-2">
              유사한 콘텐츠를 찾는 중...
            </div>
          )}

          {error && (
            <div className="text-sm text-destructive py-2">{error}</div>
          )}

          {!loading && !error && recommendations.length === 0 && (
            <div className="text-sm text-muted-foreground py-2">
              유사한 콘텐츠를 찾지 못했습니다.
            </div>
          )}

          {!loading && !error && recommendations.length > 0 && (
            <div className="space-y-2">
              {recommendations.map((rec, index) => (
                <button
                  key={index}
                  onClick={() => {
                    if (onSelect) {
                      onSelect(rec);
                    }
                    speak(`${getTypeLabel(rec.metadata.type)}: ${rec.text.substring(0, 50)}...`);
                  }}
                  className={`w-full text-left p-3 rounded-lg border transition-colors hover:shadow-md ${getTypeColor(
                    rec.metadata.type
                  )}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold px-2 py-0.5 rounded">
                          {getTypeLabel(rec.metadata.type)}
                        </span>
                        {rec.metadata.title && (
                          <span className="text-xs font-medium">
                            {rec.metadata.title}
                          </span>
                        )}
                      </div>
                      <p className="text-sm line-clamp-2">
                        {rec.text.length > 100
                          ? `${rec.text.substring(0, 100)}...`
                          : rec.text}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <span className="text-xs text-muted-foreground">
                        {Math.round(rec.score * 100)}%
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          <p className="text-xs text-muted-foreground mt-2">
            유사도가 높은 콘텐츠를 클릭하면 해당 내용으로 이동합니다.
          </p>
        </div>
      )}
    </div>
  );
}
```

### 2.3 Hook 생성 (선택사항)

**파일**: `frontend/src/hooks/useRAGRecommendation.ts`

```typescript
import { useState } from 'react';
import { aiAPI, RAGRecommendationRequest, RAGRecommendation } from '../services/ai';

export function useRAGRecommendation() {
  const [recommendations, setRecommendations] = useState<RAGRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRecommendations = async (request: RAGRecommendationRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await aiAPI.getRecommendations(request);
      setRecommendations(response.recommendations);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    recommendations,
    loading,
    error,
    getRecommendations,
  };
}
```

---

## 3단계: UI 통합

### 3.1 UnitViewer에 통합

**파일**: `frontend/src/components/unit/UnitViewer.tsx`

```typescript
// 기존 import에 추가
import RAGRecommendationCard from '../ai/RAGRecommendationCard';

// UnitViewer 컴포넌트 내부에 추가
export default function UnitViewer({ unit, onSpeak }: UnitViewerProps) {
  // ... 기존 코드 ...

  // 현재 단원의 텍스트를 추천 쿼리로 사용
  const recommendationQuery = 
    unit.content_text || 
    unit.braille_text || 
    unit.title || 
    '';

  const handleRecommendationSelect = (rec: RAGRecommendation) => {
    // 추천된 콘텐츠로 이동하는 로직
    // 예: unitId나 lessonId로 네비게이션
    console.log('선택된 추천:', rec);
    // navigate(`/unit/${rec.metadata.concept_id || rec.metadata.problem_id}`);
  };

  return (
    <div className="space-y-4">
      {/* 기존 단원 내용 */}
      {/* ... */}

      {/* RAG 추천 카드 추가 */}
      {recommendationQuery && (
        <RAGRecommendationCard
          query={recommendationQuery}
          unitId={unit.unit_id}
          lessonId={unit.lesson_id}
          contentType="all"
          onSelect={handleRecommendationSelect}
        />
      )}
    </div>
  );
}
```

### 3.2 AIQuestionInput 옆에 배치

**파일**: `frontend/src/components/ai/AIQuestionInput.tsx` (수정)

```typescript
// AIQuestionInput 컴포넌트 옆에 RAG 추천 카드 추가
import RAGRecommendationCard from './RAGRecommendationCard';

export default function AIQuestionInput({ unitId, lessonId, onAnswer }: AIQuestionInputProps) {
  // ... 기존 코드 ...

  return (
    <div className="space-y-3">
      {/* 기존 AI 질문 입력 */}
      {/* ... */}

      {/* RAG 추천 카드 */}
      {question && (
        <RAGRecommendationCard
          query={question}
          unitId={unitId}
          lessonId={lessonId}
          contentType="all"
          onSelect={(rec) => {
            // 추천 콘텐츠를 답변으로 사용하거나 네비게이션
            console.log('추천 선택:', rec);
          }}
        />
      )}
    </div>
  );
}
```

---

## 4단계: 데이터 초기화

### 4.1 Vector DB 구축 스크립트

**파일**: `backend/scripts/initialize_rag.py` (새로 생성)

```python
"""
RAG 시스템 초기화 스크립트
강의의 개념/문제/본문을 Vector DB에 추가
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.ai.genai import AIService
from app.services.curriculum_service import CurriculumService
from app.infrastructure.database import get_db

async def initialize_rag_for_lesson(lesson_id: str):
    """특정 강의의 RAG 시스템 초기화"""
    db = next(get_db())
    curriculum_service = CurriculumService(db)
    
    # 강의의 모든 단원 가져오기
    units = curriculum_service.get_lesson_units(lesson_id)
    
    # 타입별로 분류
    concepts = []
    problems = []
    passages = []
    
    for unit in units:
        if unit.type in ['CONCEPT_CORE', 'CONCEPT_FORM', 'CONCEPT_CONTENT']:
            concepts.append({
                'id': unit.unit_id,
                'title': unit.title,
                'content': unit.content_text or unit.braille_text or '',
                'metadata': {
                    'lesson_id': lesson_id,
                    'unit_id': unit.unit_id,
                }
            })
        elif unit.type == 'QUESTION':
            problems.append({
                'id': unit.unit_id,
                'question_text': unit.question?.stem or unit.content_text or '',
                'metadata': {
                    'lesson_id': lesson_id,
                    'unit_id': unit.unit_id,
                }
            })
        elif unit.type == 'PASSAGE':
            passages.append({
                'id': unit.unit_id,
                'content': unit.content_text or unit.braille_text or '',
                'metadata': {
                    'lesson_id': lesson_id,
                    'unit_id': unit.unit_id,
                }
            })
    
    # RAG 추천기에 추가
    ai_service = AIService()
    recommender = ai_service.rag_recommender
    
    if concepts:
        recommender.add_concepts(concepts, text_field='content')
        print(f"[RAG 초기화] 개념 {len(concepts)}개 추가")
    
    if problems:
        recommender.add_problems(problems, text_field='question_text')
        print(f"[RAG 초기화] 문제 {len(problems)}개 추가")
    
    if passages:
        recommender.add_passages(passages, text_field='content')
        print(f"[RAG 초기화] 본문 {len(passages)}개 추가")
    
    # Vector DB 저장 (FAISS인 경우)
    if recommender.vector_db_type == 'faiss':
        save_path = Path('backend/data/rag_vectors') / f'lesson_{lesson_id}'
        save_path.parent.mkdir(parents=True, exist_ok=True)
        recommender.save_vector_db(str(save_path))
        print(f"[RAG 초기화] Vector DB 저장: {save_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("사용법: python initialize_rag.py <lesson_id>")
        sys.exit(1)
    
    lesson_id = sys.argv[1]
    asyncio.run(initialize_rag_for_lesson(lesson_id))
```

### 4.2 자동 초기화 (선택사항)

**파일**: `backend/app/routers/lessons.py` (수정)

```python
# 강의 상세 조회 시 RAG 초기화 (선택사항)
@router.get("/lessons/{lesson_id}")
async def get_lesson_detail(lesson_id: str):
    # ... 기존 코드 ...
    
    # RAG 시스템 자동 초기화 (선택사항)
    # try:
    #     ai_service = AIService()
    #     if not ai_service.rag_recommender.vector_db:
    #         # Vector DB가 없으면 초기화
    #         await initialize_rag_for_lesson(lesson_id)
    # except Exception as e:
    #     logger.warning(f"[get_lesson_detail] RAG 초기화 실패: {e}")
    
    return lesson_detail
```

---

## 5단계: 사용 시나리오

### 시나리오 1: 단원 학습 중 유사 콘텐츠 추천

```
1. 사용자가 개념 단원 학습 중
2. "유사 콘텐츠 추천" 카드 클릭
3. 현재 개념 텍스트로 유사한 개념/문제 검색
4. 추천 결과 표시 (유사도 점수 포함)
5. 추천 항목 클릭 → 해당 단원으로 이동
```

### 시나리오 2: AI 질문 후 관련 콘텐츠 추천

```
1. 사용자가 AI에게 질문: "이차방정식이 뭐야?"
2. AI 답변 제공
3. 자동으로 "이차방정식" 관련 유사 개념/문제 추천
4. 추천 항목 클릭 → 관련 단원으로 이동
```

### 시나리오 3: 문제 풀이 중 유사 문제 추천

```
1. 사용자가 문제를 풀고 있음
2. "유사 문제 추천" 버튼 클릭
3. 현재 문제와 유사한 문제 5개 추천
4. 추천 문제 클릭 → 해당 문제로 이동
```

---

## 파일 구조

```
backend/
├── app/
│   ├── routers/
│   │   └── ai.py                    # ✅ RAG 추천 API 추가
│   └── infrastructure/
│       └── ai/
│           └── genai/
│               └── rag_recommender.py  # ✅ 이미 존재
│
└── scripts/
    └── initialize_rag.py            # 🆕 RAG 초기화 스크립트

frontend/
└── src/
    ├── components/
    │   └── ai/
    │       ├── AIQuestionInput.tsx   # ✅ 기존
    │       └── RAGRecommendationCard.tsx  # 🆕 추천 카드
    │
    ├── hooks/
    │   └── useRAGRecommendation.ts  # 🆕 Hook (선택사항)
    │
    ├── services/
    │   └── ai.ts                    # 🆕 API 서비스 추가
    │
    └── components/
        └── unit/
            └── UnitViewer.tsx       # ✅ RAG 카드 통합
```

---

## 구현 체크리스트

### 백엔드
- [ ] `ai.py`에 `/ai/recommend` 엔드포인트 추가
- [ ] `ai.py`에 `/ai/recommend/initialize` 엔드포인트 추가
- [ ] `RAGContentRecommender` 통합 확인
- [ ] 에러 처리 추가

### 프론트엔드
- [ ] `ai.ts` API 서비스 추가
- [ ] `RAGRecommendationCard.tsx` 컴포넌트 생성
- [ ] `UnitViewer.tsx`에 통합
- [ ] `AIQuestionInput.tsx` 옆에 배치 (선택사항)

### 데이터 초기화
- [ ] `initialize_rag.py` 스크립트 생성
- [ ] 강의별 Vector DB 구축
- [ ] 자동 초기화 로직 (선택사항)

### 테스트
- [ ] API 엔드포인트 테스트
- [ ] 프론트엔드 컴포넌트 테스트
- [ ] 통합 테스트

---

## 주의사항

1. **Vector DB 저장 위치**: `backend/data/rag_vectors/` 디렉토리 생성 필요
2. **의존성**: `langchain`, `sentence-transformers` 설치 확인
3. **성능**: 대량 데이터 시 Vector DB 구축 시간 고려
4. **메모리**: FAISS는 메모리 기반, Chroma는 디스크 기반

---

*작성일: 2026-01-27*  
*관련 문서: `PROBLEM_SOLUTION_ARCHITECTURE.md` (726-799 라인)*
