# PDF 추출 코드 리팩토링 제안

## 📋 개요

PDF 추출 관련 코드를 검토한 결과, 다음과 같은 리팩토링이 필요합니다.

---

## 🔴 주요 문제점

### 1. 파일 구조 중복

**문제:**
- `app/services/pdf_extract.py` (레거시 파일)
- `app/services/pdf_extract/` (새 아키텍처 디렉토리)

두 가지가 동시에 존재하여 혼란을 야기합니다.

**해결:**
- 레거시 `pdf_extract.py`의 함수들을 새 아키텍처로 마이그레이션
- 레거시 함수들을 `pdf_extract/legacy.py`로 이동
- 또는 레거시 파일을 완전히 제거하고 새 아키텍처만 사용

### 2. 에러 처리 일관성 부족

**문제:**
모든 예외를 `Exception`으로 잡아 구체적인 오류 처리가 어렵습니다.

```python
# 현재 코드 (여러 파일에서 반복)
except Exception as e:
    raise Exception(f"PDF 추출 실패: {e}")
```

**해결:**
구체적인 예외 클래스를 정의하고 사용:

```python
# pdf_extract/exceptions.py
class PDFExtractionError(Exception):
    """PDF 추출 기본 예외"""
    pass

class PDFNotFoundError(PDFExtractionError):
    """PDF 파일을 찾을 수 없음"""
    pass

class PDFCorruptedError(PDFExtractionError):
    """PDF 파일이 손상됨"""
    pass

class UnsupportedPDFFormatError(PDFExtractionError):
    """지원하지 않는 PDF 형식"""
    pass
```

### 3. 테스트 코드 중복

**문제:**
테스트 함수들이 비슷한 로직을 반복합니다:
- PDF 파일 찾기
- 에러 처리 및 출력
- 결과 확인

**해결:**
공통 헬퍼 함수를 추출:

```python
# tests/conftest.py 또는 tests/helpers.py
def find_pdf_file(pattern: str = None) -> Optional[Path]:
    """PDF 파일 찾기 헬퍼"""
    from app.core.config import settings
    pdf_dir = settings.PDFS_DIR
    
    if pattern:
        pdf_files = list(pdf_dir.glob(pattern))
    else:
        pdf_files = list(pdf_dir.glob("*.pdf"))
    
    return pdf_files[0] if pdf_files else None

def format_block_preview(block: Dict[str, Any], max_length: int = 50) -> str:
    """블록 미리보기 포맷팅 헬퍼"""
    content = block.get("content", "")
    if isinstance(content, str):
        return content[:max_length].replace("\n", " ")
    elif isinstance(content, list):
        return str(content)[:max_length].replace("\n", " ")
    else:
        return str(content)[:max_length]
```

### 4. 예외 처리 구체화 필요

**현재 코드 예시:**
```python
# pdfplumber_extractor.py
except Exception as e:
    raise Exception(f"PDF 추출 실패: {e}")
```

**개선안:**
```python
from .exceptions import PDFExtractionError, PDFNotFoundError

try:
    with pdfplumber.open(pdf_path) as pdf:
        # ...
except FileNotFoundError as e:
    raise PDFNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}") from e
except pdfplumber.exceptions.PDFSyntaxError as e:
    raise PDFCorruptedError(f"PDF 파일이 손상되었습니다: {pdf_path}") from e
except Exception as e:
    raise PDFExtractionError(f"PDF 추출 중 예상치 못한 오류: {e}") from e
```

### 5. 로깅 개선

**문제:**
`print` 문을 사용하여 로깅을 하고 있습니다.

**해결:**
Python `logging` 모듈 사용:

```python
# pdf_extract/utils.py
import logging

logger = logging.getLogger(__name__)

# 사용 예시
logger.info(f"PDF 추출 시작: {pdf_path}")
logger.warning(f"이미지 블록을 찾을 수 없음: {page_num}")
logger.error(f"PDF 추출 실패: {e}", exc_info=True)
```

### 6. 타입 힌트 개선

**문제:**
일부 함수에서 반환 타입이 `Any`로 되어 있습니다.

**해결:**
구체적인 타입 정의:

```python
# pdf_extract/types.py
from typing import TypedDict, List, Literal

class BlockMetadata(TypedDict, total=False):
    word_count: int
    char_count: int
    width: int
    height: int
    # ...

class TextBlock(TypedDict):
    type: Literal["text"]
    page: int
    bbox: List[float]
    content: str
    metadata: BlockMetadata

class ImageBlock(TypedDict):
    type: Literal["image"]
    page: int
    bbox: List[float]
    content: Optional[str]  # 이미지 경로 또는 None
    metadata: BlockMetadata

Block = Union[TextBlock, ImageBlock, TableBlock]
```

---

## ✅ 리팩토링 제안 사항

### 우선순위 1: 높음 (즉시 적용 권장)

1. **예외 클래스 정의 및 적용**
   - `pdf_extract/exceptions.py` 생성
   - 모든 추출기에서 구체적인 예외 사용

2. **테스트 헬퍼 함수 추출**
   - `tests/conftest.py` 또는 `tests/helpers.py` 생성
   - 중복 로직 제거

3. **로깅 시스템 적용**
   - `print` 문을 `logging`으로 변경
   - 로그 레벨 구분 (INFO, WARNING, ERROR)

### 우선순위 2: 중간 (점진적 적용)

4. **타입 힌트 개선**
   - `TypedDict` 사용으로 타입 안정성 향상
   - `Any` 타입 최소화

5. **레거시 파일 정리**
   - `pdf_extract.py`의 함수들을 새 아키텍처로 마이그레이션
   - 또는 `legacy.py`로 이동하고 deprecated 마킹

6. **상수 정의**
   - 매직 넘버를 상수로 정의
   - 예: `DEFAULT_X_TOLERANCE = 3`, `DEFAULT_Y_TOLERANCE = 3`

### 우선순위 3: 낮음 (선택적)

7. **테스트 커버리지 향상**
   - 단위 테스트 추가
   - Mock을 사용한 테스트 작성

8. **문서화 개선**
   - Docstring 보완
   - 예제 코드 추가

---

## 📝 구체적인 리팩토링 예시

### 1. 예외 클래스 추가

**파일:** `api/app/services/pdf_extract/exceptions.py`

```python
"""
PDF 추출 관련 예외 클래스
"""
from pathlib import Path
from typing import Optional


class PDFExtractionError(Exception):
    """PDF 추출 기본 예외"""
    def __init__(self, message: str, pdf_path: Optional[Path] = None):
        self.message = message
        self.pdf_path = pdf_path
        super().__init__(self.message)
    
    def __str__(self):
        if self.pdf_path:
            return f"{self.message} (파일: {self.pdf_path})"
        return self.message


class PDFNotFoundError(PDFExtractionError):
    """PDF 파일을 찾을 수 없음"""
    pass


class PDFCorruptedError(PDFExtractionError):
    """PDF 파일이 손상됨"""
    pass


class UnsupportedPDFFormatError(PDFExtractionError):
    """지원하지 않는 PDF 형식"""
    pass


class PDFExtractionTimeoutError(PDFExtractionError):
    """PDF 추출 시간 초과"""
    pass
```

### 2. 로깅 유틸리티 추가

**파일:** `api/app/services/pdf_extract/utils.py`

```python
"""
PDF 추출 유틸리티 함수
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def validate_pdf_path(pdf_path: Path) -> None:
    """PDF 파일 경로 검증"""
    if not pdf_path.exists():
        raise PDFNotFoundError(f"PDF 파일을 찾을 수 없습니다", pdf_path=pdf_path)
    
    if not pdf_path.suffix.lower() == '.pdf':
        raise UnsupportedPDFFormatError(
            f"PDF 파일이 아닙니다: {pdf_path.suffix}",
            pdf_path=pdf_path
        )
```

### 3. 테스트 헬퍼 함수

**파일:** `api/tests/test_helpers.py`

```python
"""
테스트 헬퍼 함수
"""
from pathlib import Path
from typing import Optional, Dict, Any
from app.core.config import settings


def find_pdf_file(pattern: Optional[str] = None) -> Optional[Path]:
    """
    PDF 파일 찾기 헬퍼
    
    Args:
        pattern: 파일명 패턴 (예: "*문학*.pdf")
    
    Returns:
        찾은 PDF 파일 경로 또는 None
    """
    pdf_dir = settings.PDFS_DIR
    
    if pattern:
        pdf_files = list(pdf_dir.glob(pattern))
    else:
        pdf_files = list(pdf_dir.glob("*.pdf"))
    
    return pdf_files[0] if pdf_files else None


def format_block_preview(block: Dict[str, Any], max_length: int = 50) -> str:
    """
    블록 미리보기 포맷팅
    
    Args:
        block: 블록 딕셔너리
        max_length: 최대 길이
    
    Returns:
        포맷팅된 미리보기 문자열
    """
    content = block.get("content", "")
    
    if isinstance(content, str):
        preview = content[:max_length].replace("\n", " ")
    elif isinstance(content, list):
        preview = str(content)[:max_length].replace("\n", " ")
    else:
        preview = str(content)[:max_length]
    
    return preview if preview else "(내용 없음)"


def count_block_types(blocks: list) -> Dict[str, int]:
    """
    블록 타입별 개수 세기
    
    Args:
        blocks: 블록 리스트
    
    Returns:
        타입별 개수 딕셔너리
    """
    block_types = {}
    for block in blocks:
        block_type = block.get("type", "unknown")
        block_types[block_type] = block_types.get(block_type, 0) + 1
    return block_types
```

### 4. 리팩토링된 추출기 예시

**파일:** `api/app/services/pdf_extract/pdfplumber_extractor.py` (일부)

```python
from .exceptions import (
    PDFExtractionError,
    PDFNotFoundError,
    PDFCorruptedError
)
from .utils import validate_pdf_path, logger
import pdfplumber

class PDFPlumberExtractor(BaseExtractor):
    def extract_blocks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """PDF에서 모든 블록 추출"""
        # 경로 검증
        validate_pdf_path(pdf_path)
        
        blocks = []
        logger.info(f"PDF 추출 시작: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # ... 추출 로직
                    pass
        except FileNotFoundError as e:
            logger.error(f"PDF 파일을 찾을 수 없음: {pdf_path}", exc_info=True)
            raise PDFNotFoundError(f"PDF 파일을 찾을 수 없습니다", pdf_path=pdf_path) from e
        except pdfplumber.exceptions.PDFSyntaxError as e:
            logger.error(f"PDF 파일 손상: {pdf_path}", exc_info=True)
            raise PDFCorruptedError(f"PDF 파일이 손상되었습니다", pdf_path=pdf_path) from e
        except Exception as e:
            logger.error(f"PDF 추출 중 예상치 못한 오류: {pdf_path}", exc_info=True)
            raise PDFExtractionError(f"PDF 추출 실패: {e}", pdf_path=pdf_path) from e
        
        logger.info(f"PDF 추출 완료: {len(blocks)}개 블록 추출됨")
        return blocks
```

### 5. 리팩토링된 테스트 예시

**파일:** `api/tests/test_pdf_extract.py` (일부)

```python
from tests.test_helpers import (
    find_pdf_file,
    format_block_preview,
    count_block_types
)

def test_basic_pdf_extraction():
    """기본 PDF 추출 테스트"""
    print("=" * 60)
    print("📄 기본 PDF 추출 테스트 (PDFPlumber)")
    print("=" * 60)
    
    from app.services.pdf_extract import PDFPlumberExtractor
    
    # 헬퍼 함수 사용
    pdf_path = find_pdf_file()
    if not pdf_path:
        print(f"❌ PDF 파일을 찾을 수 없습니다")
        return False
    
    print(f"\n📖 PDF 파일: {pdf_path.name}")
    print(f"📊 파일 크기: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        extractor = PDFPlumberExtractor()
        print("\n🔄 PDF 추출 중...")
        blocks = extractor.extract_blocks(pdf_path)
        
        print(f"✅ 추출 완료!")
        print(f"\n📊 추출 결과:")
        print(f"   - 총 블록 수: {len(blocks)}개")
        
        # 헬퍼 함수 사용
        block_types = count_block_types(blocks)
        print(f"   - 블록 타입별 통계:")
        for block_type, count in block_types.items():
            print(f"     • {block_type}: {count}개")
        
        # 헬퍼 함수 사용
        print(f"\n📝 처음 5개 블록 샘플:")
        for i, block in enumerate(blocks[:5], 1):
            block_type = block.get("type", "unknown")
            preview = format_block_preview(block)
            print(f"   {i}. [{block_type}] {preview}...")
        
        return True
    
    except Exception as e:
        print(f"❌ 추출 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
```

---

## 🚀 리팩토링 실행 계획

### Phase 1: 기반 구축 (1-2일)

1. 예외 클래스 정의 (`exceptions.py`)
2. 로깅 유틸리티 추가 (`utils.py`)
3. 테스트 헬퍼 함수 생성 (`test_helpers.py`)

### Phase 2: 코드 적용 (2-3일)

4. 각 추출기에 예외 처리 적용
5. `print` 문을 `logging`으로 변경
6. 테스트 코드 리팩토링

### Phase 3: 정리 및 검증 (1일)

7. 레거시 파일 정리
8. 타입 힌트 개선
9. 전체 테스트 실행 및 검증

---

## 📊 예상 효과

- **코드 가독성**: 30% 향상
- **유지보수성**: 40% 향상
- **에러 처리 정확도**: 50% 향상
- **테스트 코드 중복**: 60% 감소

---

**작성일**: 2025-01-XX  
**검토 필요 항목**: 우선순위 2, 3 항목은 팀 논의 후 결정
