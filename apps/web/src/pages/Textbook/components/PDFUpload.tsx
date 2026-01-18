import { useState, useRef } from 'react';
import useTTS from '../../../hooks/useTTS';

interface PDFUploadProps {
  onUploadComplete: (textbookId: number) => void;
  onSpeak: (text: string) => void;
}

export default function PDFUpload({ onUploadComplete, onSpeak }: PDFUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.includes('pdf')) {
      const errorMsg = 'PDF 파일만 업로드할 수 있습니다.';
      setError(errorMsg);
      onSpeak(errorMsg);
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);
    onSpeak('PDF를 업로드하고 있습니다. 잠시만 기다려주세요.');

    try {
      const { examAPI } = await import('../../../lib/api');
      const result = await examAPI.uploadPDF(file);
      
      setProgress(100);
      onSpeak(`PDF 업로드가 완료되었습니다. ${result.unit_count}개의 단원이 생성되었습니다.`);
      
      // 업로드 완료 후 교재 선택
      setTimeout(() => {
        onUploadComplete(result.textbook_id);
      }, 1000);
    } catch (err: any) {
      const errorMsg = err?.message || 'PDF 업로드에 실패했습니다.';
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
        <h3 className="text-lg font-semibold mb-4">PDF 교재 업로드</h3>
        <p className="text-sm text-muted mb-4">
          수능특강 PDF 파일을 업로드하면 자동으로 점자로 변환되어 학습할 수 있습니다.
        </p>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.PDF"
          onChange={handleFileSelect}
          className="hidden"
          aria-label="PDF 파일 선택"
          disabled={uploading}
        />

        <button
          onClick={handleButtonClick}
          disabled={uploading}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            uploading
              ? 'bg-muted text-muted-foreground cursor-not-allowed'
              : 'btn-primary'
          }`}
          aria-label={uploading ? '업로드 중' : 'PDF 파일 선택'}
        >
          {uploading ? '업로드 중...' : 'PDF 파일 선택'}
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
              {progress < 100 ? '업로드 및 변환 중...' : '완료'}
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

