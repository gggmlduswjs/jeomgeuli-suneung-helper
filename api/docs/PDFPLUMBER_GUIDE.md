# pdfplumber 사용 가이드

pdfplumber는 PDF에서 텍스트 레이어를 직접 추출하는 Python 라이브러리입니다. OCR보다 정확하고 빠릅니다.

## pdfplumber란?

- **텍스트 레이어 추출**: PDF 내부의 텍스트 레이어를 직접 읽어서 추출
- **OCR보다 정확**: 스캔된 이미지가 아닌 실제 텍스트를 추출하므로 오인식 없음
- **OCR보다 빠름**: 이미지 처리나 OCR 엔진이 필요 없음
- **좌표 정보**: 각 텍스트의 위치(x, y, width, height) 정보 제공

## 설치

```bash
pip install pdfplumber
```

또는 requirements.txt에서:
```bash
pip install -r api/requirements.txt
```

## 파이프라인에서의 사용

### 기본 사용 (자동)

파이프라인은 **기본적으로 pdfplumber를 사용**합니다:

```python
pipeline = TextbookPipeline(
    subject="literature",
    use_pdfplumber=True,  # 기본값: True
    # ...
)
```

### pdfplumber vs OCR

| 특징 | pdfplumber | OCR (Tesseract) |
|------|-----------|-----------------|
| **정확도** | 매우 높음 (텍스트 레이어 직접 추출) | 중간 (이미지 인식) |
| **속도** | 빠름 | 느림 |
| **요구사항** | PDF에 텍스트 레이어 필요 | Tesseract 설치 필요 |
| **사용 시기** | 텍스트 레이어가 있는 PDF | 스캔된 이미지 PDF |

### pdfplumber 사용 조건

pdfplumber는 다음 조건에서 작동합니다:
- ✅ PDF에 텍스트 레이어가 있는 경우 (일반적인 디지털 PDF)
- ❌ 스캔된 이미지만 있는 PDF (이미지 PDF)

### 자동 Fallback

PDF에 텍스트 레이어가 없으면 자동으로 OCR로 전환됩니다:

```python
# pdfplumber 사용 시도
if self.use_pdfplumber:
    try:
        self.text_extractor = PdfplumberExtractor(...)
    except:
        # 실패 시 OCR로 자동 전환
        self.text_extractor = OCRExtractor(...)
```

## 파이프라인 동작

### 1. pdfplumber 사용 시

```
PDF 업로드
  ↓
pdfplumber로 텍스트 추출 (빠름, 정확)
  ↓
텍스트 + 좌표 정보
  ↓
파싱 (강의, 문제 추출)
```

### 2. OCR 사용 시 (pdfplumber 실패 또는 비활성화)

```
PDF 업로드
  ↓
PDF → 이미지 변환
  ↓
Tesseract OCR (느림, 오인식 가능)
  ↓
텍스트 + 좌표 정보
  ↓
파싱 (강의, 문제 추출)
```

## 수능특강 PDF의 경우

수능특강 PDF는 일반적으로 **텍스트 레이어가 있는 디지털 PDF**이므로:
- ✅ pdfplumber 사용 권장
- ✅ 빠르고 정확한 텍스트 추출
- ✅ OCR보다 훨씬 빠름

## 테스트

### pdfplumber 설치 확인

```bash
python -c "import pdfplumber; print('pdfplumber 버전:', pdfplumber.__version__)"
```

### 파이프라인에서 pdfplumber 사용 확인

테스트 스크립트 실행 시:
```
[OK] pdfplumber 사용 (텍스트 레이어 추출, OCR보다 정확하고 빠름)
```

이 메시지가 보이면 pdfplumber가 사용되고 있습니다.

## pdfplumber 비활성화 (OCR만 사용)

특정 이유로 OCR만 사용하고 싶다면:

```python
pipeline = TextbookPipeline(
    subject="literature",
    use_pdfplumber=False,  # pdfplumber 비활성화
    # ...
)
```

또는 테스트 스크립트에서:
```bash
# 현재는 옵션이 없지만, 코드에서 use_pdfplumber=False로 설정 가능
```

## 참고

- **공식 문서**: https://github.com/jsvine/pdfplumber
- **설치**: `pip install pdfplumber`
- **의존성**: `pdfplumber`는 `pdf2image`와 함께 사용됩니다 (이미지 크롭용)
