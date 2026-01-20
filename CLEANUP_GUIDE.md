# 데이터 폴더 정리 가이드

## 완료된 정리

✅ **api/data/pdfs/** - 삭제 완료
✅ **api/data/pages/** - 삭제 완료  
✅ **api/data/lectures/** - 삭제 완료
✅ **api/data/literature/** - 삭제 완료
✅ **api/data/pdf/** - 삭제 완료
✅ **api/data/problems/** - 삭제 완료

## 수동 정리 필요

### data/pdfs/ 폴더
일부 PDF 파일이 사용 중이어서 자동 삭제되지 않았습니다.

**수동 정리 방법:**
1. 모든 PDF 뷰어/에디터를 닫기
2. 다음 명령 실행:
   ```powershell
   Remove-Item -Recurse -Force "data\pdfs"
   ```

**또는 PDF 파일을 새 위치로 이동:**
- `data/pdfs/2026 수능특강_ 문학.pdf` → `data/literature/pdf/`
- `data/pdfs/2026 수능특강 수학Ⅰ.pdf.pdf` → `data/math1/pdf/`
- `data/pdfs/2026 수능특강_영어.pdf` → `data/english/pdf/`

## 새로운 폴더 구조

```
data/
 ├─ literature/
 │   ├─ pdf/          (문학 PDF 파일)
 │   ├─ pages/        (페이지 이미지)
 │   ├─ lectures/     (강의 JSON)
 │   ├─ problems/     (문제 JSON)
 │   └─ config.json
 ├─ math1/
 │   └─ (동일 구조)
 └─ english/
     └─ (동일 구조)
```

## 기존 폴더 정리

- ❌ `data/pdfs/` - 삭제 예정 (새 구조에서는 각 과목별 pdf/ 사용)
- ❌ `data/pages/` - 삭제 예정 (새 구조에서는 각 과목별 pages/ 사용)
- ✅ `data/uploads/` - 유지 (업로드된 파일용)
