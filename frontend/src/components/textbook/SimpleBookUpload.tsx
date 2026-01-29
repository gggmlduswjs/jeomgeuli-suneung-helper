/**
 * 간단 교재 업로드 (실시간 학습용)
 * OCR만 실행 + 목차 입력으로 강의 목록 생성
 */
import { useState } from 'react';
import { booksAPI } from '../../services/api/client';

interface SimpleBookUploadProps {
  onComplete?: (bookId: string) => void;
  onCancel?: () => void;
}

export default function SimpleBookUpload({ onComplete, onCancel }: SimpleBookUploadProps) {
  const [step, setStep] = useState<'upload' | 'toc'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [subject] = useState('KOREAN'); // 문학 고정
  const [year] = useState(2026);
  const [uploading, setUploading] = useState(false);
  const [bookId, setBookId] = useState<string | null>(null);
  const [tocText, setTocText] = useState('');
  const [savingTOC, setSavingTOC] = useState(false);

  // 1단계: PDF 업로드 (OCR만)
  const handleUpload = async () => {
    if (!file || !title) {
      alert('파일과 제목을 입력하세요.');
      return;
    }

    setUploading(true);

    try {
      // OCR만 실행 (simple_mode=true)
      const book = await booksAPI.upload(
        file,
        title,
        subject,
        year,
        undefined, // aiOptions 없음
        undefined, // templateName 없음
        true       // simpleMode=true (OCR만 실행)
      );

      setBookId(book.book_id);
      setStep('toc');
      alert('PDF 업로드 완료! OCR이 백그라운드에서 실행 중입니다.');
    } catch (err) {
      console.error('업로드 실패:', err);
      alert('업로드 실패: ' + (err as Error).message);
    } finally {
      setUploading(false);
    }
  };

  // 2단계: 목차 입력 및 강의 목록 생성
  const handleSaveTOC = async () => {
    if (!bookId || !tocText.trim()) {
      alert('목차를 입력하세요.');
      return;
    }

    setSavingTOC(true);

    try {
      const response = await fetch(`/api/v1/books/${bookId}/simple-parse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ toc_text: tocText })
      });

      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = '목차 파싱 실패';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          // If response is not JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      alert(`${data.lectures.length}개 강의 생성 완료!`);

      if (onComplete) {
        onComplete(bookId);
      }
    } catch (err) {
      console.error('목차 저장 실패:', err);
      const errorMessage = err instanceof Error ? err.message : String(err);
      alert('목차 저장 실패: ' + errorMessage);
    } finally {
      setSavingTOC(false);
    }
  };

  if (step === 'upload') {
    return (
      <div className="space-y-4 p-4 bg-card rounded-lg border border-border">
        <h3 className="text-lg font-semibold">간단 교재 업로드</h3>
        <p className="text-sm text-muted-foreground">
          PDF를 업로드하면 OCR이 실행됩니다. 파싱은 하지 않고, 다음 단계에서 목차를 입력하여 강의 목록을 만듭니다.
        </p>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">PDF 파일</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full px-3 py-2 border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">제목</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="예: 2026 수능특강 문학"
              className="w-full px-3 py-2 border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleUpload}
              disabled={!file || !title || uploading}
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
            >
              {uploading ? '업로드 중...' : 'PDF 업로드'}
            </button>
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80"
              >
                취소
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // step === 'toc'
  return (
    <div className="space-y-4 p-4 bg-card rounded-lg border border-border">
      <h3 className="text-lg font-semibold">목차 입력</h3>
      <p className="text-sm text-muted-foreground">
        목차를 입력하세요. 한 줄에 하나씩 입력합니다.
      </p>

      <div className="space-y-2">
        <p className="text-xs text-muted-foreground">
          형식 예시:<br/>
          1강 | 시의 표현과 형식 9<br/>
          2강 | 시의 내용 15<br/>
          3강 : 소설의 서술 19
        </p>

        <textarea
          value={tocText}
          onChange={(e) => setTocText(e.target.value)}
          placeholder="1강 | 시의 표현과 형식 9&#10;2강 | 시의 내용 15&#10;3강 | 소설의 서술 19"
          rows={10}
          className="w-full px-3 py-2 border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono text-sm"
        />
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleSaveTOC}
          disabled={!tocText.trim() || savingTOC}
          className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
        >
          {savingTOC ? '저장 중...' : '강의 목록 생성'}
        </button>
        <button
          onClick={() => setStep('upload')}
          className="px-4 py-2 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80"
        >
          이전
        </button>
      </div>
    </div>
  );
}
