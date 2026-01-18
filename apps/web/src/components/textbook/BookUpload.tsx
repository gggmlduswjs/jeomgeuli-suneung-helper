/**
 * 교재 PDF 업로드 컴포넌트
 */
import { useState } from 'react';
import { booksAPI } from '../../services/books';
import type { Book } from '../../types/book';
import { Subject } from '../../types/book';

interface BookUploadProps {
  onUploadComplete: (book: Book) => void;
  onSpeak?: (text: string) => void;
}

export default function BookUpload({ onUploadComplete, onSpeak }: BookUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState<Subject>(Subject.KOREAN);
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== 'application/pdf') {
        setError('PDF 파일만 업로드 가능합니다.');
        onSpeak?.('PDF 파일만 업로드 가능합니다.');
        return;
      }
      setFile(selectedFile);
      setError(null);
      
      // 파일명에서 제목 추출 (확장자 제거)
      const fileName = selectedFile.name.replace(/\.pdf$/i, '');
      if (!title) {
        setTitle(fileName);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('파일을 선택해주세요.');
      onSpeak?.('파일을 선택해주세요.');
      return;
    }
    
    if (!title.trim()) {
      setError('제목을 입력해주세요.');
      onSpeak?.('제목을 입력해주세요.');
      return;
    }

    setUploading(true);
    setError(null);
    
    try {
      const book = await booksAPI.upload(file, title, subject, year);
      onSpeak?.(`${book.title} 업로드가 완료되었습니다.`);
      onUploadComplete(book);
    } catch (err: any) {
      const errorMsg = err.message || '업로드 중 오류가 발생했습니다.';
      setError(errorMsg);
      onSpeak?.(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4">교재 PDF 업로드</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">PDF 파일</label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="w-full p-2 border border-border rounded-lg"
            disabled={uploading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">제목</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-border rounded-lg"
            placeholder="예: 수능특강 2026 문학"
            disabled={uploading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">과목</label>
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value as Subject)}
            className="w-full p-2 border border-border rounded-lg"
            disabled={uploading}
          >
            <option value={Subject.KOREAN}>국어</option>
            <option value={Subject.ENGLISH}>영어</option>
            <option value={Subject.MATH}>수학</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">연도</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value) || new Date().getFullYear())}
            className="w-full p-2 border border-border rounded-lg"
            min="2020"
            max="2030"
            disabled={uploading}
          />
        </div>

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-3">
            <p className="text-error text-sm">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={uploading || !file}
          className="w-full px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? '업로드 중...' : '업로드'}
        </button>
      </form>
    </div>
  );
}
