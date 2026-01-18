import { useState, useRef } from 'react';
import useTTS from '../../../hooks/useTTS';
import { booksAPI } from '../../../services/books';
import type { Book, Subject } from '../../../types/book';

interface HWPUploadProps {
  onUploadComplete: (book: Book) => void;
  onSpeak: (text: string) => void;
}

export default function HWPUpload({ onUploadComplete, onSpeak }: HWPUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState<Subject>('KOREAN');
  const [year, setYear] = useState<number | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.hwp')) {
      const errorMsg = '한글 파일(.hwp)만 업로드할 수 있습니다.';
      setError(errorMsg);
      onSpeak(errorMsg);
      return;
    }

    // 파일명에서 제목 추출 (확장자 제거)
    if (!title) {
      const fileName = file.name.replace(/\.hwp$/i, '');
      setTitle(fileName);
    }

    setUploading(true);
    setProgress(0);
    setError(null);
    onSpeak('한글 파일을 업로드하고 있습니다. 잠시만 기다려주세요.');

    try {
      // 진행률 시뮬레이션
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const result = await booksAPI.uploadHWP(file, title || file.name, subject, year);
      
      clearInterval(progressInterval);
      setProgress(100);
      
      const successMsg = `한글 파일 업로드가 완료되었습니다. ${result.lesson_count}개의 레슨이 생성되었습니다.`;
      onSpeak(successMsg);
      
      // 업로드 완료 후 교재 선택
      setTimeout(() => {
        onUploadComplete(result);
      }, 1000);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || '한글 파일 업로드에 실패했습니다.';
      setError(errorMsg);
      onSpeak(errorMsg);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-4">
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">한글 파일 업로드</h3>
        <p className="text-sm text-muted mb-4">
          강의 대본 한글 파일(.hwp)을 업로드하면 자동으로 구조화되어 학습 자료로 변환됩니다.
        </p>

        <div className="space-y-4 mb-4">
          <div>
            <label htmlFor="hwp-title" className="block text-sm font-medium mb-2">
              교재 제목
            </label>
            <input
              id="hwp-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="예: 2026 수능특강 문학"
              className="w-full px-3 py-2 border border-border rounded-lg"
              disabled={uploading}
            />
          </div>

          <div>
            <label htmlFor="hwp-subject" className="block text-sm font-medium mb-2">
              과목
            </label>
            <select
              id="hwp-subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value as Subject)}
              className="w-full px-3 py-2 border border-border rounded-lg"
              disabled={uploading}
            >
              <option value="KOREAN">국어</option>
              <option value="ENGLISH">영어</option>
              <option value="MATH">수학</option>
            </select>
          </div>

          <div>
            <label htmlFor="hwp-year" className="block text-sm font-medium mb-2">
              연도 (선택)
            </label>
            <input
              id="hwp-year"
              type="number"
              value={year || ''}
              onChange={(e) => setYear(e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder="예: 2026"
              className="w-full px-3 py-2 border border-border rounded-lg"
              disabled={uploading}
            />
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".hwp,.HWP"
          onChange={handleFileSelect}
          className="hidden"
          aria-label="한글 파일 선택"
          disabled={uploading}
        />

        <button
          onClick={handleButtonClick}
          disabled={uploading || !title}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            uploading || !title
              ? 'bg-muted text-muted-foreground cursor-not-allowed'
              : 'btn-primary'
          }`}
          aria-label={uploading ? '업로드 중' : '한글 파일 선택'}
        >
          {uploading ? '업로드 중...' : '한글 파일 선택'}
        </button>

        {uploading && (
          <div className="mt-4">
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-muted mt-2 text-center">
              {progress < 100 ? '업로드 및 파싱 중...' : '완료'}
            </p>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-error/10 border border-error rounded-lg p-3">
            <p className="text-error text-sm">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
