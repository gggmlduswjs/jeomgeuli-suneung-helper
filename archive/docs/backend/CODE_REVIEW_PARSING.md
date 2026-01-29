# PDF 파싱 코드 리뷰

## 📋 개요

전체 파싱 파이프라인을 검토한 결과, 전반적으로 잘 구조화되어 있으나 개선이 필요한 부분들이 발견되었습니다.

## ✅ 잘된 점

1. **템플릿 기반 아키텍처**: 템플릿 시스템으로 과목별 차이를 잘 추상화
2. **하이브리드 라우터**: 템플릿/AI/폴백 전략이 명확하게 분리됨
3. **에러 처리 개선**: 최근 None 체크와 타입 검증이 추가됨
4. **성능 최적화**: 템플릿 기반 페이지 범위 계산 추가

## ⚠️ 주요 문제점

### 1. 코드 중복 (Critical)

#### 문제: `_render_page_from_pdf` 함수 중복
**위치**: `pipeline.py`의 3개 메서드
- `_save_problem_images` (line 520-536)
- `_save_concept_images` (line 647-662)
- `_save_content_images` (line 783-798)

**영향**: 
- 유지보수 어려움 (수정 시 3곳 모두 변경 필요)
- 코드 가독성 저하
- 버그 발생 가능성 증가

**해결 방안**:
```python
# pipeline.py에 공통 메서드 추가
def _render_page_from_pdf(self, page_num: int) -> Optional[Image.Image]:
    """PDF에서 특정 페이지만 렌더링하여 PIL.Image로 반환"""
    if not page_num or int(page_num) < 1:
        logger.warning(f"유효하지 않은 페이지 번호: {page_num}")
        return None
    
    convert_kwargs: Dict[str, Any] = {
        "dpi": getattr(self.extractor, "dpi", 300),
        "first_page": int(page_num),
        "last_page": int(page_num),
    }
    
    if settings.POPPLER_PATH:
        convert_kwargs["poppler_path"] = settings.POPPLER_PATH
    
    try:
        page_images = convert_from_path(self.pdf_path, **convert_kwargs)
        return page_images[0] if page_images else None
    except Exception as e:
        logger.error(f"페이지 {page_num} 렌더링 실패: {e}")
        return None
```

#### 문제: 이미지 저장 로직 중복
**위치**: `_save_problem_images`, `_save_concept_images`, `_save_content_images`

**해결 방안**: 공통 이미지 저장 로직을 별도 클래스로 분리
```python
class ImageSaver:
    def __init__(self, pdf_path: Path, extractor, subject: str, book_id: Optional[str] = None):
        self.pdf_path = pdf_path
        self.extractor = extractor
        self.data_dir = self._get_data_dir(subject, book_id)
    
    def save_images(self, items: List[Dict], item_type: str, ocr_data: List[Dict]):
        """공통 이미지 저장 로직"""
        # 페이지별 그룹화
        # 이미지 크롭 및 저장
        # ...
```

### 2. 파일 크기 문제 (High)

#### 문제: `pipeline.py`가 너무 큼 (899줄)
**영향**: 
- 단일 책임 원칙 위반
- 테스트 어려움
- 코드 탐색 어려움

**해결 방안**: 책임별로 분리
```
pipeline.py (메인 오케스트레이션만)
├── extractors/
│   └── image_saver.py (이미지 저장 로직)
├── processors/
│   └── page_range_calculator.py (페이지 범위 계산)
└── orchestrators/
    └── pipeline_orchestrator.py (전체 플로우 조율)
```

### 3. 에러 처리 일관성 (Medium)

#### 문제: 예외 처리 방식이 일관되지 않음

**현재 상태**:
```python
# 일부는 구체적 예외 처리
except FileNotFoundError as e:
    logger.error(f"파일 없음: {e}")
    raise

# 일부는 광범위한 예외 처리
except Exception as e:
    logger.error(f"오류: {e}")
    raise
```

**개선 방안**: 예외 처리 전략 수립
```python
# 커스텀 예외 클래스 정의
class ParsingError(Exception):
    """파싱 관련 기본 예외"""
    pass

class TemplateNotFoundError(ParsingError):
    """템플릿을 찾을 수 없음"""
    pass

class ExtractionError(ParsingError):
    """추출 실패"""
    pass

# 예외 처리 헬퍼
def handle_parsing_error(func):
    """파싱 함수의 공통 예외 처리"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ParsingError:
            raise  # 파싱 관련 예외는 그대로 전파
        except Exception as e:
            logger.error(f"{func.__name__} 실행 중 예상치 못한 오류: {e}")
            raise ParsingError(f"{func.__name__} 실패") from e
    return wrapper
```

### 4. 타입 안정성 (Medium)

#### 문제: 타입 힌트가 불완전함

**현재 상태**:
```python
def extract(self, all_ocr_data: List[Dict[str, Any]], lectures: List[Dict[str, Any]], parser: Any):
    # parser의 타입이 Any로 되어 있음
```

**개선 방안**: 타입 힌트 강화
```python
from typing import Protocol

class ParserProtocol(Protocol):
    def extract_sections(self, ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ...
    
    def extract_content_paragraphs(self, ocr_data: List[Dict[str, Any]], sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ...

def extract(
    self,
    all_ocr_data: List[Dict[str, Any]],
    lectures: List[Dict[str, Any]],
    parser: ParserProtocol
) -> List[Dict[str, Any]]:
    ...
```

### 5. 성능 최적화 (Medium)

#### 문제: 이미지 저장 시 페이지별 PDF 재렌더링

**현재 상태**: 각 이미지 저장 메서드에서 페이지별로 `convert_from_path` 호출

**개선 방안**: 페이지별 이미지 캐싱
```python
class ImageCache:
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self._cache: Dict[int, Image.Image] = {}
    
    def get_page_image(self, page_num: int) -> Optional[Image.Image]:
        if page_num not in self._cache:
            self._cache[page_num] = self._render_page(page_num)
        return self._cache.get(page_num)
    
    def clear(self):
        self._cache.clear()
```

### 6. 로깅 일관성 (Low)

#### 문제: 로그 형식이 일관되지 않음

**현재 상태**:
```python
logger.info(f"[Pipeline] 텍스트 추출 시작")
logger.info("1. 텍스트 추출 중...")
logger.info(f"   추출기 타입: {type(self.extractor).__name__}")
```

**개선 방안**: 구조화된 로깅
```python
from structlog import get_logger

logger = get_logger()

logger.info(
    "text_extraction_started",
    extractor_type=type(self.extractor).__name__,
    pdf_path=str(pdf_path),
    page_range=(start_page, end_page)
)
```

### 7. 테스트 가능성 (Low)

#### 문제: 의존성이 하드코딩되어 있음

**현재 상태**:
```python
def _create_ocr_extractor(self) -> OCRExtractor:
    # settings를 직접 참조
    if settings.POPPLER_PATH:
        ...
```

**개선 방안**: 의존성 주입
```python
class UnifiedPipeline:
    def __init__(
        self,
        ...,
        settings_provider: Optional[SettingsProvider] = None
    ):
        self.settings = settings_provider or settings
```

## 🔧 우선순위별 개선 사항

### 즉시 수정 (Phase 1)
1. ✅ **코드 중복 제거**: `_render_page_from_pdf` 공통화 (완료)
2. ✅ **이미지 저장 로직 통합**: `ImageSaver` 클래스 생성 (완료)
3. ✅ **예외 처리 표준화**: 커스텀 예외 클래스 도입 (완료)

### 단기 개선 (Phase 2)
4. ✅ **파일 분리**: `pipeline.py` 책임 분리 (부분 완료)
   - ✅ `PageRangeCalculator` 분리 (완료)
   - ✅ `ExtractorFactory` 분리 (완료)
   - ⏳ 텍스트 추출 로직 분리 (다음 단계)
5. ⏳ **타입 힌트 강화**: Protocol 사용
6. ✅ **이미지 캐싱**: 페이지별 이미지 재사용 (완료)

### 중기 개선 (Phase 3)
7. **구조화된 로깅**: structlog 도입
8. **의존성 주입**: 테스트 가능성 향상
9. **단위 테스트**: 핵심 로직 테스트 추가

## 📊 코드 메트릭

| 항목 | 현재 | 목표 |
|------|------|------|
| pipeline.py 라인 수 | ~450 (책임 분리 후) | < 300 |
| 코드 중복률 | ~5% (이미지 저장 통합 후) | < 5% ✅ |
| 타입 힌트 커버리지 | ~60% | > 90% |
| 예외 처리 일관성 | 높음 (커스텀 예외 도입) | 높음 ✅ |
| 이미지 캐싱 | ✅ 구현 완료 | ✅ |

## 💡 추가 제안

1. **설정 검증**: 파이프라인 시작 시 설정 유효성 검증
2. **진행률 추적**: 단계별 진행률 콜백 개선
3. **메트릭 수집**: 파싱 성능 메트릭 수집 및 모니터링
4. **문서화**: 주요 메서드에 docstring 추가

## 📝 결론

전반적으로 잘 구조화된 코드베이스이지만, 코드 중복 제거와 파일 분리를 통해 유지보수성을 크게 향상시킬 수 있습니다. 특히 이미지 저장 로직의 중복은 즉시 개선이 필요합니다.
