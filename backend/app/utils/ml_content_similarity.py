"""
ML 기반 콘텐츠 유사도 계산 서비스
Hugging Face Transformers를 사용한 문장 임베딩 및 유사도 계산
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import hashlib
import json
from pathlib import Path
import pickle
from datetime import datetime, timedelta

# sentence_transformers는 선택적 의존성 (torch 필요)
SENTENCE_TRANSFORMERS_AVAILABLE = False
SentenceTransformer = None
try:
    # torch import가 실패할 수 있으므로 모든 예외를 잡음
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception as e:
    # torch, sentence_transformers 관련 모든 에러 무시 (선택적 의존성)
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[MLContentSimilarity] scikit-learn이 설치되지 않았습니다. pip install scikit-learn")


class MLContentSimilarity:
    """
    ML 기반 콘텐츠 유사도 계산 클래스
    
    기능:
    - 문장 임베딩 생성 (Hugging Face Sentence Transformers)
    - 콘텐츠 유사도 계산 (코사인 유사도)
    - 유사 콘텐츠 추천
    - TF-IDF 기반 키워드 추출
    - 임베딩 캐싱 (성능 최적화)
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        use_gpu: bool = False,
        enable_cache: bool = True,
        cache_dir: Optional[Path] = None,
        cache_ttl_days: int = 30
    ):
        """
        Args:
            model_name: 사용할 Sentence Transformer 모델명
                       한국어 지원: 'paraphrase-multilingual-MiniLM-L12-v2'
            use_gpu: GPU 사용 여부
            enable_cache: 임베딩 캐싱 활성화 여부
            cache_dir: 캐시 디렉토리 경로 (None이면 자동 생성)
            cache_ttl_days: 캐시 유효 기간 (일)
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.enable_cache = enable_cache
        self.cache_ttl_days = cache_ttl_days
        self.model: Optional[Any] = None  # SentenceTransformer 타입 힌트 제거 (선택적 의존성)
        
        # 캐시 디렉토리 설정
        if cache_dir is None:
            # 기본 캐시 디렉토리: backend/data/ml_cache/
            api_dir = Path(__file__).parent.parent.parent
            cache_dir = api_dir / "data" / "ml_cache"
        
        self.cache_dir = Path(cache_dir)
        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"[MLContentSimilarity] 캐시 디렉토리: {self.cache_dir}")
        
        # 메모리 캐시 (실시간 사용)
        self.memory_cache: Dict[str, Tuple[np.ndarray, datetime]] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "file_hits": 0,
            "saves": 0
        }
        
        self._load_model()
    
    def _load_model(self):
        """모델 로드 (lazy loading)"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("[MLContentSimilarity] sentence-transformers 미설치로 모델 로드 실패")
            return
        
        try:
            print(f"[MLContentSimilarity] 모델 로딩 중: {self.model_name}")
            if SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer is not None:
                self.model = SentenceTransformer(self.model_name)
            else:
                raise ImportError("sentence-transformers가 사용 불가능합니다.")
            if self.use_gpu:
                self.model = self.model.to('cuda')
            print("[MLContentSimilarity] 모델 로딩 완료")
        except Exception as e:
            print(f"[MLContentSimilarity] 모델 로딩 실패: {e}")
            self.model = None
    
    def _get_text_hash(self, text: str) -> str:
        """텍스트 해시 생성 (캐시 키용)"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _load_embedding_cache(self, text_hash: str) -> Optional[np.ndarray]:
        """임베딩 캐시 로드"""
        if not self.enable_cache:
            return None
        
        # 메모리 캐시 확인
        if text_hash in self.memory_cache:
            embedding, cached_at = self.memory_cache[text_hash]
            # 캐시 만료 확인
            if datetime.now() - cached_at < timedelta(days=self.cache_ttl_days):
                self.cache_stats["memory_hits"] += 1
                return embedding
            else:
                # 만료된 캐시 제거
                del self.memory_cache[text_hash]
        
        # 파일 캐시 확인
        cache_file = self.cache_dir / f"{text_hash}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    embedding = cache_data['embedding']
                    cached_at = cache_data['cached_at']
                    
                    # 캐시 만료 확인
                    if isinstance(cached_at, str):
                        cached_at = datetime.fromisoformat(cached_at)
                    
                    if datetime.now() - cached_at < timedelta(days=self.cache_ttl_days):
                        # 메모리 캐시에도 저장
                        self.memory_cache[text_hash] = (embedding, cached_at)
                        self.cache_stats["file_hits"] += 1
                        return embedding
                    else:
                        # 만료된 캐시 파일 삭제
                        cache_file.unlink()
            except Exception as e:
                print(f"[MLContentSimilarity] 캐시 로드 실패 ({text_hash[:8]}): {e}")
                # 손상된 캐시 파일 삭제
                try:
                    cache_file.unlink()
                except:
                    pass
        
        return None
    
    def _save_embedding_cache(self, text_hash: str, embedding: np.ndarray):
        """임베딩 캐시 저장"""
        if not self.enable_cache:
            return
        
        now = datetime.now()
        
        # 메모리 캐시 저장
        self.memory_cache[text_hash] = (embedding, now)
        
        # 메모리 캐시 크기 제한 (100개)
        if len(self.memory_cache) > 100:
            # 가장 오래된 항목 제거 (FIFO)
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k][1]
            )
            del self.memory_cache[oldest_key]
        
        # 파일 캐시 저장
        try:
            cache_file = self.cache_dir / f"{text_hash}.pkl"
            cache_data = {
                'embedding': embedding,
                'cached_at': now.isoformat(),
                'model_name': self.model_name
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            self.cache_stats["saves"] += 1
        except Exception as e:
            print(f"[MLContentSimilarity] 캐시 저장 실패 ({text_hash[:8]}): {e}")
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 리스트를 임베딩 벡터로 변환 (캐싱 지원)
        
        Args:
            texts: 텍스트 리스트
        
        Returns:
            임베딩 벡터 배열 (n_samples, embedding_dim)
        """
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다. sentence-transformers를 설치하세요.")
        
        if not texts:
            return np.array([])
        
        # 캐시된 임베딩과 계산이 필요한 텍스트 분리
        cached_embeddings: Dict[int, np.ndarray] = {}
        texts_to_encode: List[Tuple[int, str]] = []
        
        for idx, text in enumerate(texts):
            if not text or not text.strip():
                continue
            
            text_hash = self._get_text_hash(text.strip())
            cached_embedding = self._load_embedding_cache(text_hash)
            
            if cached_embedding is not None:
                cached_embeddings[idx] = cached_embedding
                self.cache_stats["hits"] += 1
            else:
                texts_to_encode.append((idx, text.strip()))
                self.cache_stats["misses"] += 1
        
        # 모든 텍스트가 캐시되어 있으면 바로 반환
        if len(texts_to_encode) == 0:
            embeddings = np.array([cached_embeddings[i] for i in range(len(texts))])
            return embeddings
        
        # 캐시되지 않은 텍스트만 임베딩 계산
        texts_only = [text for _, text in texts_to_encode]
        new_embeddings = self.model.encode(
            texts_only,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32
        )
        
        # 새로 계산한 임베딩을 캐시에 저장
        for (idx, text), embedding in zip(texts_to_encode, new_embeddings):
            text_hash = self._get_text_hash(text)
            self._save_embedding_cache(text_hash, embedding)
        
        # 모든 임베딩 결합 (캐시된 것 + 새로 계산한 것)
        all_embeddings = []
        encode_idx = 0
        for i in range(len(texts)):
            if i in cached_embeddings:
                all_embeddings.append(cached_embeddings[i])
            else:
                all_embeddings.append(new_embeddings[encode_idx])
                encode_idx += 1
        
        return np.array(all_embeddings)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache),
            "cache_enabled": self.enable_cache
        }
    
    def clear_cache(self, expired_only: bool = True):
        """캐시 정리"""
        if not self.enable_cache:
            return
        
        # 메모리 캐시 정리
        if expired_only:
            now = datetime.now()
            expired_keys = [
                k for k, (_, cached_at) in self.memory_cache.items()
                if now - cached_at >= timedelta(days=self.cache_ttl_days)
            ]
            for k in expired_keys:
                del self.memory_cache[k]
        else:
            self.memory_cache.clear()
        
        # 파일 캐시 정리
        if self.cache_dir.exists():
            now = datetime.now()
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                        cached_at_str = cache_data.get('cached_at')
                        if cached_at_str:
                            cached_at = datetime.fromisoformat(cached_at_str)
                            if expired_only and now - cached_at < timedelta(days=self.cache_ttl_days):
                                continue
                    cache_file.unlink()
                except Exception as e:
                    print(f"[MLContentSimilarity] 캐시 파일 삭제 실패: {e}")
    
    def compute_similarity(
        self,
        query_text: str,
        candidate_texts: List[str]
    ) -> List[Dict[str, Any]]:
        """
        쿼리 텍스트와 후보 텍스트들의 유사도 계산
        
        Args:
            query_text: 쿼리 텍스트
            candidate_texts: 후보 텍스트 리스트
        
        Returns:
            유사도 점수와 함께 정렬된 결과 리스트
            [{"text": str, "similarity": float, "index": int}, ...]
        """
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        if not candidate_texts:
            return []
        
        # 모든 텍스트 임베딩 생성
        all_texts = [query_text] + candidate_texts
        embeddings = self.encode(all_texts)
        
        if len(embeddings) == 0:
            return []
        
        # 쿼리와 후보들 간의 코사인 유사도 계산
        query_embedding = embeddings[0:1]  # (1, dim)
        candidate_embeddings = embeddings[1:]  # (n, dim)
        
        # 코사인 유사도 계산 (수동 계산)
        similarities = np.dot(candidate_embeddings, query_embedding.T).flatten()
        
        # 결과 정렬 (유사도 높은 순)
        results = []
        for idx, similarity in enumerate(similarities):
            results.append({
                "text": candidate_texts[idx],
                "similarity": float(similarity),
                "index": idx
            })
        
        # 유사도 높은 순으로 정렬
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results
    
    def find_similar_content(
        self,
        query_text: str,
        candidate_texts: List[str],
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        유사 콘텐츠 찾기
        
        Args:
            query_text: 쿼리 텍스트
            candidate_texts: 후보 텍스트 리스트
            top_k: 상위 K개 결과 반환
            min_similarity: 최소 유사도 임계값
        
        Returns:
            유사 콘텐츠 리스트 (유사도 높은 순)
        """
        results = self.compute_similarity(query_text, candidate_texts)
        
        # 임계값 필터링
        filtered = [r for r in results if r["similarity"] >= min_similarity]
        
        # 상위 K개 반환
        return filtered[:top_k]


class TFIDFKeywordExtractor:
    """
    TF-IDF 기반 키워드 추출기
    Scikit-learn 사용
    """
    
    def __init__(self, max_features: int = 100, min_df: int = 1):
        """
        Args:
            max_features: 최대 특성 수
            min_df: 최소 문서 빈도
        """
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn이 설치되지 않았습니다.")
        
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=min_df,
            stop_words=None,  # 한국어 불용어는 별도 처리 필요
            ngram_range=(1, 1)  # 단일 단어만 (2-gram 필요시 (1, 2))
        )
    
    def extract_keywords(
        self,
        texts: List[str],
        top_k: int = 10
    ) -> List[Dict[str, float]]:
        """
        텍스트 리스트에서 TF-IDF 기반 키워드 추출
        
        Args:
            texts: 텍스트 리스트
            top_k: 상위 K개 키워드
        
        Returns:
            [{"keyword": str, "score": float}, ...] (점수 높은 순)
        """
        if not texts:
            return []
        
        try:
            # TF-IDF 벡터화
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # 특성 이름 가져오기
            feature_names = self.vectorizer.get_feature_names_out()
            
            # 전체 문서에 대한 평균 TF-IDF 점수 계산
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # 상위 K개 키워드 추출
            top_indices = np.argsort(mean_scores)[::-1][:top_k]
            
            keywords = []
            for idx in top_indices:
                if mean_scores[idx] > 0:  # 0이 아닌 점수만
                    keywords.append({
                        "keyword": feature_names[idx],
                        "score": float(mean_scores[idx])
                    })
            
            return keywords
        except Exception as e:
            print(f"[TFIDFKeywordExtractor] 키워드 추출 실패: {e}")
            return []
    
    def extract_keywords_from_single_text(
        self,
        text: str,
        corpus: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[str]:
        """
        단일 텍스트에서 키워드 추출
        
        Args:
            text: 대상 텍스트
            corpus: 참조 코퍼스 (없으면 text만 사용)
            top_k: 상위 K개 키워드
        
        Returns:
            키워드 리스트
        """
        if corpus is None:
            corpus = [text]
        else:
            corpus = corpus + [text]
        
        results = self.extract_keywords(corpus, top_k=top_k)
        return [r["keyword"] for r in results]


# 전역 인스턴스 (필요시 사용)
_similarity_instance: Optional[MLContentSimilarity] = None
_keyword_extractor_instance: Optional[TFIDFKeywordExtractor] = None


def get_similarity_service() -> MLContentSimilarity:
    """전역 유사도 서비스 인스턴스 가져오기 (싱글톤)"""
    global _similarity_instance
    if _similarity_instance is None:
        _similarity_instance = MLContentSimilarity(
            enable_cache=True,  # 캐싱 활성화
            cache_ttl_days=30   # 30일 캐시 유효 기간
        )
    return _similarity_instance


def get_keyword_extractor() -> TFIDFKeywordExtractor:
    """전역 키워드 추출기 인스턴스 가져오기 (싱글톤)"""
    global _keyword_extractor_instance
    if _keyword_extractor_instance is None:
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn이 설치되지 않았습니다.")
        _keyword_extractor_instance = TFIDFKeywordExtractor()
    return _keyword_extractor_instance
