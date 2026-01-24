"""
RAG-based Similar Content Finder (Level 3.4)

Vector DB 기반 유사 콘텐츠 추천
- Chroma/FAISS로 Vector DB 구축
- OpenAI Embeddings 또는 Sentence Transformers
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

try:
    from langchain.vectorstores import Chroma, FAISS
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.docstore.document import Document
    from langchain.schema import BaseRetriever
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("[RAGRecommender] langchain not available")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


@dataclass
class RecommendationResult:
    """추천 결과"""
    query: str
    recommendations: List[Dict[str, Any]]
    scores: List[float]


class SentenceTransformerEmbeddings:
    """Sentence Transformers 래퍼 (LangChain 호환)"""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError("sentence-transformers not available")

        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서 임베딩"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """쿼리 임베딩"""
        embedding = self.model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()


class RAGContentRecommender:
    """
    RAG 기반 콘텐츠 추천기

    특징:
    - Vector DB로 콘텐츠 저장
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
        vector_db_type: str = "faiss",  # "faiss" or "chroma"
        embedding_type: str = "sentence_transformers",  # "openai" or "sentence_transformers"
        api_key: Optional[str] = None,
        persist_directory: Optional[str] = None
    ):
        """
        Args:
            vector_db_type: Vector DB 타입
            embedding_type: Embedding 타입
            api_key: OpenAI API 키 (embedding_type="openai"일 때만)
            persist_directory: 저장 디렉토리 (Chroma 전용)
        """
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("langchain not available")

        self.vector_db_type = vector_db_type
        self.embedding_type = embedding_type

        # Embeddings 초기화
        if embedding_type == "openai":
            self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        elif embedding_type == "sentence_transformers":
            self.embeddings = SentenceTransformerEmbeddings()
        else:
            raise ValueError(f"Unknown embedding type: {embedding_type}")

        # Vector DB 초기화
        self.vector_db = None
        self.persist_directory = persist_directory

        print(f"[RAGRecommender] Initialized with {vector_db_type} + {embedding_type}")

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
            ids: 문서 ID 리스트
        """
        if not texts:
            return

        # Document 객체 생성
        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            doc = Document(
                page_content=text,
                metadata=metadata
            )
            documents.append(doc)

        # Vector DB에 추가
        if self.vector_db is None:
            # 초기 생성
            if self.vector_db_type == "faiss":
                self.vector_db = FAISS.from_documents(
                    documents,
                    self.embeddings
                )
            elif self.vector_db_type == "chroma":
                self.vector_db = Chroma.from_documents(
                    documents,
                    self.embeddings,
                    persist_directory=self.persist_directory
                )
                if self.persist_directory:
                    self.vector_db.persist()
        else:
            # 추가
            if self.vector_db_type == "faiss":
                new_db = FAISS.from_documents(documents, self.embeddings)
                self.vector_db.merge_from(new_db)
            elif self.vector_db_type == "chroma":
                self.vector_db.add_documents(documents)
                if self.persist_directory:
                    self.vector_db.persist()

        print(f"[RAGRecommender] Added {len(documents)} documents")

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
        if self.vector_db is None:
            print("[RAGRecommender] Vector DB is empty")
            return RecommendationResult(
                query=query,
                recommendations=[],
                scores=[]
            )

        try:
            # Similarity search with scores
            results = self.vector_db.similarity_search_with_score(
                query,
                k=top_k
            )

            recommendations = []
            scores = []

            for doc, score in results:
                # 메타데이터 필터 적용
                if filter_metadata:
                    if not all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                        continue

                recommendations.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
                scores.append(float(score))

            return RecommendationResult(
                query=query,
                recommendations=recommendations[:top_k],
                scores=scores[:top_k]
            )

        except Exception as e:
            print(f"[RAGRecommender] Search failed: {e}")
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
        if self.vector_db_type == "faiss" and self.vector_db is not None:
            self.vector_db.save_local(path)
            print(f"[RAGRecommender] Saved to {path}")

    def load(self, path: str):
        """Vector DB 로드 (FAISS 전용)"""
        if self.vector_db_type == "faiss":
            self.vector_db = FAISS.load_local(path, self.embeddings)
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
