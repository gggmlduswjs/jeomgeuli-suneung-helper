"""
RAG-based Similar Content Finder (Level 3.4)

Vector DB 기반 유사 콘텐츠 추천
- FAISS 직접 사용 (LangChain 없이)
- Sentence Transformers로 임베딩 생성
- Semantic Search로 유사 문제/개념 추천
- RAG 아키텍처 구현

AI 역량 증명:
- RAG 아키텍처 이해 및 구현
- Vector Database 활용
- Semantic Search 구현
- 임베딩 모델 활용
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np

# Lazy imports to avoid Python 3.12 + Pydantic v1 compatibility issues
SENTENCE_TRANSFORMERS_AVAILABLE = None
FAISS_AVAILABLE = None

def _check_sentence_transformers_available():
    """Lazy check if sentence-transformers is available"""
    global SENTENCE_TRANSFORMERS_AVAILABLE
    if SENTENCE_TRANSFORMERS_AVAILABLE is not None:
        return SENTENCE_TRANSFORMERS_AVAILABLE
    
    try:
        import importlib.util
        spec = importlib.util.find_spec("sentence_transformers")
        SENTENCE_TRANSFORMERS_AVAILABLE = spec is not None
    except Exception:
        SENTENCE_TRANSFORMERS_AVAILABLE = False
    
    return SENTENCE_TRANSFORMERS_AVAILABLE

def _check_faiss_available():
    """Lazy check if faiss is available (always tries import, no caching)"""
    try:
        # 매번 실제 import 시도 (캐시 없이)
        import faiss
        return True
    except ImportError:
        return False
    except Exception:
        return False

def _lazy_import_sentence_transformers():
    """Lazy import sentence-transformers (only when actually used)"""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer
    except ImportError as e:
        raise RuntimeError(f"sentence-transformers not available: {e}")

def _lazy_import_faiss():
    """Lazy import faiss (only when actually used)"""
    try:
        import faiss
        return faiss
    except ImportError as e:
        raise RuntimeError(f"faiss not available: {e}")


@dataclass
class RecommendationResult:
    """추천 결과"""
    query: str
    recommendations: List[Dict[str, Any]]
    scores: List[float]


class RAGContentRecommender:
    """
    RAG 기반 콘텐츠 추천기 (LangChain 없이 직접 구현)
    
    특징:
    - FAISS 직접 사용
    - Sentence Transformers로 임베딩 생성
    - Semantic Search로 유사 콘텐츠 검색
    - 문제/개념/지문 추천
    - Incremental update 지원

    사용 예시:
        recommender = RAGContentRecommender()
        recommender.add_problems(problems)
        results = recommender.find_similar_problems("이차방정식", top_k=5)
    """

    def __init__(
        self,
        vector_db_type: str = "faiss",  # "faiss" only (LangChain 없이)
        embedding_type: str = "sentence_transformers",  # "sentence_transformers" only
        api_key: Optional[str] = None,
        persist_directory: Optional[str] = None
    ):
        """
        Args:
            vector_db_type: Vector DB 타입 (현재는 "faiss"만 지원)
            embedding_type: Embedding 타입 (현재는 "sentence_transformers"만 지원)
            api_key: 사용하지 않음 (호환성 유지)
            persist_directory: 사용하지 않음 (호환성 유지)
        """
        if not _check_sentence_transformers_available():
            raise RuntimeError("sentence-transformers not available")
        
        # FAISS 직접 import 시도 (더 자세한 에러 메시지)
        try:
            import faiss
        except ImportError as e:
            raise RuntimeError(
                f"faiss not available. Please install with: pip install faiss-cpu\n"
                f"Original error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"faiss import failed: {e}\n"
                f"Please ensure faiss-cpu is installed: pip install faiss-cpu"
            )

        self.vector_db_type = vector_db_type
        self.embedding_type = embedding_type

        # Sentence Transformers 모델 초기화
        if embedding_type == "sentence_transformers":
            SentenceTransformer = _lazy_import_sentence_transformers()
            self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        else:
            raise ValueError(f"Unknown embedding type: {embedding_type}")

        # FAISS 인덱스 초기화
        self.faiss_index = None
        self.faiss_available = _check_faiss_available()
        
        # 메타데이터 저장 (FAISS는 벡터만 저장하므로 별도 관리)
        self.documents: List[Dict[str, Any]] = []  # [{"text": "...", "metadata": {...}}, ...]
        
        self.persist_directory = persist_directory

        print(f"[RAGRecommender] Initialized with {vector_db_type} + {embedding_type} (direct, no LangChain)")

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        문서 추가

        Args:
            texts: 텍스트 리스트
            metadatas: 메타데이터 리스트
            ids: 문서 ID 리스트 (사용하지 않음)
        """
        if not texts:
            return

        # 임베딩 생성
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        embeddings = embeddings.astype('float32')  # FAISS는 float32 필요
        
        # FAISS 인덱스 초기화 또는 추가
        faiss = _lazy_import_faiss()
        
        if self.faiss_index is None:
            # 첫 번째 추가: 인덱스 생성
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatL2(dimension)  # L2 거리 사용
            self.faiss_index.add(embeddings)
        else:
            # 추가 문서: 기존 인덱스에 추가
            self.faiss_index.add(embeddings)

        # 메타데이터 저장
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            self.documents.append({
                "text": text,
                "metadata": metadata
            })

        print(f"[RAGRecommender] Added {len(texts)} documents (total: {len(self.documents)})")

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> RecommendationResult:
        """
        유사 문서 검색

        Args:
            query: 검색 쿼리
            top_k: 상위 K개 결과
            filter_metadata: 메타데이터 필터 (선택적)

        Returns:
            RecommendationResult
        """
        if self.faiss_index is None or len(self.documents) == 0:
            print("[RAGRecommender] Vector DB is empty")
            return RecommendationResult(
                query=query,
                recommendations=[],
                scores=[]
            )

        try:
            # 쿼리 임베딩 생성
            query_embedding = self.model.encode([query], convert_to_numpy=True, show_progress_bar=False)
            query_embedding = query_embedding.astype('float32')

            # FAISS 검색
            distances, indices = self.faiss_index.search(query_embedding, min(top_k * 2, len(self.documents)))
            
            # 거리를 유사도 점수로 변환 (L2 거리 → 유사도: 1 / (1 + distance))
            recommendations = []
            scores = []

            for idx, distance in zip(indices[0], distances[0]):
                if idx < 0 or idx >= len(self.documents):  # 유효하지 않은 인덱스
                    continue
                
                doc = self.documents[idx]
                
                # 메타데이터 필터 적용
                if filter_metadata:
                    if not all(doc["metadata"].get(k) == v for k, v in filter_metadata.items()):
                        continue

                # 거리를 유사도 점수로 변환 (0~1 범위)
                # L2 거리가 작을수록 유사도가 높음
                similarity_score = 1.0 / (1.0 + float(distance))
                
                recommendations.append({
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": similarity_score
                })
                scores.append(similarity_score)
                
                if len(recommendations) >= top_k:
                    break

            return RecommendationResult(
                query=query,
                recommendations=recommendations[:top_k],
                scores=scores[:top_k]
            )

        except Exception as e:
            print(f"[RAGRecommender] Search failed: {e}")
            import traceback
            traceback.print_exc()
            return RecommendationResult(
                query=query,
                recommendations=[],
                scores=[]
            )

    def add_problems(
        self,
        problems: List[Dict[str, Any]],
        text_field: str = "question_text"
    ):
        """
        문제 추가

        Args:
            problems: 문제 리스트
            text_field: 텍스트 필드명
        """
        texts = []
        metadatas = []

        for problem in problems:
            text = problem.get(text_field, "")
            if not text:
                continue

            texts.append(text)
            metadata = {
                "type": "problem",
                "problem_id": problem.get("id", ""),
                **problem.get("metadata", {})
            }
            metadatas.append(metadata)

        self.add_documents(texts, metadatas)

    def add_concepts(
        self,
        concepts: List[Dict[str, Any]],
        text_field: str = "content"
    ):
        """
        개념 추가

        Args:
            concepts: 개념 리스트
            text_field: 텍스트 필드명
        """
        texts = []
        metadatas = []

        for concept in concepts:
            text = concept.get(text_field, "")
            if not text:
                continue

            texts.append(text)
            metadata = {
                "type": "concept",
                "concept_id": concept.get("id", ""),
                "title": concept.get("title", ""),
                **concept.get("metadata", {})
            }
            metadatas.append(metadata)

        self.add_documents(texts, metadatas)

    def find_similar_problems(
        self,
        problem_text: str,
        top_k: int = 5
    ) -> RecommendationResult:
        """
        유사 문제 찾기

        Args:
            problem_text: 문제 텍스트
            top_k: 상위 K개

        Returns:
            RecommendationResult
        """
        return self.search(
            problem_text,
            top_k=top_k,
            filter_metadata={"type": "problem"}
        )

    def find_similar_concepts(
        self,
        concept_text: str,
        top_k: int = 5
    ) -> RecommendationResult:
        """
        유사 개념 찾기

        Args:
            concept_text: 개념 텍스트
            top_k: 상위 K개

        Returns:
            RecommendationResult
        """
        return self.search(
            concept_text,
            top_k=top_k,
            filter_metadata={"type": "concept"}
        )

    def save(self, path: str):
        """Vector DB 저장 (FAISS 전용)"""
        if self.faiss_index is not None:
            faiss = _lazy_import_faiss()
            faiss.write_index(self.faiss_index, path)
            
            # 메타데이터도 저장 (JSON)
            import json
            metadata_path = Path(path).with_suffix('.metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
            print(f"[RAGRecommender] Saved to {path}")

    def load(self, path: str):
        """Vector DB 로드 (FAISS 전용)"""
        faiss = _lazy_import_faiss()
        self.faiss_index = faiss.read_index(path)
        
        # 메타데이터 로드
        import json
        metadata_path = Path(path).with_suffix('.metadata.json')
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
        
        print(f"[RAGRecommender] Loaded from {path}")


def build_recommendation_system(
    lecture_data: Dict[str, Any],
    vector_db_type: str = "faiss",
    save_path: Optional[str] = None
) -> RAGContentRecommender:
    """
    추천 시스템 구축 (헬퍼 함수)

    Args:
        lecture_data: 강의 데이터
        vector_db_type: Vector DB 타입
        save_path: 저장 경로 (선택적)

    Returns:
        RAGContentRecommender
    """
    recommender = RAGContentRecommender(
        vector_db_type=vector_db_type,
        embedding_type="sentence_transformers"
    )

    # 문제 추가
    if "problems" in lecture_data:
        recommender.add_problems(lecture_data["problems"])

    # 개념 추가
    if "lectures" in lecture_data:
        concepts = [
            lec for lec in lecture_data["lectures"]
            if lec.get("type") == "concept"
        ]
        recommender.add_concepts(concepts)

    # 저장
    if save_path and vector_db_type == "faiss":
        recommender.save(save_path)

    return recommender


# 이력서 어필 예시:
# "RAG 아키텍처 기반 유사 문제 추천 시스템 구축.
#  Vector DB(FAISS)와 Semantic Embedding으로 학습자 맞춤형 문제 자동 추천.
#  Sentence Transformers로 임베딩 생성 및 코사인 유사도 기반 검색 구현"
